import SwiftUI
import CoreData

struct WorkoutLogView: View {
    @Environment(\.managedObjectContext) private var context
    let healthKit: HealthKitProviding

    @FetchRequest(
        sortDescriptors: [NSSortDescriptor(keyPath: \WorkoutEntry.startDate, ascending: false)],
        animation: .default
    )
    private var workouts: FetchedResults<WorkoutEntry>

    @State private var category: WorkoutCategory = .cardio
    @State private var startDate = Date()
    @State private var endDate = Date().addingTimeInterval(3600)
    @State private var caloriesText = ""
    @State private var notes = ""
    @State private var syncToHealth = false
    @State private var saveError: String?
    @State private var isSaving = false

    @FocusState private var focusedField: LogField?

    private enum LogField: Hashable {
        case calories
        case notes
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("New workout") {
                    Picker("Category", selection: $category) {
                        ForEach(WorkoutCategory.allCases) { c in
                            Label(c.title, systemImage: c.symbolName).tag(c)
                        }
                    }
                    .accessibilityIdentifier("log_category_picker")
                    DatePicker("Start", selection: $startDate)
                    DatePicker("End", selection: $endDate)
                    TextField("Calories (optional)", text: $caloriesText)
                        .keyboardType(.decimalPad)
                        .focused($focusedField, equals: .calories)
                    TextField("Notes", text: $notes, axis: .vertical)
                        .lineLimit(2...4)
                        .focused($focusedField, equals: .notes)
                    Toggle("Save to Apple Health", isOn: $syncToHealth)
                        .disabled(!healthKit.isHealthDataAvailable)
                    if !healthKit.isHealthDataAvailable {
                        Text("Health not available on this device.")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    if let saveError {
                        Text(saveError).foregroundStyle(.red).font(.caption)
                    }
                    Button(action: saveWorkout) {
                        if isSaving { ProgressView() }
                        else { Text("Save workout") }
                    }
                    .disabled(isSaving || endDate <= startDate)
                    .accessibilityIdentifier("log_save_button")
                }

                Section {
                    Text("Swipe left on a row to delete, or tap Edit (top right).")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Section("Recent") {
                    if workouts.isEmpty {
                        Text("No workouts yet.")
                            .foregroundStyle(.secondary)
                            .accessibilityIdentifier("log_list_empty")
                    } else {
                        ForEach(workouts) { entry in
                            WorkoutRow(entry: entry)
                                .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                                    Button(role: .destructive) {
                                        deleteEntry(entry)
                                    } label: {
                                        Label("Delete", systemImage: "trash")
                                    }
                                    .accessibilityIdentifier("log_row_delete_\(entry.objectID.uriRepresentation().absoluteString)")
                                }
                                .accessibilityIdentifier("log_row_\(entry.objectID.uriRepresentation().absoluteString)")
                        }
                        .onDelete(perform: delete)
                    }
                }
            }
            .scrollDismissesKeyboard(.interactively)
            .navigationTitle("Log workout")
            .toolbar {
                ToolbarItemGroup(placement: .keyboard) {
                    Spacer()
                    Button("Done") { focusedField = nil }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    EditButton()
                }
            }
            .accessibilityIdentifier("log_root")
        }
    }

    private func saveWorkout() {
        focusedField = nil
        saveError = nil
        isSaving = true
        let calories = Double(caloriesText.trimmingCharacters(in: .whitespaces))
        let entry = WorkoutEntry(context: context)
        entry.id = UUID()
        entry.category = category
        entry.startDate = startDate
        entry.endDate = endDate
        entry.durationSeconds = Int32(endDate.timeIntervalSince(startDate))
        entry.caloriesBurned = calories ?? 0
        entry.notes = notes.isEmpty ? nil : notes
        entry.syncToHealth = syncToHealth && healthKit.isHealthDataAvailable
        do {
            try context.save()
            notes = ""
            caloriesText = ""
            let shouldSync = entry.syncToHealth
            let cat = category
            let s = startDate
            let e = endDate
            if shouldSync {
                Task {
                    do {
                        try await healthKit.requestAuthorization()
                        try await healthKit.saveWorkout(category: cat, start: s, end: e, calories: calories)
                    } catch {
                        await MainActor.run { saveError = error.localizedDescription }
                    }
                    await MainActor.run { isSaving = false }
                }
            } else {
                isSaving = false
            }
        } catch {
            saveError = error.localizedDescription
            context.delete(entry)
            isSaving = false
        }
    }

    private func deleteEntry(_ entry: WorkoutEntry) {
        context.delete(entry)
        try? context.save()
    }

    private func delete(at offsets: IndexSet) {
        offsets.map { workouts[$0] }.forEach(context.delete)
        try? context.save()
    }
}

private struct WorkoutRow: View {
    @ObservedObject var entry: WorkoutEntry

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(entry.category.title)
                .font(.headline)
            if let start = entry.startDate {
                Text(start.formatted(date: .abbreviated, time: .shortened))
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            if let notes = entry.notes, !notes.isEmpty {
                Text(notes).font(.caption).foregroundStyle(.secondary)
            }
        }
    }
}
