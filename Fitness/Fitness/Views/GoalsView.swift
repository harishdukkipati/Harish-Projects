import SwiftUI
import CoreData

struct GoalsView: View {
    @Environment(\.managedObjectContext) private var context

    @FetchRequest(
        sortDescriptors: [NSSortDescriptor(keyPath: \FitnessGoal.startDate, ascending: false)],
        animation: .default
    )
    private var goals: FetchedResults<FitnessGoal>

    @State private var category: WorkoutCategory = .cardio
    @State private var unit: GoalUnit = .workouts
    @State private var targetText = "3"
    @State private var hasEndDate = false
    @State private var endDate = Date().addingTimeInterval(86400 * 7)

    @FocusState private var targetFieldFocused: Bool

    var body: some View {
        NavigationStack {
            List {
                Section("New goal") {
                    Picker("Category", selection: $category) {
                        ForEach(WorkoutCategory.allCases) { c in
                            Text(c.title).tag(c)
                        }
                    }
                    .accessibilityIdentifier("goals_category_picker")
                    Picker("Unit", selection: $unit) {
                        ForEach(GoalUnit.allCases) { u in
                            Text(u.displayTitle).tag(u)
                        }
                    }
                    TextField("Target", text: $targetText)
                        .keyboardType(.decimalPad)
                        .focused($targetFieldFocused)
                        .accessibilityIdentifier("goals_target_field")
                    Toggle("End date", isOn: $hasEndDate)
                    if hasEndDate {
                        DatePicker("End", selection: $endDate, displayedComponents: .date)
                    }
                    Button("Add goal") {
                        targetFieldFocused = false
                        addGoal()
                    }
                    .accessibilityIdentifier("goals_add_button")
                }

                Section("Your goals") {
                    if goals.isEmpty {
                        Text("No goals yet.")
                            .foregroundStyle(.secondary)
                            .accessibilityIdentifier("goals_list_empty")
                    } else {
                        ForEach(goals) { goal in
                            GoalRow(goal: goal)
                        }
                        .onDelete(perform: delete)
                    }
                }
            }
            .scrollDismissesKeyboard(.interactively)
            .navigationTitle("Goals")
            .toolbar {
                ToolbarItemGroup(placement: .keyboard) {
                    Spacer()
                    Button("Done") { targetFieldFocused = false }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    EditButton()
                }
            }
            .accessibilityIdentifier("goals_root")
        }
    }

    private func addGoal() {
        guard let target = Double(targetText), target > 0 else { return }
        let g = FitnessGoal(context: context)
        g.id = UUID()
        g.goalCategory = category
        g.unit = unit
        g.targetValue = target
        g.startDate = Calendar.current.startOfDay(for: Date())
        g.endDate = hasEndDate ? Calendar.current.startOfDay(for: endDate) : nil
        g.isCompleted = false
        try? context.save()
        targetText = "3"
    }

    private func delete(at offsets: IndexSet) {
        offsets.map { goals[$0] }.forEach(context.delete)
        try? context.save()
    }
}

private struct GoalRow: View {
    @ObservedObject var goal: FitnessGoal
    @Environment(\.managedObjectContext) private var context

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(goal.goalCategory.title)
                .font(.headline)
            let current = GoalProgress.currentValue(for: goal, in: context)
            ProgressView(value: GoalProgress.fraction(for: goal, in: context)) {
                Text("\(format(current)) / \(format(goal.targetValue)) \(goal.unit.displayTitle)")
                    .font(.subheadline)
            }
            if goal.isCompleted {
                Text("Completed")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.vertical, 4)
        .accessibilityIdentifier("goal_row_\(goal.objectID.uriRepresentation().absoluteString)")
    }

    private func format(_ v: Double) -> String {
        if v.rounded() == v { return String(Int(v)) }
        return String(format: "%.1f", v)
    }
}
