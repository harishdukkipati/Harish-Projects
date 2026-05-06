import Foundation

/// User preference: when true, Dashboard loads charts from HealthKit and may request system authorization.
enum AppHealthSync {
    static let userDefaultsKey = "fitness.appleHealthDashboardSync"

    static var isEnabled: Bool {
        UserDefaults.standard.bool(forKey: userDefaultsKey)
    }
}
