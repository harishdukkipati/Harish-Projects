import Foundation
import CoreData
import HealthKit

enum WorkoutCategory: Int16, CaseIterable, Identifiable {
    case cardio = 0
    case strength = 1
    case flexibility = 2
    case sports = 3

    var id: Int16 { rawValue }

    var title: String {
        switch self {
        case .cardio: "Cardio"
        case .strength: "Strength"
        case .flexibility: "Flexibility"
        case .sports: "Sports"
        }
    }

    var symbolName: String {
        switch self {
        case .cardio: "figure.run"
        case .strength: "dumbbell.fill"
        case .flexibility: "figure.flexibility"
        case .sports: "sportscourt.fill"
        }
    }

    var hkActivityType: HKWorkoutActivityType {
        switch self {
        case .cardio: .running
        case .strength: .functionalStrengthTraining
        case .flexibility: .flexibility
        case .sports: .soccer
        }
    }
}

extension WorkoutEntry {
    var category: WorkoutCategory {
        get { WorkoutCategory(rawValue: categoryRaw) ?? .cardio }
        set { categoryRaw = newValue.rawValue }
    }
}

extension FitnessGoal {
    var goalCategory: WorkoutCategory {
        get { WorkoutCategory(rawValue: goalCategoryRaw) ?? .cardio }
        set { goalCategoryRaw = newValue.rawValue }
    }
}

enum GoalUnit: String, CaseIterable, Identifiable {
    case workouts = "workouts"
    case minutes = "minutes"
    case calories = "kcal"

    var id: String { rawValue }

    var displayTitle: String {
        switch self {
        case .workouts: "Workouts"
        case .minutes: "Minutes"
        case .calories: "Active calories"
        }
    }
}

extension FitnessGoal {
    var unit: GoalUnit {
        get { GoalUnit(rawValue: unitRaw ?? GoalUnit.workouts.rawValue) ?? .workouts }
        set { unitRaw = newValue.rawValue }
    }
}
