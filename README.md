1.	IIUC_CONNECT — Backend API Service
This repository contains the backend API service for IIUC Connect, a role-based university management system powering authentication, course operations, payments, and real-time notifications.
Frontend applications and other clients consume this API separately.
	Core Features
•	Role-Based Access Control: Admin, Teacher, Student
•	User Account Management: Registration, Login, Profile Update
•	Course & Routine Management
•	Academic Resource Management
•	Student Course Registration
•	Payment Handling (Student submissions, Admin view/edit)
•	Real-Time Notifications via WebSockets
•	Modular & Extensible Backend Architecture
•	Secure Token-Based Authorization (JWT)
* This README contains public-safe information only. Sensitive configurations, environment variables, or credentials are intentionally excluded.

2.	Project Structure
iiuc_connect/
├── accounts/          # User authentication & profile
├── course/            # Course & registration management
├── routine/           # Academic schedule management
├── notification/      # WebSocket & notification system
├── event/             # Event Management
├── iiuc_connect/      # Project settings & ASGI configuration
├── manage.py
└── requirements.txt	#Dependency


3.	API Overview
•	JSON-based communication
•	Role-based authorization required for protected endpoints
•	HTTP verbs: GET, POST, PUT, DELETE used meaningfully
•	Structured responses for success and error handling
Detailed API documentation is not included publicly.
4.	Development Setup
1.	Install dependencies
pip install -r requirements.txt
2. Start development server
python manage.py runserver

3.Real-Time Features
To enable WebSocket support (Daphne/ASGI):
daphne -p 8000 iiuc_connect.asgi:application
5.	WebSocket (Overview)
•	Endpoint: ws://127.0.0.1:8000/ws/notifications/?token=<JWT_TOKEN>
•	Purpose: Real-time notifications for users,  admin inactive-user updates
•	Client Example (JavaScript):
const ws = new WebSocket(
  `ws://127.0.0.1:8000/ws/notifications/?token=${token}`
);

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  console.log("WS Message:", msg);
};

6.	 Security Note
The public repository does not include:
•	Environment variables or secrets
•	Database connection strings
•	Cloud service credentials
•	Internal architecture or server details
•	Role restriction implementation
•	WebSocket authentication details
All sensitive information is kept private.
7.	 Purpose
•	Provides backend API for IIUC Connect system
•	Supports frontend 
•	Open for community review without exposing internal logic
•	Maintains clear separation between frontend and backend

8.	 License
No license applied — all rights reserved by the project owner.

