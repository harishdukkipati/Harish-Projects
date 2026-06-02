## Projects Completed

Here are 11 projects that I have completed over the past year.

---

### **Project 1: NBA Draft Scouting Platform**
I built an NBA Draft scouting platform that streamlines prospect evaluation for teams by combining rankings, stats, and reports in one interface.  

**Key Features:**
- Homepage with a **Big Board** ranking all draft-eligible players  
- Color-coded scout rankings (green = above consensus, red = below consensus)  
- Search by player or filter by school  
- Detailed player profiles with photos, combine measurements, game logs, season averages, and scouting reports  
- Built-in form for scouts to submit new reports  
- Centralized system for tracking outlier opinions and performance trends  

---

### **Project 2: Events Search App (Android)**
Built a full-stack, location-based **Android event discovery application** enabling users to search for nearby events, view detailed event information, and manage favorites with persistent storage.  

**Highlights:**
- Developed a responsive, **Material Design–compliant UI** using Kotlin, Android SDK, and Jetpack Compose  
- Designed and deployed a **scalable Node.js backend on Google Cloud Platform**  
- Integrated **Ticketmaster, Google Maps, and Spotify APIs** to deliver real-time event, venue, and artist data  
- Implemented **persistent favorites management with MongoDB Atlas**, allowing users to save and retrieve events across sessions  

---

### **Project 3: Multi-threaded HTTP Server (C)**
Developed a multi-threaded HTTP server in C, including:
- Creating and managing multiple threads  
- Implementing a bounded buffer  
- Using mutex locks to ensure atomic and coherent request processing  

---

### **Project 4: NBA Stat Predictor (Python)**
Developed a feedforward neural network to predict player stats for **Pacers and Thunder players during the 2025 NBA Finals** using historical performance data.

---

### **Project 5: NFL Chatbot**
Built an NFL chatbot powered by OpenAI’s Large Language Models to answer NFL-related queries.  

**Tech Highlights:**
- Stored 1000+ lines of raw NFL data as word embeddings in **Pinecone Vector Database**  
- Used semantic search to retrieve the most relevant information  
- Delivered accurate, context-aware responses to user questions  

---

### **Project 6: Pac-Man AI Optimization**
Implemented **Q-learning**, **DFS**, **BFS**, and **A\*** algorithms in Python to:
- Improve Pac-Man’s decision-making  
- Optimize pathfinding for maximum food consumption  

---

### **Project 7: Slack App Clone**
Developed a Slack-like messaging application using:
- **Frontend:** React  
- **Backend:** Node.js + Express  
- **Database:** PostgreSQL  

**Features:**
- Stored and retrieved user workspace, channel, and message data  
- Integrated backend server calls for seamless data flow and UI updates  

---

### **Project 8: N-gram Language Models**
Built unigram, bigram, and trigram language models to predict word sequences.  

**Evaluation:**
- Trained on text data to compute conditional probabilities  
- Measured model accuracy using **perplexity**  
- Compared performance across different n-gram sizes  

---

### **Project 9: Modular Code Processing (MCP) Server**
Created an intelligent Q&A system using **FastAPI**, **OpenAI GPT-4**, and the **Wikipedia API**.  

**Highlights:**
- Modular API endpoints for Wikipedia search, summary retrieval, and chatbot interaction  
- LLM dynamically extracts and synthesizes relevant information from external tools  
- Demonstrated orchestration of tool use for context-aware responses  

---

### **Project 10: Fitness Tracker (iOS)**
Built a native **SwiftUI** fitness companion for logging workouts, setting goals, and visualizing activity with optional **Apple Health** integration.

**Key Features:**
- **Core Data** persistence for workouts, goals, and synced health snapshots  
- **Dashboard** with **Swift Charts** for logged workout minutes and optional HealthKit series (steps, active energy, daily average heart rate)  
- **Workout log** with categories, start/end times, optional calories and notes, and list management (edit/delete)  
- Optional **save to Apple Health** for logged sessions when write access is granted  
- **Goals** by workout category with targets in workouts, minutes, or active calories, plus optional end dates  
- **Health settings** so users enable or disable dashboard Health reads and manage authorization via the Health app  

---

### **Project 11: March Madness Bracket Predictor (Python)**
Built an **NCAA tournament prediction and simulation** pipeline that joins historic Kaggle results with rating/resume data, trains a **logistic regression** model for matchup win probability, and runs **Monte Carlo bracket simulations** through a **FastAPI** backend.

**Key Features:**
- **Matchup model** on 2008–2025 tournament games using seed, resume, KenPom/Barttorvik, upset rates, head-to-head, recent form, and path-strength features  
- **Full-bracket simulation** with configurable temperature and hybrid deterministic/stochastic game resolution  
- **2026 live data** via game logs, bracket JSON, and Sweet 16 path inputs for post–First Four updates  
- **FastAPI endpoints** for round-of-64 matchups and multi-run championship frequency output  
- **ESPN scraping** and export scripts for refreshing game logs and training datasets  

---

