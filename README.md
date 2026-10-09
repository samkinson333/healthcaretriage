# SmartTriage AI

**OPCODE IMPACT 2026 | Hackathon Submission**

**Team Name:** Pazhampori  
**Team ID:** OPC009  
**Team Lead:** Ajisha  
**Team Members:** Ajisha, Anjo, Jimson, Sam

## 1. Problem Statement

Emergency departments can face overcrowding and delays in assessing patients. First-come-first-served queues may fail to prioritize patients whose symptoms or vital signs indicate greater urgency. SmartTriage AI addresses this problem through transparent triage rules, urgency-based queue prioritization, waiting-time alerts, and clinician supervision.

## 2. Solution Title

SmartTriage AI — Explainable Emergency Queue and Triage Decision Support

## 3. Solution Description

SmartTriage AI is a clinician-supervised decision-support prototype that evaluates patient intake information and vital signs using transparent, rules-based logic. It generates provisional urgency recommendations, explains the rules that triggered them, and prioritizes waiting patients. The system supports clinician overrides with mandatory reasons and maintains an audit trail of important decisions. Queue simulations compare different scheduling strategies and demonstrate waiting-time trade-offs. Future enhancements include OP registration and integration with compatible health-screening kiosks.

## 4. Architecture Diagram

![Architecture Diagram](docs/architecture.png)

**Workflow:** Patient Intake → Vital-Sign Collection → Input Validation → Deterministic Triage Rules Engine → Urgency Recommendation → Priority Queue and Waiting-Time Alerts → Clinician Review and Override → Audit Trail.

Future development may connect OP registration and screening measurements from compatible devices to a unique patient visit.

## 5. Technology Stack

- **Frontend:** React
- **Backend:** Django
- **Database:** SQLite
- **Other Technologies:** Python, deterministic triage rules, NEWS2-based scoring reference, queue scheduling, simulation, audit logging, and automated testing.

## 6. Quick Start Guide

**Prerequisites:** Git, Node.js, npm, Python, and a modern web browser.

**Repository:** https://github.com/samkinson333/healthcaretriage.git

**Installation & Execution:**

```bash
git clone https://github.com/samkinson333/healthcaretriage.git
```

Install the React frontend and Django backend dependencies according to the repository README. Start the frontend using its configured development command. For Django, install the required Python dependencies, apply database migrations, and run the development server.

```bash
python manage.py migrate
python manage.py runserver
```

Use the actual repository configuration and README to confirm the correct startup commands.

## 7. Output Screenshots

![Output Screenshot](docs/output.png)

**Output Description:** The prototype demonstrates patient intake, provisional urgency recommendations, rule explanations, an urgency-based queue, clinician overrides, feedback, audit history, and queue-policy simulation.

## 8. Future Scope

- Improve triage rules and obtain qualified clinician review.
- Implement and verify persistent storage, authentication, and role-based access control.
- Add OP registration and unique visit/ticket identification.
- Integrate compatible devices for blood pressure, SpO₂, pulse, temperature, and optional blood glucose.
- Develop Malayalam and English intake support.
- Conduct appropriate independent clinical, privacy, security, and regulatory reviews.

## 9. Team Contributions

| Member Name | Contribution |
|---|---|
| Ajisha | Team Lead and team coordination |
| Anjo | Project development and implementation |
| Jimson | Project development and implementation |
| Sam | Project development and implementation |

## 10. Tools Used

| Tool / Platform | Purpose / Why Used |
|---|---|
| React | Frontend user-interface development |
| Django | Backend application and API development |
| SQLite | Database management |
| Python | Backend logic and triage rules |
| Git / GitHub | Source control and collaboration |
| Web Browser | Running and demonstrating the prototype |
| ChatGPT / AI Tool | Assistance with project planning, documentation, and development |