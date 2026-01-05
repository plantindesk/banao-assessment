# HMS Project

A Hospital Management System built with Django and Django REST Framework, featuring Google Calendar integration for appointment scheduling.

## Description

HMS Project is a web-based hospital management system that enables:
- User authentication with role-based access (Doctors and Patients)
- Appointment scheduling with availability management
- Google Calendar integration for calendar sync
- RESTful API for frontend applications
- Serverless deployment option on AWS Lambda

## Tech Stack

- **Backend**: Python 3.12+, Django 6.0
- **API**: Django REST Framework
- **Database**: SQLite (development), compatible with PostgreSQL for production
- **Authentication**: Session + Token authentication
- **Integration**: Google Calendar API, AWS SES (email)
- **Deployment**: Serverless Framework (AWS Lambda)

## Prerequisites

- Python 3.12 or higher
- pip (Python package manager)
- Google Cloud Console account (for Calendar API)
- AWS account (for serverless deployment)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd banao-assessment
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r pyproject.toml
```

4. Set up environment variables:
Create a `.env` file in the root directory:
```env
FRONTEND_URL=http://localhost:5173
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_CALENDAR_SECRET=google_calender_secret.json
```

5. Set up Google Calendar API credentials:
- Create a project in Google Cloud Console
- Enable Google Calendar API
- Download credentials as `google_calender_secret.json` and place in root directory

6. Run migrations:
```bash
python manage.py migrate
```

## Usage

### Development Server

Start the Django development server:
```bash
python manage.py runserver
```

The server will be available at `http://localhost:8000`

### Available Management Commands

```bash
# Create superuser
python manage.py createsuperuser

# Run tests
python manage.py test

# Check system requirements
python manage.py check

# Generate database migrations
python manage.py makemigrations

# Apply database migrations
python manage.py migrate
```

### API Endpoints

- `/admin/` - Django admin interface
- `/api/` - REST API endpoints
- `/oauth2callback/` - Google Calendar OAuth callback

## Project Structure

```
banao-assessment/
├── main/                    # Django project configuration
│   ├── settings.py         # Django settings
│   ├── urls.py            # Root URL configuration
│   ├── wsgi.py            # WSGI application
│   └── asgi.py            # ASGI application
├── users/                  # User management app
│   ├── models.py          # Custom User model (Doctor/Patient)
│   ├── views.py           # User views and Google OAuth
│   ├── serializers.py     # User serialization
│   ├── urls.py            # User URLs
│   ├── permissions.py     # Custom permissions
│   ├── services.py        # User services
│   └── signals.py         # Django signals
├── scheduling/             # Scheduling app
│   ├── models.py          # Availability and Appointment models
│   ├── views.py           # Scheduling views
│   ├── serializers.py     # Scheduling serialization
│   └── urls.py            # Scheduling URLs
├── api/                    # REST API app
│   ├── views.py           # API views
│   └── urls.py            # API URLs
├── handler.py             # Serverless email handler
├── manage.py              # Django management script
├── pyproject.toml         # Project dependencies
├── serverless.yml         # Serverless configuration
└── README.md              # This file
```

## Deployment

### Serverless Deployment (AWS Lambda)

1. Install Serverless Framework:
```bash
npm install -g serverless
```

2. Install plugins:
```bash
npm install serverless-wsgi serverless-python-requirements serverless-offline
```

3. Deploy to AWS:
```bash
serverless deploy --stage dev
```

4. Run locally with Serverless Offline:
```bash
serverless offline
```

### Environment Variables for Production

Configure the following environment variables in your deployment:
- `DJANGO_SETTINGS_MODULE`: main.settings
- `DEV_MODE`: False
- `AWS_SES_REGION`: AWS region for SES
- `SENDER_EMAIL`: Production email sender

## Google Calendar Integration

The application integrates with Google Calendar to:
- Sync doctor availability
- Create calendar events for appointments
- Handle OAuth2 authentication flow

To set up Google Calendar:
1. Create credentials in Google Cloud Console
2. Configure redirect URIs
3. Download and place `google_calender_secret.json` in the project root

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

This project is licensed under the MIT License.
