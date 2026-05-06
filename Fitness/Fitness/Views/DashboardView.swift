import SwiftUI
import Charts

struct DashboardView: View {
    @Environment(\.colorScheme) private var colorScheme
    @Bindable var viewModel: DashboardViewModel

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    if let err = viewModel.healthError {
                        Text(err)
                            .font(.subheadline)
                            .foregroundStyle(.orange)
                            .padding(12)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(Color.orange.opacity(0.12), in: RoundedRectangle(cornerRadius: 12))
                            .accessibilityIdentifier("dashboard_health_error")
                    }

                    sectionCard(title: "Logged minutes", systemImage: "clock.fill") {
                        if viewModel.loggedMinutesSeries.isEmpty {
                            emptyState(
                                message: "No workouts in this range.",
                                hint: "Log a session on the Log tab to see minutes here.",
                                icon: "figure.strengthtraining.traditional"
                            )
                            .accessibilityIdentifier("dashboard_logged_empty")
                        } else {
                            Chart(viewModel.loggedMinutesSeries) { point in
                                BarMark(
                                    x: .value("Day", point.dayStart, unit: .day),
                                    y: .value("Minutes", point.value)
                                )
                                .foregroundStyle(FitbitTheme.chartGradient)
                            }
                            .frame(height: 180)
                            .chartXAxis(.visible)
                            .chartYAxis(.visible)
                            .accessibilityIdentifier("dashboard_logged_chart")
                        }
                    }

                    sectionCard(title: "Steps (Health)", systemImage: "figure.walk") {
                        if viewModel.isLoadingHealth && viewModel.stepsSeries.isEmpty {
                            ProgressView("Loading Health…")
                                .frame(maxWidth: .infinity, minHeight: 100)
                        } else if viewModel.stepsSeries.isEmpty {
                            emptyState(
                                message: "No step data in this range",
                                hint: "Allow read access to Steps in the Health app, or add steps via another tracker. Pull to refresh.",
                                icon: "heart.text.square.fill"
                            )
                            .accessibilityIdentifier("dashboard_steps_empty")
                        } else {
                            Chart(viewModel.stepsSeries) { point in
                                LineMark(
                                    x: .value("Day", point.dayStart, unit: .day),
                                    y: .value("Steps", point.value)
                                )
                                .foregroundStyle(FitbitTheme.chartGradient)
                                .interpolationMethod(.catmullRom)
                            }
                            .frame(height: 160)
                            .accessibilityIdentifier("dashboard_steps_chart")
                        }
                    }

                    sectionCard(title: "Active energy (Health)", systemImage: "flame.fill") {
                        if viewModel.isLoadingHealth && viewModel.energySeries.isEmpty {
                            ProgressView("Loading Health…")
                                .frame(maxWidth: .infinity, minHeight: 100)
                        } else if viewModel.energySeries.isEmpty {
                            emptyState(
                                message: "No active energy in this range",
                                hint: "Grant access to Active Energy, then refresh.",
                                icon: "leaf.fill"
                            )
                            .accessibilityIdentifier("dashboard_energy_empty")
                        } else {
                            Chart(viewModel.energySeries) { point in
                                AreaMark(
                                    x: .value("Day", point.dayStart, unit: .day),
                                    y: .value("kcal", point.value)
                                )
                                .foregroundStyle(FitbitTheme.energyGradient)
                            }
                            .frame(height: 160)
                            .accessibilityIdentifier("dashboard_energy_chart")
                        }
                    }

                    sectionCard(title: "Heart rate (daily avg, Health)", systemImage: "waveform.path.ecg") {
                        if viewModel.isLoadingHealth && viewModel.heartSeries.isEmpty {
                            ProgressView("Loading Health…")
                                .frame(maxWidth: .infinity, minHeight: 100)
                        } else if viewModel.heartSeries.isEmpty {
                            emptyState(
                                message: "No heart rate averages in this range",
                                hint: "Heart rate needs samples in Apple Health (more reliable on a physical device).",
                                icon: "heart.fill"
                            )
                            .accessibilityIdentifier("dashboard_heart_empty")
                        } else {
                            Chart(viewModel.heartSeries) { point in
                                LineMark(
                                    x: .value("Day", point.dayStart, unit: .day),
                                    y: .value("BPM", point.value)
                                )
                                .foregroundStyle(FitbitTheme.accentBright)
                                .interpolationMethod(.catmullRom)
                            }
                            .frame(height: 160)
                            .accessibilityIdentifier("dashboard_heart_chart")
                        }
                    }
                }
                .padding()
            }
            .background(Color(uiColor: .systemGroupedBackground))
            .navigationTitle("Dashboard")
            .accessibilityIdentifier("dashboard_root")
            .refreshable {
                await viewModel.refresh()
            }
            .task {
                await viewModel.refresh()
            }
        }
    }

    @ViewBuilder
    private func sectionCard<Content: View>(title: String, systemImage: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Label(title, systemImage: systemImage)
                .font(.headline)
                .foregroundStyle(FitbitTheme.accent)
            content()
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .fill(FitbitTheme.cardBackground(colorScheme))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .strokeBorder(FitbitTheme.cardStroke(colorScheme), lineWidth: 1)
        )
    }

    private func emptyState(message: String, hint: String, icon: String) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 10) {
                Image(systemName: icon)
                    .font(.title2)
                    .foregroundStyle(FitbitTheme.chartGradient)
                Text(message)
                    .font(.subheadline)
                    .foregroundStyle(.primary)
            }
            Text(hint)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.vertical, 8)
    }
}
