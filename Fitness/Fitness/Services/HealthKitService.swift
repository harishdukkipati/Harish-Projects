import Foundation
import HealthKit
import CoreData

struct DailyMetricPoint: Identifiable, Sendable {
    let dayStart: Date
    let value: Double
    var id: Date { dayStart }
}

/// User-visible hints about HealthKit write access (read types don’t expose reliable per-type status in HealthKit).
enum HealthWorkoutWriteAccess: Sendable {
    case notAvailable
    case notDetermined
    case denied
    case authorized
}

protocol HealthKitProviding: AnyObject {
    var isHealthDataAvailable: Bool { get }
    /// Whether the user has allowed saving workouts to Health (best-effort; `notDetermined` until first successful auth flow).
    var workoutWriteAccess: HealthWorkoutWriteAccess { get }

    func requestAuthorization() async throws
    func fetchDailySteps(start: Date, end: Date) async throws -> [DailyMetricPoint]
    func fetchDailyActiveEnergy(start: Date, end: Date) async throws -> [DailyMetricPoint]
    func fetchDailyAverageHeartRate(start: Date, end: Date) async throws -> [DailyMetricPoint]
    func saveWorkout(category: WorkoutCategory, start: Date, end: Date, calories: Double?) async throws
}

enum HealthKitServiceError: LocalizedError {
    case notAvailable
    case typeUnavailable

    var errorDescription: String? {
        switch self {
        case .notAvailable: "Health data is not available on this device."
        case .typeUnavailable: "A required Health type is unavailable."
        }
    }
}

final class HealthKitService: HealthKitProviding {
    private let healthStore = HKHealthStore()

    var isHealthDataAvailable: Bool {
        HKHealthStore.isHealthDataAvailable()
    }

    var workoutWriteAccess: HealthWorkoutWriteAccess {
        guard isHealthDataAvailable else { return .notAvailable }
        switch healthStore.authorizationStatus(for: HKObjectType.workoutType()) {
        case .notDetermined: return .notDetermined
        case .sharingDenied: return .denied
        case .sharingAuthorized: return .authorized
        @unknown default: return .notDetermined
        }
    }

    private var stepType: HKQuantityType? {
        HKQuantityType.quantityType(forIdentifier: .stepCount)
    }

    private var activeEnergyType: HKQuantityType? {
        HKQuantityType.quantityType(forIdentifier: .activeEnergyBurned)
    }

    private var heartRateType: HKQuantityType? {
        HKQuantityType.quantityType(forIdentifier: .heartRate)
    }

    func requestAuthorization() async throws {
        guard isHealthDataAvailable else { throw HealthKitServiceError.notAvailable }
        guard let stepType, let activeEnergyType, let heartRateType else {
            throw HealthKitServiceError.typeUnavailable
        }
        let toRead: Set<HKObjectType> = [stepType, activeEnergyType, heartRateType]
        let toWrite: Set<HKSampleType> = [HKObjectType.workoutType()]
        try await healthStore.requestAuthorization(toShare: toWrite, read: toRead)
    }

    func fetchDailySteps(start: Date, end: Date) async throws -> [DailyMetricPoint] {
        guard let stepType else { throw HealthKitServiceError.typeUnavailable }
        return try await fetchDailyCumulativeQuantity(
            type: stepType,
            unit: .count(),
            start: start,
            end: end
        )
    }

    func fetchDailyActiveEnergy(start: Date, end: Date) async throws -> [DailyMetricPoint] {
        guard let activeEnergyType else { throw HealthKitServiceError.typeUnavailable }
        return try await fetchDailyCumulativeQuantity(
            type: activeEnergyType,
            unit: .kilocalorie(),
            start: start,
            end: end
        )
    }

    func fetchDailyAverageHeartRate(start: Date, end: Date) async throws -> [DailyMetricPoint] {
        guard let heartRateType else { throw HealthKitServiceError.typeUnavailable }
        return try await fetchDailyAverageQuantity(
            type: heartRateType,
            unit: HKUnit.count().unitDivided(by: .minute()),
            start: start,
            end: end
        )
    }

    func saveWorkout(category: WorkoutCategory, start: Date, end: Date, calories: Double?) async throws {
        guard isHealthDataAvailable else { throw HealthKitServiceError.notAvailable }
        let energyQuantity = calories.map { HKQuantity(unit: .kilocalorie(), doubleValue: $0) }
        let workout = HKWorkout(
            activityType: category.hkActivityType,
            start: start,
            end: end,
            workoutEvents: nil,
            totalEnergyBurned: energyQuantity,
            totalDistance: nil,
            metadata: nil
        )
        try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
            healthStore.save(workout) { success, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                guard success else {
                    continuation.resume(throwing: HealthKitServiceError.notAvailable)
                    return
                }
                continuation.resume()
            }
        }
    }

    private func fetchDailyCumulativeQuantity(
        type: HKQuantityType,
        unit: HKUnit,
        start: Date,
        end: Date
    ) async throws -> [DailyMetricPoint] {
        let calendar = Calendar.current
        var interval = DateComponents()
        interval.day = 1
        let anchor = calendar.startOfDay(for: start)
        let predicate = HKQuery.predicateForSamples(withStart: start, end: end, options: .strictStartDate)

        return try await withCheckedThrowingContinuation { continuation in
            let query = HKStatisticsCollectionQuery(
                quantityType: type,
                quantitySamplePredicate: predicate,
                options: .cumulativeSum,
                anchorDate: anchor,
                intervalComponents: interval
            )
            query.initialResultsHandler = { _, collection, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                var points: [DailyMetricPoint] = []
                collection?.enumerateStatistics(from: start, to: end) { stats, _ in
                    let dayStart = stats.startDate
                    let value = stats.sumQuantity()?.doubleValue(for: unit) ?? 0
                    points.append(DailyMetricPoint(dayStart: dayStart, value: value))
                }
                continuation.resume(returning: points)
            }
            self.healthStore.execute(query)
        }
    }

    private func fetchDailyAverageQuantity(
        type: HKQuantityType,
        unit: HKUnit,
        start: Date,
        end: Date
    ) async throws ->[DailyMetricPoint] {
        let calendar = Calendar.current
        var interval = DateComponents()
        interval.day = 1
        let anchor = calendar.startOfDay(for: start)
        let predicate = HKQuery.predicateForSamples(withStart: start, end: end, options: .strictStartDate)

        return try await withCheckedThrowingContinuation { continuation in
            let query = HKStatisticsCollectionQuery(
                quantityType: type,
                quantitySamplePredicate: predicate,
                options: .discreteAverage,
                anchorDate: anchor,
                intervalComponents: interval
            )
            query.initialResultsHandler = { _, collection, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                var points: [DailyMetricPoint] = []
                collection?.enumerateStatistics(from: start, to: end) { stats, _ in
                    let dayStart = stats.startDate
                    let value = stats.averageQuantity()?.doubleValue(for: unit) ?? 0
                    points.append(DailyMetricPoint(dayStart: dayStart, value: value))
                }
                continuation.resume(returning: points)
            }
            self.healthStore.execute(query)
        }
    }
}
