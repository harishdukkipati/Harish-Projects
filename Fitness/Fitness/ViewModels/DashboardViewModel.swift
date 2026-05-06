import Foundation
import CoreData
import Observation

@MainActor
@Observable
final class DashboardViewModel {
    private let healthKit: HealthKitProviding
    private let context: NSManagedObjectContext

    var stepsSeries: [DailyMetricPoint] = []
    var energySeries: [DailyMetricPoint] = []
    var heartSeries: [DailyMetricPoint] = []
    var loggedMinutesSeries: [DailyMetricPoint] = []

    /// User-facing message when HealthKit queries fail unexpectedly. Empty/series alone imply no data or denied read.
    var healthError: String?
    var isLoadingHealth = false

    init(healthKit: HealthKitProviding, context: NSManagedObjectContext) {
        self.healthKit = healthKit
        self.context = context
    }

    func refresh(days: Int = 7) async {
        let calendar = Calendar.current
        let end = Date()
        guard let start = calendar.date(byAdding: .day, value: -days, to: calendar.startOfDay(for: end)) else { return }

        await MainActor.run {
            loggedMinutesSeries = Self.workoutMinutesPerDay(context: context, start: start, end: end)
            healthError = nil
        }

        guard AppHealthSync.isEnabled else {
            await MainActor.run {
                stepsSeries = []
                energySeries = []
                heartSeries = []
                isLoadingHealth = false
            }
            return
        }

        guard healthKit.isHealthDataAvailable else {
            await MainActor.run {
                stepsSeries = []
                energySeries = []
                heartSeries = []
            }
            return
        }

        isLoadingHealth = true
        defer { isLoadingHealth = false }

        do {
            try await healthKit.requestAuthorization()
            async let steps = healthKit.fetchDailySteps(start: start, end: end)
            async let energy = healthKit.fetchDailyActiveEnergy(start: start, end: end)
            async let heart = healthKit.fetchDailyAverageHeartRate(start: start, end: end)
            let (s, e, h) = try await (steps, energy, heart)
            await MainActor.run {
                stepsSeries = s
                energySeries = e
                heartSeries = h
                healthError = nil
            }
            await persistSnapshots(start: start, end: end, steps: s, energy: e, heart: h)
        } catch {
            await MainActor.run {
                stepsSeries = []
                energySeries = []
                heartSeries = []
                healthError = Self.friendlyHealthMessage(for: error)
            }
        }
    }

    private static func friendlyHealthMessage(for error: Error) -> String {
        let text = error.localizedDescription
        if text.localizedCaseInsensitiveContains("authorization")
            || text.localizedCaseInsensitiveContains("not determined") {
            return "Health access is needed for steps, energy, and heart rate. Turn on Apple Health in the Health tab, then pull to refresh here."
        }
        return text
    }

    private func persistSnapshots(
        start: Date,
        end: Date,
        steps: [DailyMetricPoint],
        energy: [DailyMetricPoint],
        heart: [DailyMetricPoint]
    ) async {
        await context.perform {
            let calendar = Calendar.current
            var day = calendar.startOfDay(for: start)
            let endDay = calendar.startOfDay(for: end)
            let stepsByDay = Dictionary(uniqueKeysWithValues: steps.map { (calendar.startOfDay(for: $0.dayStart), $0.value) })
            let energyByDay = Dictionary(uniqueKeysWithValues: energy.map { (calendar.startOfDay(for: $0.dayStart), $0.value) })
            let heartByDay = Dictionary(uniqueKeysWithValues: heart.map { (calendar.startOfDay(for: $0.dayStart), $0.value) })

            while day <= endDay {
                let request: NSFetchRequest<SyncedHealthSnapshot> = SyncedHealthSnapshot.fetchRequest()
                request.predicate = NSPredicate(format: "dayStart == %@", day as NSDate)
                request.fetchLimit = 1
                let snapshot: SyncedHealthSnapshot
                if let existing = try? self.context.fetch(request).first {
                    snapshot = existing
                } else {
                    snapshot = SyncedHealthSnapshot(context: self.context)
                    snapshot.id = UUID()
                    snapshot.dayStart = day
                }
                snapshot.steps = stepsByDay[day] ?? 0
                snapshot.activeEnergyKcal = energyByDay[day] ?? 0
                if let hr = heartByDay[day], hr > 0 {
                    snapshot.avgHeartRate = hr
                }
                guard let next = calendar.date(byAdding: .day, value: 1, to: day) else { break }
                day = next
            }
            try? self.context.save()
        }
    }

    private static func workoutMinutesPerDay(context: NSManagedObjectContext, start: Date, end: Date) -> [DailyMetricPoint] {
        let request: NSFetchRequest<WorkoutEntry> = WorkoutEntry.fetchRequest()
        request.predicate = NSPredicate(format: "startDate >= %@ AND startDate < %@", start as NSDate, end as NSDate)
        request.sortDescriptors = [NSSortDescriptor(keyPath: \WorkoutEntry.startDate, ascending: true)]
        guard let entries = try? context.fetch(request) else { return [] }

        let calendar = Calendar.current
        var totals: [Date: Double] = [:]
        for entry in entries {
            guard let workoutStart = entry.startDate else { continue }
            let day = calendar.startOfDay(for: workoutStart)
            let minutes: Double
            if entry.durationSeconds > 0 {
                minutes = Double(entry.durationSeconds) / 60.0
            } else if let workoutEnd = entry.endDate {
                minutes = workoutEnd.timeIntervalSince(workoutStart) / 60.0
            } else {
                minutes = 0
            }
            totals[day, default: 0] += minutes
        }
        return totals.keys.sorted().map { DailyMetricPoint(dayStart: $0, value: totals[$0] ?? 0) }
    }
}
