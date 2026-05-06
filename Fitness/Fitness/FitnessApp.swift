import SwiftUI

@main
struct FitnessApp: App {
    private let persistence = PersistenceController.shared
    private let healthKit = HealthKitService()

    var body: some Scene {
        WindowGroup {
            MainTabView(healthKit: healthKit)
                .environment(\.managedObjectContext, persistence.container.viewContext)
                .tint(FitbitTheme.accent)
        }
    }
}
