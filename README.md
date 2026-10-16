# TaskFlow — Smart Task Management System

TaskFlow is a moderate-level, full-stack web application built for personal task tracking, prioritization, and workflow analytics. It features a modern dark-mode glassmorphic user interface, an asynchronous Python FastAPI backend, a MySQL database managed with SQLAlchemy ORM, and secure stateless JWT authentication.

---

## 🌟 Key Features

- **Responsive Dark Glassmorphic UI**: Ambient glow backdrops, interactive modals, micro-animations, and smooth transitions built using vanilla HTML5, CSS3, and modern JavaScript.
- **Secure Authentication & Authorization**:
  - Secure password hashing with `bcrypt` (12 work factor salt rounds). Plain-text passwords are never stored.
  - Stateless authentication with cryptographically signed JSON Web Tokens (JWT, HS256).
  - Protected API routes and automatic redirection for expired sessions.
- **User Data Isolation & Ownership Protection**:
  - Every task is strictly linked to an authenticated user (`user_id`).
  - Cross-user data isolation enforced on all endpoints (attempts to view, edit, or delete another user's task are rejected with `403 Forbidden`).
- **Interactive Personal Dashboard**:
  - **Live Metrics**: Real-time aggregate counters for Total, Pending, Completed, and Overdue tasks.
  - **Dynamic Task Management**: Create, edit, and delete tasks with confirmation dialogs.
  - **Quick Status Toggle**: Mark tasks done or reopen them with a single click.
  - **Search & Multi-Filters**: Instant keyword search across titles and descriptions, plus dropdown filters for status (`pending`, `in_progress`, `completed`) and priority (`low`, `medium`, `high`).
  - **Overdue Detection**: Automatically detects and highlights overdue tasks based on due date timestamps.
- **Interactive API Documentation**: Auto-generated interactive Swagger UI and ReDoc endpoints for rapid testing and API exploration.

---

## 🛠️ Technology Stack

| Layer | Technology | Details |
| :--- | :--- | :--- |
| **Frontend** | Vanilla HTML5, CSS3, JavaScript | Pure CSS Glassmorphism, Responsive Grid, ES6+ Fetch API |
| **Backend** | Python 3.12+, FastAPI | Asynchronous RESTful API framework |
| **Server** | Uvicorn (Standard) | High-performance ASGI web server |
| **Database** | MySQL 8.0+ | Relational database with Foreign Key constraints & cascade delete |
| **ORM** | SQLAlchemy 2.0+ | Object-Relational Mapping & connection pooling with PyMySQL |
| **Security** | PyJWT, Bcrypt | Cryptographic JWT signing and salted password hashing |
| **Validation** | Pydantic v2 & Pydantic-Settings | Request/response data validation and `.env` parsing |
| **Testing** | Pytest, HTTPX | Automated unit, integration, and security test suite |

---

## 📁 Project Directory Structure

```text
task/
├── .gitignore                     # Git ignore rules for venv, cache, and .env
├── README.md                      # Comprehensive project documentation
├── venv/                          # Python virtual environment (isolated packages)
├── backend/
│   ├── .env                       # Local secrets & credentials (never committed to git)
│   ├── .env.example               # Template for environment configuration
│   ├── requirements.txt           # Python package dependencies
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI entry point, CORS, table creation & routing
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py          # Pydantic BaseSettings loading from .env
│   │   │   └── security.py        # Bcrypt hashing & JWT encode/decode functions
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   └── session.py         # SQLAlchemy engine, SessionLocal & get_db dependency
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py            # SQLAlchemy User model (`users` table)
│   │   │   └── task.py            # SQLAlchemy Task model (`tasks` table)
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── user.py            # Pydantic schemas for User registration, login, and response
│   │   │   └── task.py            # Pydantic schemas for Task CRUD, metrics, and response
│   │   └── api/
│   │       ├── __init__.py
│   │       ├── deps.py            # Authentication dependency (get_current_user)
│   │       ├── auth.py            # /api/v1/auth (register, login, me)
│   │       └── tasks.py           # /api/v1/tasks (CRUD, metrics, search, filters)
│   └── tests/
│       ├── __init__.py
│       └── test_api.py            # Comprehensive Pytest automated test suite
└── frontend/
    ├── index.html                 # Registration page
    ├── login.html                 # Sign-in page
    ├── dashboard.html             # Main Task Management Dashboard
    ├── css/
    │   └── style.css              # Dark mode glassmorphic stylesheet
    └── js/
        ├── auth.js                # Centralized JWT storage & authenticated fetch wrapper
        ├── register.js            # Registration form validation & API call
        ├── login.js               # Login form submission & session handling
        └── dashboard.js           # Dashboard metrics, task CRUD, search, filter, and modals
```

---

## ⚙️ Environment Configuration

Configuration values are loaded using `pydantic-settings` from `backend/.env`.

A template is provided in `backend/.env.example`:

```env
PROJECT_NAME="TaskFlow - Smart Task Management System"
ENVIRONMENT="development"
HOST="127.0.0.1"
PORT=8000

# Database Configuration (MySQL)
DB_HOST="localhost"
DB_PORT=3306
DB_USER="root"
DB_PASSWORD="your_mysql_password"
DB_NAME="taskflow_db"

# JWT Security Settings
# Generate a secure key using: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY="your_super_secret_jwt_key_keep_it_safe"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

> [!IMPORTANT]
> Never commit `backend/.env` to Git. Keep `backend/.env` in `.gitignore` to protect your database credentials and JWT secret.

---

## 🚀 Local Setup & Installation (Windows 11 PowerShell)

### Prerequisites
- **Python 3.12+** installed on Windows.
- **MySQL Server 8.0+** running locally (service `MySQL80` on default port `3306`).

### Step 1: Open PowerShell and Navigate to the Project Folder
```powershell
cd c:\Users\katch\OneDrive\Desktop\projects\task
```

### Step 2: Create and Activate the Virtual Environment
```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If PowerShell displays an execution policy error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` once).*

### Step 3: Install Backend Dependencies
```powershell
pip install -r backend/requirements.txt
```

### Step 4: Configure the MySQL Database
Ensure your MySQL server is running, and configure your credentials in `backend/.env`:
```powershell
# Copy the example environment file if .env does not already exist:
Copy-Item backend\.env.example backend\.env
```
Open `backend/.env` in your editor and update `DB_PASSWORD` with your MySQL root password.

*(Optional)* You can manually create the database in MySQL, or let the server create the tables automatically:
```sql
CREATE DATABASE IF NOT EXISTS taskflow_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 🖥️ Running the Application

### 1. Start the FastAPI Development Server
From the root `task` folder with your virtual environment activated:
```powershell
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

When started, FastAPI automatically initializes the database tables (`users` and `tasks`) in MySQL.

### 2. Access the Application in Your Browser
- **Homepage & Registration**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/) *(or `/index.html`, `/register`)*
- **Sign In / Login**: [http://127.0.0.1:8000/login.html](http://127.0.0.1:8000/login.html) *(or `/login`)*
- **Personal Dashboard**: [http://127.0.0.1:8000/dashboard.html](http://127.0.0.1:8000/dashboard.html) *(or `/dashboard`)*
- **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **API Status & Metadata**: [http://127.0.0.1:8000/api](http://127.0.0.1:8000/api)

---

## 📡 REST API Endpoints Reference

All endpoints are versioned under `/api/v1`.

### 1. Authentication Endpoints (`/api/v1/auth`)

| Method | Endpoint | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | No | Validates name/email/password, hashes password with bcrypt, and creates user in MySQL. |
| `POST` | `/api/v1/auth/login` | No | Verifies email and password, returns signed JWT access token. |
| `GET` | `/api/v1/auth/me` | **Bearer Token** | Returns profile of currently authenticated user. |

#### Sample Registration Request (`POST /api/v1/auth/register`)
```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "password": "SecurePassword123!"
}
```

#### Sample Login Response (`POST /api/v1/auth/login`)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in_minutes": 60,
  "user": {
    "id": 1,
    "name": "Jane Doe",
    "email": "jane@example.com",
    "created_at": "2026-10-14T18:00:00"
  }
}
```

