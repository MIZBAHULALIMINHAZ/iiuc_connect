1.	IIUC_CONNECT — Backend API Service<br/>
This repository contains the backend API service for IIUC Connect, a role-based university management system powering authentication, course operations, payments, and real-time notifications.
Frontend applications and other clients consume this API separately.
	Core Features<br/>
•	Role-Based Access Control: Admin, Teacher, Student<br/>
•	User Account Management: Registration, Login, Profile Update<br/>
•	Course & Routine Management<br/>
•	Academic Resource Management<br/>
•	Student Course Registration<br/>
•	Payment Handling (Student submissions, Admin view/edit)<br/>
•	Real-Time Notifications via WebSockets<br/>
•	Modular & Extensible Backend Architecture<br/>
•	Secure Token-Based Authorization (JWT)<br/>
* This README contains public-safe information only. Sensitive configurations, environment variables, or credentials are intentionally excluded.<br/>

2.	Project Structure <br/>
iiuc_connect/ <br/>
├── accounts/          # User authentication & profile <br/>
├── course/            # Course & registration management <br/>
├── routine/           # Academic schedule management <br/>
├── notification/      # WebSocket & notification system <br/>
├── event/             # Event Management <br/>
├── iiuc_connect/      # Project settings & ASGI configuration <br/>
├── manage.py <br/>
└── requirements.txt	#Dependency <br/>


3.	API Overview<br/>
•	JSON-based communication<br/>
•	Role-based authorization required for protected endpoints<br/>
•	HTTP verbs: GET, POST, PUT, DELETE used meaningfully<br/>
•	Structured responses for success and error handling<br/>
Detailed API documentation is not included publicly.<br/>
4.	Development Setup<br/>
1.	Install dependencies<br/>
pip install -r requirements.txt<br/>
2. Start development server<br/>
python manage.py runserver<br/>

3.Real-Time Features<br/>
To enable WebSocket support (Daphne/ASGI):<br/>
daphne -p 8000 iiuc_connect.asgi:application<br/>
5.	WebSocket (Overview)<br/>
•	Endpoint: ws://127.0.0.1:8000/ws/notifications/?token=<JWT_TOKEN><br/>
•	Purpose: Real-time notifications for users,  admin inactive-user updates<br/>
•	Client Example (JavaScript):<br/>
const ws = new WebSocket(<br/>
  `ws://127.0.0.1:8000/ws/notifications/?token=${token}`<br/>
);<br/>

ws.onmessage = (event) => {<br/>
  const msg = JSON.parse(event.data);<br/>
  console.log("WS Message:", msg);<br/>
};<br/>

6.	 Security Note<br/>
The public repository does not include:<br/>
•	Environment variables or secrets<br/>
•	Database connection strings<br/>
•	Cloud service credentials<br/>
•	Internal architecture or server details<br/>
•	Role restriction implementation<br/>
•	WebSocket authentication details<br/>
All sensitive information is kept private.<br/>
7.	 Purpose<br/>
•	Provides backend API for IIUC Connect system<br/>
•	Supports frontend <br/>
•	Open for community review without exposing internal logic<br/>
•	Maintains clear separation between frontend and backend<br/>
<br/>
8.	 License<br/>
No license applied — all rights reserved by the project owner.<br/>

