# Distributed LMS with LLM-based Tutoring and Raft-based Data Consistency

## Overview
This project implements a Distributed Learning Management System (LMS) designed to deliver a scalable, intelligent, and fault-tolerant educational platform.  
It integrates a fine-tuned Phi-3 Large Language Model (LLM) for context-aware tutoring and employs the Raft consensus algorithm to ensure data consistency and reliability across distributed nodes.  

The system supports seamless collaboration between students and instructors, maintaining high availability and strong consistency through distributed coordination and secure communication.

---

## Technologies Used
- Python – Core development language  
- gRPC – Remote Procedure Calls (RPC) for inter-node communication  
- SQLite – Lightweight database for persistent storage  
- Raft Protocol – Consensus algorithm for data consistency and fault tolerance  
- SHA-256 – Secure password hashing  
- AES-256 – Encryption for session tokens  
- Phi-3 LLM – Fine-tuned model providing intelligent responses to student queries  

---

## System Components and Services

### 1. Authentication Service
Handles user authentication and secure session management for students and instructors.
- `studentLogin` – Authenticates students and returns an AES-encrypted session token.  
- `facultyLogin` – Authenticates instructors and returns a valid session token with course details.

### 2. Materials Service
Manages course material uploads and retrieval.
- `courseMaterialUpload` – Uploads large files in chunks.  
- `getCourseContents` – Lists available materials for a course and term.  
- `getCourseMaterial` – Streams requested material to the client.

### 3. Assignments Service
Manages student submissions and instructor retrievals.
- `submitAssignment` – Allows students to submit assignments securely.  
- `getSubmittedAssignment` – Retrieves submissions mapped to student IDs.

### 4. Queries Service
Handles student-instructor interaction for academic queries.
- `createQuery` – Enables students to post course queries.  
- `getQueries` – Retrieves queries for specific courses.  
- `answerQuery` – Allows instructors to respond to queries.

### 5. LLM Service
Provides real-time, intelligent responses using the Phi-3 LLM.
- `askLlm` – Processes student questions and streams detailed, context-aware answers.

### 6. Raft Service
Ensures distributed consensus and synchronization among LMS nodes.
- `requestVote` – Handles leader election.  
- `appendEntries` – Replicates logs and ensures consistency.  
- `getLeader` – Returns the current Raft leader node ID.

---

## Database Design (SQLite)
- Users – Stores credentials, roles, and session tokens.  
- Courses – Contains course details and material file paths.  
- Assignments – Tracks submissions by student and course.  
- Queries – Stores student questions and instructor responses.  

The database integrates with Raft to replicate changes across all nodes, ensuring consistency and fault tolerance.

---

## Key Features
- Distributed, fault-tolerant LMS with real-time synchronization.  
- Secure authentication using SHA-256 and AES-256 encryption.  
- AI-powered tutoring via the fine-tuned Phi-3 LLM.  
- Raft-based consensus ensuring reliable multi-node operation.  
- Efficient RPC-based communication using gRPC.  
- Modular and extensible architecture for easy scaling.  

---

## Conclusion
This project combines Distributed Systems and Artificial Intelligence to build a reliable, scalable, and interactive LMS.  
Through Raft-based consistency and LLM-driven tutoring, it delivers a modern, intelligent learning experience optimized for both students and instructors.


