# ovatify-backend

## Overview

Ovatify is a music platform designed to offer a unique and personalized experience to music lovers. This project includes a web application, a mobile application, and a robust backend service to manage streaming, user interactions, and data handling. In this repository you will find `backend` of the project.

## Features

- Stream a wide range of songs and albums
- Personalized music recommendations
- User rating system for songs
- Social features, including friend connections
- Real-time song and artist statistics
- Responsive web and mobile interfaces

## Technology Stack

- **Backend:** Django (Python), Firebase Authentication
- **Frontend:** Svelte Kit (Web), Kotlin (Mobile/Android)
- **Database:** PostgreSQL
- **CI/CD:** GitHub Actions, Fly.io
- **Project Management:** Jira, Agile with Scrum

## Prerequisites

- Python 3.8+
- Docker (For containerization and deployment)
- Firebase Account (For Authentication)

## Local Development Setup

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/enesonus/ovatify-backend.git
   ```

2. **Setup:**

   - Install dependencies: `pip install -r requirements.txt`

   ```markdown
      ## Environment Variables

      Ensure to set up the following environment variables:

      - `DB_URL`
      - `DB_USER`
      - `DB_PASSWORD`
      - `FIREBASE_CREDENTIALS`
      ```

   - Run migrations: `python manage.py migrate`

   - Start the Django server: `python manage.py runserver`

## Continuous Integration and Deployment

CI/CD is managed through GitHub Actions and Fly.io. The workflow is configured for automatic deployment upon pushing to the `main` branch or `dev` branch. Both branches has their own Github Actions workflow and server, providing us a shared and seperated mechanism at `dev` branch to test features.

## Contributing

Contributions are welcome! Please read our [Contribution Guidelines](CONTRIBUTING_GUIDELINES.md) for more details. For information about Database tables and Entity Relations of the application you can also have a look at the [DB Plan](DB_PLAN.MD).

---

Ovatify - Bringing the world of music to your fingertips.
