# 🌐 Project 2: Multi-threaded HTTP Server (C)

## 📖 Overview
I developed a **multi-threaded HTTP server in C** that demonstrates the fundamentals of **client-server architecture** and **parallel processing**. The project focused on handling multiple client requests efficiently while maintaining thread safety and coherent request handling.

---

## 🚀 Features
- Implemented a **client-server model** using sockets in C  
- Supported multiple HTTP methods such as **GET** and **PUT**  
- Created a **bounded buffer** to manage incoming client requests  
- Used **multi-threading** to process requests in parallel for improved performance  
- Integrated **mutex locks** to ensure atomic operations and prevent race conditions  
- Designed the system to scale with multiple simultaneous client connections  

---

## ⚙️ Technical Highlights
- **Language:** C  
- **Concurrency:** POSIX Threads (pthreads)  
- **Synchronization:** Mutex locks and condition variables  
- **Networking:** Socket programming (TCP/IP)  
- **Data Structures:** Bounded buffer for request management  

---

## 🧩 Learning Outcomes
This project gave me hands-on experience with:
- **Systems programming in C**  
- **Concurrency control** and avoiding common pitfalls like deadlocks and race conditions  
- **Low-level networking** through socket APIs  
- Building the foundations of a simple but functional **HTTP server**  