---

### 2. Task Management Endpoints (`/api/v1/tasks`)

All task endpoints require an `Authorization: Bearer <token>` header.

| Method | Endpoint | Query Parameters | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/tasks/metrics` | None | Returns total, pending, in-progress, completed, and overdue task counts for current user. |
| `GET` | `/api/v1/tasks/` | `search`, `status`, `priority` | Lists tasks owned by current user with optional filtering and keyword search. |
| `POST` | `/api/v1/tasks/` | None | Creates a new task bound to the authenticated user. |
| `GET` | `/api/v1/tasks/{id}` | None | Retrieves a specific task. Returns `403 Forbidden` if owned by another user. |
| `PUT` | `/api/v1/tasks/{id}` | None | Updates task fields. Enforces ownership check (`403 Forbidden` for non-owners). |
| `DELETE` | `/api/v1/tasks/{id}` | None | Permanently deletes a task. Enforces ownership check (`403 Forbidden` for non-owners). |

#### Sample Create Task Request (`POST /api/v1/tasks/`)
```json
{
  "title": "Complete Database Architecture Review",
  "description": "Inspect indexing and foreign key constraints on MySQL tables",
  "priority": "high",
  "status": "pending",
  "due_date": "2026-10-25T18:00:00Z"
}
```

#### Sample Task Metrics Response (`GET /api/v1/tasks/metrics`)
```json
{
  "total": 4,
  "pending": 2,
  "in_progress": 1,
  "completed": 1,
  "overdue": 1
}
```

---

## 🧪 Running the Automated Test Suite

TaskFlow includes an automated Pytest test suite covering authentication, database persistence, token validation, task CRUD, search/filtering, and cross-user ownership security checks.

To run the test suite:
```powershell
cd c:\Users\katch\OneDrive\Desktop\projects\task
.\venv\Scripts\Activate.ps1
$env:PYTHONPATH="backend"
pytest backend\tests\test_api.py -v
```

### Verified Test Cases:
- `test_root_endpoint`: Health and sanity check.
- `test_user_registration_success`: Account creation & password hashing verification.
- `test_user_registration_duplicate_email`: Rejection of duplicate emails (case-insensitive).
- `test_user_registration_invalid_inputs`: Validation of email format, minimum password length, and non-empty name.
- `test_login_success`: Valid login and JWT generation.
- `test_login_invalid_password`: Rejection of incorrect credentials with `401 Unauthorized`.
- `test_protected_me_endpoint_with_valid_token`: Profile retrieval via Bearer token.
- `test_protected_me_endpoint_expired_token`: Rejection of expired tokens with `401`.
- `test_task_crud_and_ownership`: Full CRUD lifecycle and **403 Forbidden** security check blocking User B from viewing, updating, or deleting User A's tasks.
- `test_task_metrics_and_search_filters`: Verification of overdue detection, search keywords, and status/priority filters.
- `test_frontend_static_assets`: HTTP 200 delivery of all frontend HTML, CSS, and JS files.

---

## 📦 Publishing to GitHub

To publish TaskFlow as a new repository on your GitHub account:

### 1. Initialize Git in the Project Root
```powershell
cd c:\Users\katch\OneDrive\Desktop\projects\task
git init -b main
```

### 2. Verify `.gitignore` is Active
Ensure `.env` and `venv` are ignored before adding files:
```powershell
git status
```
*(Confirm that neither `venv/` nor `backend/.env` are listed under untracked files).*

### 3. Stage and Commit Your Code
```powershell
git add .
git commit -m "feat: initial TaskFlow full-stack application release"
```

### 4. Link to GitHub and Push
Create a new empty repository on [GitHub](https://github.com/new) named `taskflow`, then run:
```powershell
git remote add origin https://github.com/<your-username>/taskflow.git
git branch -M main
git push -u origin main
```

---

## 📄 License
This project is licensed under the MIT License.
