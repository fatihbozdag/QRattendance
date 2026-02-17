# QR Code Attendance System — Project Recap & Claude Code Prompts

## Project Overview

A web-based QR code attendance tracking application for university classes that evolves into a full student portal. The system addresses the pain of manually taking attendance in large classes (70+ students) by letting students scan QR codes to self-register their attendance.

---

## Key Requirements

### Core Attendance System
- **4 static QR codes** — one per class/course
- **Schedule-based activation** — QR codes only work during the scheduled class time for that course
- **IP-based fraud prevention** — each student's IP is logged on first scan; duplicate IPs are rejected for the same session
- **Student ID entry** — students enter their student number after scanning
- **14-week term** — attendance tracked across the full semester

### Expanded Student Dashboard
- **Attendance history** — students view their full attendance record, including dates present and absent
- **Course materials** — instructors upload lecture notes and resources; students can view/download them
- **Grades** — students see their marks for quizzes, midterms, and finals per course
- **Exam papers** — instructors upload scanned exam papers so students can review their graded work

### Security & Access Control
- **Basic attendance:** no login required — IP + schedule-based restrictions are sufficient
- **Dashboard access:** one-time PIN sent via university email for each login session (no permanent passwords)
- **Role-based access:** students only see their own data; instructors manage courses
- **Session expiration:** tokens expire after inactivity to prevent unauthorized access
- **Audit logging:** all data access attempts are logged

---

## Claude Code Prompts

### Prompt 1 — Project Initialization & Core Attendance System

```
I'm building a web-based QR code attendance system for university classes. Here are the requirements:

Core concept:
- I teach 4 classes at a university. Each class gets one static QR code that stays the same all semester.
- Students scan the QR code on their phone, enter their student ID, and their attendance is marked.

Fraud prevention:
- Schedule-based activation: each QR code only accepts attendance submissions during the scheduled class time for that course. Outside of that window, the form is disabled.
- IP-based restriction: once a student's IP address is recorded for a session, no further submissions are accepted from that IP for that class session. This prevents students from marking attendance for absent classmates.

Technical details:
- 14-week semester with a configurable class schedule (day of week, start time, end time per course)
- Store attendance records with: student ID, course ID, session date, timestamp, IP address
- Simple admin panel for me (the instructor) to view attendance records and export reports

Please set up the complete project:
1. Initialize the repository with proper folder structure and Git
2. Choose a clean, modern tech stack (suggest what works best)
3. Design the database schema for students, courses, schedules, and attendance records
4. Create the QR code scanning flow (landing page after scan → student ID entry → confirmation)
5. Implement the schedule-based activation and IP-based fraud prevention logic
6. Build a basic admin dashboard for viewing attendance by course and session
7. Add a README with setup instructions

Keep the codebase clean, well-commented, and maintainable. I'll be developing this myself, so clarity matters.
```

---

### Prompt 2 — Student Dashboard & Portal Expansion

```
Expand the QR code attendance system with a student portal and dashboard. Here's what to add:

Authentication:
- Students log in using their student ID + a one-time PIN sent to their university email
- PINs expire after 30 minutes of inactivity
- No permanent passwords — each login generates a fresh PIN
- This prevents account sharing and unauthorized access

Student Dashboard — after login, students see:
1. Attendance history: full record for the 14-week term showing dates present, absent, and attendance percentage per course
2. Course materials: downloadable lecture notes and resources organized by week/topic, uploaded by the instructor
3. Grades: marks for quizzes, midterms, and final exams broken down by assessment type per course
4. Exam papers: scanned/uploaded graded exam papers that students can view and download

Instructor (Admin) Enhancements:
- Upload course materials per course per week
- Enter and manage grades per student per assessment
- Upload scanned exam papers linked to specific students and assessments
- View and export attendance and grade reports

Security:
- Role-based access control: students only see their own data, instructors manage all courses
- Row-level security on all database queries — filter by authenticated student ID
- Session-based authentication with automatic expiration
- Audit logging for all data access attempts
- HTTPS for all communication

Database additions:
- Course materials table (course, week, title, file path, upload date)
- Grades table (student ID, course, assessment type, mark, date)
- Exam papers table (student ID, course, assessment type, file path, upload date)
- Sessions table (student ID, token, created at, expires at)

Please update the project structure, database schema, API endpoints, and frontend to support these features. Build incrementally — start with authentication and attendance history, then add materials, grades, and exam papers.
```

---

## Development Roadmap

| Phase | Features | Priority |
|-------|----------|----------|
| 1 | Project setup, QR scanning, schedule-based activation, IP fraud prevention | High |
| 2 | Admin panel for viewing/exporting attendance | High |
| 3 | Student authentication (email PIN) | Medium |
| 4 | Student dashboard with attendance history | Medium |
| 5 | Course materials upload and access | Medium |
| 6 | Grades entry and student viewing | Medium |
| 7 | Exam paper upload and student viewing | Low |
