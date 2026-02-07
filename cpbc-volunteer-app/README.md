# CPBC Volunteer App

A mobile-friendly web application for Cross Point Baptist Church volunteer signup and management.

## Overview

This application allows church members to sign up for volunteer opportunities via a QR code. It includes:

- **Public Volunteer Form**: Mobile-friendly signup form accessed via QR code
- **Admin Dashboard**: Protected dashboard for church staff to manage volunteers

## Tech Stack

- **Frontend**: React + Vite
- **Backend**: Python with FastAPI
- **Database**: PostgreSQL
- **Email**: AWS SES for admin notifications
- **Authentication**: JWT tokens for admin access

## Project Structure

```
cpbc-volunteer-app/
├── frontend/           # React + Vite application
│   ├── src/
│   │   ├── components/ # Reusable UI components
│   │   ├── pages/      # Page components
│   │   └── services/   # API client functions
│   └── ...
├── backend/
│   ├── app/
│   │   ├── routes/     # API endpoints
│   │   ├── services/   # Business logic (email, etc.)
│   │   ├── auth/       # JWT authentication
│   │   ├── models.py   # SQLAlchemy models
│   │   └── schemas.py  # Pydantic schemas
│   └── alembic/        # Database migrations
└── ...
```

## Setup Instructions

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy the environment example and configure:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and other settings
   ```

5. Set up the database:
   ```bash
   # Create the PostgreSQL database
   createdb cpbc_volunteers

   # Run migrations (when available)
   alembic upgrade head
   ```

6. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

   The app will be available at `http://localhost:5173`

## API Endpoints

### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/volunteers` | Submit a volunteer signup |
| GET | `/api/ministry-areas` | Get list of ministry categories |

### Admin Endpoints (JWT Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/admin/login` | Admin login, returns JWT token |
| GET | `/api/admin/volunteers` | List all volunteers |
| GET | `/api/admin/reports/export` | Export volunteers as CSV |

### Query Parameters for `/api/admin/volunteers`

- `ministry_area`: Filter by specific ministry area
- `category`: Filter by ministry category
- `sort_by`: Sort results (`name`, `date`, `ministry`)

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing secret |
| `JWT_ALGORITHM` | JWT algorithm (default: HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time |
| `AWS_ACCESS_KEY_ID` | AWS credentials for SES |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials for SES |
| `AWS_REGION` | AWS region for SES |
| `SES_SENDER_EMAIL` | Email sender address |
| `ADMIN_NOTIFICATION_EMAILS` | Comma-separated admin emails |
| `CORS_ORIGINS` | Allowed CORS origins |

## Creating an Admin User

Use the Python shell to create an admin user:

```python
from app.database import SessionLocal
from app.auth.auth import create_admin_user

db = SessionLocal()
create_admin_user(db, "admin@crosspointbc.org", "secure-password", "Admin Name")
db.close()
```

## Ministry Categories

The following ministry areas are available for volunteer signup:

- **Children's Ministry**: Childcare and/or Teaching, VBS
- **Hospitality**: Greeters, Make Contact with Visitors, Kitchen Cleanup
- **Media**: Sound, etc., Social Media
- **Missions**: Guatemala Mission Trip, El Salvador Mission Trip, 3:18 Church (Third Saturday), 5 Loaves 2 Fish (Thursday before 1st Saturday)
- **Member Care**: Meal Trains for members in need, Help for Elderly/Widows
- **Community Outreach**: Trunk or Treat, Easter Event, New Outreach Programs
- **Building/Grounds**: Maintenance, Security

## Development Notes

- The backend uses proper logging (no `print()` statements)
- Email notifications fail gracefully - signups are saved even if email fails
- CORS is configured to allow frontend development server requests
- Database tables are auto-created on startup in development mode

## License

Private - Cross Point Baptist Church
