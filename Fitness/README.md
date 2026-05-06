## Fitness – SwiftUI, Core Data, HealthKit

A native **iOS fitness companion** for logging workouts, setting goals, and viewing activity trends. The app stores sessions locally with **Core Data**, optionally syncs logged workouts to **Apple Health**, and can surface **HealthKit** metrics (steps, active energy, heart rate) on a chart-based dashboard when the user enables read access.

---

### Features

- **Dashboard** – Swift Charts for logged workout minutes plus optional Apple Health series (steps, active energy, daily average heart rate); pull to refresh and automatic load on appear  
- **Workout log** – Category (cardio, strength, flexibility, sports), start/end times, optional calories and notes; list of recent entries with edit/delete  
- **Optional save to Health** – Toggle to write workouts to Apple Health when permitted  
- **Goals** – Create goals by category with units (workouts, minutes, active calories) and optional end date; progress tracking via Core Data  
- **Health settings** – User-controlled toggle to show Apple Health data on the dashboard; authorization flow and guidance for managing sharing in the Health app  
- **UI** – SwiftUI tab navigation with a Fitbit-inspired theme

---

### Tech stack

**Client**

- Swift, SwiftUI  
- Core Data (workouts, goals, synced health snapshots)  
- HealthKit (read: steps, active energy, heart rate; write: workouts)  
- Swift Charts

**Tooling**

- Xcode (iOS project: `Fitness.xcodeproj`)  
- Unit and UI test targets (`FitnessTests`, `FitnessUITests`)

---

### App overview


| Tab           | Purpose                                                                                                     |
| ------------- | ----------------------------------------------------------------------------------------------------------- |
| **Dashboard** | Charts for logged minutes and (if enabled) Health metrics over a rolling window (default 7 days)            |
| **Log**       | Form to add workouts and browse/delete recent logs                                                          |
| **Goals**     | Add and manage category-based goals                                                                         |
| **Health**    | Enable or disable dashboard Health integration; workout logging to Health remains available where supported |


---

### Running the app

1. Open `Fitness.xcodeproj` in **Xcode** on a Mac.
2. Select an iPhone simulator or a **physical device** (HealthKit behaves more realistically on device).
3. Build and run the **Fitness** scheme.

For dashboard Health charts and saving workouts to Apple Health, grant the requested permissions when prompted; adjust individual data types later in the **Health** app under **Sharing → Apps → Fitness**.

---

### Highlights

- Built a **SwiftUI** iOS app with **Core Data** persistence for workouts and goals  
- Integrated **HealthKit** for optional read/write: dashboard metrics when allowed, and writing logged workouts to Apple Health  
- Used **Swift Charts** for clear, readable activity visualizations aligned with the app theme

