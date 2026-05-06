import SwiftUI

/// Settings for Apple Health. Toggle controls whether Dashboard reads Health data; Log can still offer “Save to Apple Health” when Health is available.
struct HealthSettingsView: View {
    let healthKit: HealthKitProviding

    @AppStorage(AppHealthSync.userDefaultsKey) private var appleHealthSyncEnabled = false

    @State private var isRequesting = false
    @State private var showManageInHealthAppAlert = false
    @State private var authErrorMessage: String?
    @State private var showAuthError = false

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Toggle(
                        "Show Apple Health data on Dashboard",
                        isOn: syncToggleBinding
                    )
                    .disabled(!healthKit.isHealthDataAvailable || isRequesting)
                    .accessibilityIdentifier("health_sync_toggle")
                    if isRequesting {
                        HStack {
                            ProgressView()
                            Text("Connecting…")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                    }
                    if !healthKit.isHealthDataAvailable {
                        Text("Health is not available on this device.")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                } footer: {
                    if appleHealthSyncEnabled {
                        Text("Turn off anytime to stop loading Health charts on Dashboard (logged workouts are unchanged).")
                    } else {
                        Text("Turn this on to allow Dashboard to read steps, active energy, and heart rate from Apple Health.")
                    }
                }

                if !appleHealthSyncEnabled {
                    introSections
                }

                if appleHealthSyncEnabled {
                    Section {
                        Button("How to change sharing in the Health app") {
                            showManageInHealthAppAlert = true
                        }
                        .accessibilityIdentifier("health_manage_sharing_button")
                    }
                }
            }
            .navigationTitle("Health settings")
            .accessibilityIdentifier("health_settings_root")
            .alert("Manage Apple Health sharing", isPresented: $showManageInHealthAppAlert) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(
                    "Open the Health app, then go to Sharing → Apps → Fitness. "
                    + "There you can turn individual data types on or off for this app."
                )
            }
            .alert("Couldn’t connect to Health", isPresented: $showAuthError) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(authErrorMessage ?? "Unknown error")
            }
        }
    }

    /// Turning on sets the preference immediately, runs authorization, then shows the Health-app info alert. Reverts on failure.
    private var syncToggleBinding: Binding<Bool> {
        Binding(
            get: { appleHealthSyncEnabled },
            set: { newValue in
                if newValue {
                    appleHealthSyncEnabled = true
                    Task { await turnOnDashboardHealthSync() }
                } else {
                    appleHealthSyncEnabled = false
                }
            }
        )
    }

    private var introSections: some View {
        Group {
            Section {
                Text(
                    "Charts for steps, active energy, and heart rate live on the Dashboard tab and only load when the toggle above is on."
                )
                .font(.subheadline)
                .foregroundStyle(.secondary)
            }

            Section("What Fitness uses from Health") {
                Label("Read: step count, active energy, heart rate (Dashboard charts)", systemImage: "chart.line.uptrend.xyaxis")
                Label("Write: workouts when you enable Save to Apple Health on the Log tab", systemImage: "figure.run")
            }
            .font(.subheadline)

            Section("Workout saving status") {
                Text(workoutWriteStatusExplanation)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        }
    }

    private var workoutWriteStatusExplanation: String {
        switch healthKit.workoutWriteAccess {
        case .notAvailable:
            return "Health is not available on this device."
        case .notDetermined:
            return "Saving workouts to Health is not configured yet. Turn on the toggle above, or add a workout with Save to Apple Health on the Log tab."
        case .denied:
            return "This app is not allowed to save workouts. Open the Health app → Sharing → Apps → Fitness and turn on Workouts."
        case .authorized:
            return "You’ve allowed saving workouts. When Save to Apple Health is on for a log entry, that session is written to Apple Health."
        }
    }

    private func turnOnDashboardHealthSync() async {
        guard healthKit.isHealthDataAvailable else {
            await MainActor.run { appleHealthSyncEnabled = false }
            return
        }
        isRequesting = true
        defer { isRequesting = false }
        do {
            try await healthKit.requestAuthorization()
            await MainActor.run {
                showManageInHealthAppAlert = true
            }
        } catch {
            await MainActor.run {
                appleHealthSyncEnabled = false
                authErrorMessage = error.localizedDescription
                showAuthError = true
            }
        }
    }
}
