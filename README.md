# ARES
AI Disaster Response Platform.

1.1 Purpose

ARES is an AI-assisted emergency dispatch and decision support platform designed to help emergency responders make faster and more informed rescue decisions during natural disasters.

The platform transforms emergency hotline calls into structured rescue tickets, prioritizes incidents based on victim condition and environmental factors, and recommends appropriate rescue teams and evacuation shelters.

1.2 Goals

The system aims to:

- Reduce emergency response time.
- Help responders prioritize victims.
- Prevent evacuation center overcrowding.
- Improve situational awareness.
- Provide AI-assisted recommendations while keeping humans in control.

1.3 Scope (Version 1)

Version 1 focuses on flood-related emergencies.

Features include:

Emergency ticket creation
Victim information recording
Rescue team assignment
Shelter management
Road closure monitoring
AI priority scoring
Incident tracking

2. Users
   
DISPATCHER

Responsibilities

- Receive emergency calls
- Assess caller
- Create rescue ticket
- Update ticket
- Forward incident

Permissions

- Create Ticket
- Edit Ticket
- View Active Incidents

INCIDENT COMMANDER

Responsibilities

- Monitor incidents
- Allocate rescue teams
- Review AI recommendations
- Track shelters

Permissions

- View Dashboard
- Assign Teams
- Override AI Recommendation
- Rescue Team

Responsibilities

- Accept assignments
- Navigate to victim
- Rescue victim
- Update rescue status

Permissions

- View Assigned Tickets
- Update Rescue Progress
- Close Ticket
- Administrator

Responsibilities

- Manage system users
- Manage shelters
- Configure AI settings

Permissions

- Full Access

3. System Workflow

Citizen

↓

Emergency Hotline

↓

Dispatcher

↓

ARES Ticket

↓

AI Decision Engine

↓

Incident Commander

↓

Rescue Team

↓

Victim Rescued

↓

Shelter

↓

Incident Closed

4. Functional Requirements

4.1 Login

The system shall allow authenticated users to log in using role-based accounts.

4.2 Emergency Ticket

The dispatcher shall be able to create an emergency ticket containing:

- Caller Name
- Contact Number
- GPS Location
- Barangay
- Number of Victims
- Medical Conditions
- Water Level
- Food Supply
- Notes

4.3 Shelter Management

The system shall display:

Capacity
- Current Occupancy
- Remaining Capacity
- Flood Risk
- Accessibility

4.4 Rescue Team Management

The system shall:

- Display available rescue teams
- Display current assignments
- Show estimated arrival time

4.5 Dashboard

The dashboard shall display:

- Active Incidents
- Flood Alerts
- Shelter Status
- Road Closures
- Weather Alerts
- AI Recommendations

5. Non-Functional Requirements

5.1 Performance

- Ticket creation under 2 seconds
- Dashboard refresh under 5 seconds

5.2 Availability

- 99% uptime

5.3 Security

- User authentication
- Role-based authorization
- Encrypted passwords

5.4 Usability

- Simple interface
- Responsive dashboard

S.5 Scalability

- Support multiple municipalities

7. Database
   
User

↓

creates

↓

Ticket

↓

assigned to

↓

Rescue Team

↓

rescues

↓

Victim

↓

transported to

↓

Shelter

7. Ticket Lifecycle

New

↓

Assessment

↓

AI Priority Assigned

↓

Commander Review

↓

Assigned

↓

Accepted

↓

En Route

↓

On Scene

↓

Victim Rescued

↓

Shelter Assigned

↓

Closed

8. AI Decision Engine

Inputs
- Victim Condition
- Flood Risk
- Road Accessibility
- Shelter Capacity
- Rescue Team Availability

Output
- Priority Score
- Recommended Rescue Team
- Recommended Shelter
- Recommended Route
- Confidence Score

9. Future Features

Version 2

- Live GPS Tracking
- Mobile App
- AI Chat Assistant
- Drone Integration
- SMS Notification

Version 3

- Computer Vision
- Flood Prediction
- Satellite Analysis
- AI Agents
- Automatic Resource Allocation

10. Technology Stack

Frontend

- React
- TypeScript
- Tailwind CSS

Backend

- FastAPI
- Python

Database

- PostgreSQL

Maps

- Leaflet

AI

- OpenAI
- LangGraph
- ChromaDB

Deployment

- Docker
- Azure
