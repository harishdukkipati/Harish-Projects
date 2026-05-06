import SwiftUI
import CoreData

struct MainTabView: View {
    @Environment(\.managedObjectContext) private var context
    let healthKit: HealthKitService

    @State private var dashboardVM: DashboardViewModel?

    var body: some View {
        TabView {
            Group {
                if let vm = dashboardVM {
                    DashboardView(viewModel: vm)
                } else {
                    ProgressView("Loading…")
                }
            }
            .tabItem { Label("Dashboard", systemImage: "chart.xyaxis.line") }

            WorkoutLogView(healthKit: healthKit)
                .tabItem { Label("Log", systemImage: "plus.circle.fill") }

            GoalsView()
                .tabItem { Label("Goals", systemImage: "target") }

            HealthSettingsView(healthKit: healthKit)
                .tabItem { Label("Health", systemImage: "heart.fill") }
        }
        .accessibilityIdentifier("main_tab_view")
        .onAppear {
            if dashboardVM == nil {
                dashboardVM = DashboardViewModel(healthKit: healthKit, context: context)
            }
        }
    }
}
