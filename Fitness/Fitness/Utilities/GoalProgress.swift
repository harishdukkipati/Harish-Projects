import Foundation
import CoreData

enum GoalProgress {
    static func currentValue(for goal: FitnessGoal, in context: NSManagedObjectContext) -> Double {
        let rangeStart: Date = (goal.startDate as Date?) ?? .distantPast
        let rangeEnd: Date = (goal.endDate as Date?) ?? Date()
        let request: NSFetchRequest<WorkoutEntry> = WorkoutEntry.fetchRequest()
        let categoryPredicate = NSPredicate(format: "categoryRaw == %d", goal.goalCategoryRaw)
        let dateFrom = NSPredicate(format: "startDate >= %@", rangeStart as NSDate)
        let dateTo = NSPredicate(format: "startDate <= %@", rangeEnd as NSDate)
        request.predicate = NSCompoundPredicate(andPredicateWithSubpredicates: [
            categoryPredicate, dateFrom, dateTo,
        ])
        guard let workouts = try? context.fetch(request) else { return 0 }

        switch goal.unit {
        case .workouts:
            return Double(workouts.count)
        case .minutes:
            return workouts.reduce(0.0) { acc, workout in
                guard let workoutStart = workout.startDate else { return acc }
                let minutes: Double
                if workout.durationSeconds > 0 {
                    minutes = Double(workout.durationSeconds) / 60.0
                } else if let workoutEnd = workout.endDate {
                    minutes = workoutEnd.timeIntervalSince(workoutStart) / 60.0
                } else {
                    minutes = 0
                }
                return acc + minutes
            }
        case .calories:
            return workouts.reduce(0.0) { acc, w in
                acc + w.caloriesBurned
            }
        }
    }

    static func fraction(for goal: FitnessGoal, in context: NSManagedObjectContext) -> Double {
        let current = currentValue(for: goal, in: context)
        guard goal.targetValue > 0 else { return 0 }
        return min(current / goal.targetValue, 1.0)
    }
}
