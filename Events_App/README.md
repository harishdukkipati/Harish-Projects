## 📍 Events Search App – Kotlin, Android, Node.js, MongoDB  
**October 2025 – November 2025**

A full-stack, location-based **Android event discovery application** that enables users to search for nearby events, explore detailed event information, and manage favorites with persistent storage. The app follows **Material Design 3** principles and integrates multiple third-party APIs through a scalable cloud backend.

---

### ✨ Features

- Keyword-based event search with category and distance filtering  
- Location-aware discovery using current or specified locations  
- Real-time event, venue, and artist data  
- Persistent favorites saved across sessions  
- Rich event detail views with artists, venue info, and ticketing links  
- Responsive, modern UI built with Jetpack Compose  

---

### 🛠️ Tech Stack

**Frontend**
- Kotlin  
- Android SDK  
- Jetpack Compose  
- Material Design 3  
- Retrofit + OkHttp  
- Coil (image loading)

**Backend**
- Node.js  
- Express  
- MongoDB Atlas  
- Google Cloud Platform (GCP)

**APIs**
- Ticketmaster API (events, venues, ticketing)  
- Google Maps & Geocoding APIs (location and distance filtering)  
- Spotify API (artist data and albums)

---

### 📱 App Overview

#### Home Screen
- Displays favorited events  
- Empty-state message when no favorites exist  
- External “Powered by Ticketmaster” link  

#### Search Screen
- Keyword input with validation  
- Location selector (current location supported)  
- Distance and category filters  
- Asynchronous loading with progress indicators  
- Graceful handling of empty search results  

#### Search Results
- Scrollable list of event cards  
- Event name, venue, date/time, and category  
- Favorite toggle (star icon) on each event  

#### Event Details
Each event includes three tabs:
- **Details**: date/time, genres, ticket status, seat map, and buy-ticket link  
- **Artists**: Spotify integration with follower counts, popularity, and albums  
- **Venue**: venue name, address, image, and external Ticketmaster link  

Users can share events using Android’s native share modal and manage favorites directly from the event detail view.

---

### 🧠 Backend Architecture

- Scalable **Node.js backend deployed on Google Cloud Platform**  
- Aggregates and normalizes data from Ticketmaster, Google Maps, and Spotify APIs  
- Exposes RESTful endpoints consumed by the Android client  
- Uses **MongoDB Atlas** for persistent favorites management  
- Fully asynchronous, non-blocking API requests  

---

### 📌 Highlights

- Built a **location-based event discovery Android app** using Kotlin, Android SDK, and Jetpack Compose with a responsive, Material Design–compliant UI  
- Designed and deployed a **scalable Node.js backend on GCP**, integrating Ticketmaster, Google Maps, and Spotify APIs for real-time data delivery  
- Implemented **persistent favorites management with MongoDB Atlas**, allowing users to save and retrieve events across sessions, improving usability and reliability  

---

### ▶️ Running the App

1. Clone the repository  
2. Configure backend API keys  
3. Start the Node.js backend (locally or on GCP)  
4. Open the Android project in **Android Studio**  
5. Run on a Pixel emulator (API 36 recommended)  

