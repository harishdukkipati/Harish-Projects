import CoreData

struct PersistenceController {
    static let shared = PersistenceController()

    let container: NSPersistentContainer

    static var preview: PersistenceController = {
        let controller = PersistenceController(inMemory: true)
        let ctx = controller.container.viewContext
        let workout = WorkoutEntry(context: ctx)
        workout.id = UUID()
        workout.category = .cardio
        workout.startDate = Date().addingTimeInterval(-3600)
        workout.endDate = Date()
        workout.durationSeconds = 3600
        workout.notes = "Morning run"
        workout.syncToHealth = false
        let goal = FitnessGoal(context: ctx)
        goal.id = UUID()
        goal.goalCategory = .strength
        goal.targetValue = 4
        goal.unitRaw = GoalUnit.workouts.rawValue
        goal.startDate = Calendar.current.startOfDay(for: Date())
        goal.isCompleted = false
        try? ctx.save()
        return controller
    }()

    init(inMemory: Bool = false) {
        container = NSPersistentContainer(name: "FitnessModel")
        if inMemory {
            let description = NSPersistentStoreDescription()
            description.type = NSInMemoryStoreType
            container.persistentStoreDescriptions = [description]
        }
        container.loadPersistentStores { _, error in
            if let error = error as NSError? {
                fatalError("Core Data failed to load: \(error), \(error.userInfo)")
            }
        }
        container.viewContext.automaticallyMergesChangesFromParent = true
        container.viewContext.mergePolicy = NSMergeByPropertyObjectTrumpMergePolicy
    }

    func newBackgroundContext() -> NSManagedObjectContext {
        container.newBackgroundContext()
    }
}
