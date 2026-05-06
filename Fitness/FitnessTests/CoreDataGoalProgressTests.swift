import CoreData
import XCTest
@testable import Fitness

final class CoreDataGoalProgressTests: XCTestCase {

    func testGoalProgressCountsMatchingWorkouts() throws {
        let stack = PersistenceController(inMemory: true)
        let ctx = stack.container.viewContext

        let goal = FitnessGoal(context: ctx)
        goal.id = UUID()
        goal.goalCategory = .strength
        goal.targetValue = 2
        goal.unit = .workouts
        goal.startDate = Calendar.current.startOfDay(for: Date())
        goal.endDate = Date().addingTimeInterval(86400 * 7)
        goal.isCompleted = false

        let w1 = WorkoutEntry(context: ctx)
        w1.id = UUID()
        w1.category = .strength
        w1.startDate = Date()
        w1.endDate = Date().addingTimeInterval(1800)
        w1.durationSeconds = 1800
        w1.syncToHealth = false

        let w2 = WorkoutEntry(context: ctx)
        w2.id = UUID()
        w2.category = .cardio
        w2.startDate = Date()
        w2.endDate = Date().addingTimeInterval(600)
        w2.durationSeconds = 600
        w2.syncToHealth = false

        try ctx.save()

        let value = GoalProgress.currentValue(for: goal, in: ctx)
        XCTAssertEqual(value, 1, accuracy: 0.001)
        XCTAssertEqual(GoalProgress.fraction(for: goal, in: ctx), 0.5, accuracy: 0.001)
    }

    func testGoalProgressSumsMinutes() throws {
        let stack = PersistenceController(inMemory: true)
        let ctx = stack.container.viewContext

        let goal = FitnessGoal(context: ctx)
        goal.id = UUID()
        goal.goalCategory = .cardio
        goal.targetValue = 45
        goal.unit = .minutes
        goal.startDate = .distantPast
        goal.endDate = .distantFuture
        goal.isCompleted = false

        let w = WorkoutEntry(context: ctx)
        w.id = UUID()
        w.category = .cardio
        let start = Date()
        w.startDate = start
        w.endDate = start.addingTimeInterval(30 * 60)
        w.durationSeconds = 0
        w.syncToHealth = false

        try ctx.save()
        XCTAssertEqual(GoalProgress.currentValue(for: goal, in: ctx), 30, accuracy: 0.1)
    }
}
