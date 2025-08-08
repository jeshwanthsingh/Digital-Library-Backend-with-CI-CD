# Agora - SFSU Community Marketplace

CSC 648-848 Spring 2025 - Team #2

## Overview

This application demonstrates the core functionality of the Agora marketplace application. It implements the full stack from browser to database and back using FastAPI for the backend, SQLAlchemy for ORM, and Svelte for the frontend.

## Access URLs

- **Production HTTPS**: [https://team02sfsu.org](https://team02sfsu.org)
- **Production HTTP**: [http://18.223.28.173](http://18.223.28.173) # TODO: Update if IP changes
- **Local Development**: http://localhost:5173 (Svelte dev server) + http://localhost:8000 (API)

## Project Structure

```
application/
├── database/               # Database-related files
│   ├── models.py           # SQLAlchemy ORM models
│   ├── database.py         # Database connection setup
│   └── crud.py             # CRUD operations
├── router/                 # API routes
│   └── search.py           # Search-related endpoints
├── Frontend/               # Frontend files
│   ├── src/                # Svelte source code
│   │   ├── components/     # Svelte components
│   │   └── stores/         # Svelte stores for state management
│   ├── public/             # Static assets served by Vite/Svelte
│   │   └── Images/         # Team member images (if served directly)
│   └── Team-Members/       # Individual team member pages (HTML) - Served via /static/Team-Members
├── static/                 # Static files
│   └── images/             # Images for listings
├── app.py                  # Main FastAPI application
├── schemas.py              # Pydantic schemas for API
└── seed.py                 # Database seeding script
```

## Features Implemented

- **Database Models**: Categories, Listings, and Images with appropriate relationships
- **API Endpoints**:
  - GET `/api/search`: Search for listings by keyword and/or category
  - GET `/api/categories`: Get all categories
  - GET `/api/categories/{id}`: Get a specific category
  - GET `/api/listings/{id}`: Get a specific listing
- **Search Functionality**:
  - Text search across title, description, and keywords
  - Category filtering
  - Result count display
  - Persistent search parameters
- **Frontend**:
  - Modern SPA using Svelte framework
  - Responsive design
  - Client-side routing
  - State management with Svelte stores

## CI/CD with GitHub Actions

We use GitHub Actions for continuous integration and deployment with two main workflows:

1.  **`.github/workflows/super-linter.yml`**: Runs Super-Linter on pushes/PRs to check code quality across Python, CSS, HTML, etc.
2.  **`.github/workflows/deploy.yml`**: Runs on pushes/PRs to `main`. It includes jobs to:
    *   Run backend tests using `pytest`.
    *   Build the Svelte frontend using `npm run build`.
    *   Upload the built frontend as an artifact (`frontend-dist`).
    *   (On push to `main` only) Deploy the application package to the AWS server and execute the `scripts/deploy.sh` script.

See `docs/testing/testing_github_actions.md` for details on how these workflows are triggered and tested.

## How to Run

### Prerequisites

- Python 3.10 or higher
- Node.js 16 or higher
- pip (Python package installer)
- Git

### Running Locally (Non-Docker)

The recommended way to run the application locally uses a simple SQLite database and avoids Docker.

1.  **Follow the setup guide:** See `docs/setup/LOCAL_SETUP.md` for detailed step-by-step instructions on:
    *   Cloning the repository.
    *   Setting up a Python virtual environment.
    *   Installing backend (`pip`) and frontend (`npm`) dependencies.
    *   Seeding the local SQLite database (`python application/seed.py`).
    *   Running the backend server (`uvicorn ...`) in one terminal.
    *   Running the frontend development server (`npm run dev`) in a separate terminal.
2.  **Access the application:** Open `http://localhost:5173` in your browser.

### Production Deployment

The application is deployed on an AWS EC2 instance using:
- Nginx (as configured by `scripts/deploy.sh`) for static file serving and reverse proxy to the backend.
- Systemd (via `agora.service` created by `scripts/deploy.sh`) for managing the backend Python process (run with Gunicorn/Uvicorn).
- AWS RDS (MySQL) for the database.
- GitHub Actions (`deploy.yml`) for automating the deployment process upon merges to `main`.

For deployment details, see:
- `docs/deployment/DEPLOYMENT_GUIDE.md`
- `scripts/deploy.sh` (The actual deployment script run on the server)

## Database Configuration

The application uses:
- **SQLite** (`db/agora.db`) by default for local development.
- **AWS RDS (MySQL)** for the production server environment.

Configuration is handled via environment variables (see `.env.example`) loaded by `application/database/database.py`. See `docs/setup/database_setup.md` for details on configuring the connection for local vs. RDS.

## Frontend Development

The frontend is built with Svelte:

1. Navigate to the frontend directory:
   ```bash
   cd application/Frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Build for production:
   ```bash
   npm run build
   ```

## Architecture

The implementation follows a modern architecture pattern:

- **Backend**: FastAPI with SQLAlchemy ORM
- **Frontend**: Svelte for component-based UI
- **API**: RESTful endpoints for data access
- **Database**: MySQL via AWS RDS (production) or SQLite/MySQL (development)
- **Deployment**: Nginx + Systemd on Ubuntu 20.04
- **CI/CD**: GitHub Actions for automated building and testing

## Next Steps

1. Complete user authentication for buyers and sellers
2. Implement listing creation and management
3. Add messaging between users
4. Create admin dashboard for moderation
5. Enhance search with more filtering options (price, condition, etc.)

## Team Members

- Nathan Delos Reyes - Team Lead
- Jeshwanth Ravindra Singh - Back-end Lead
- Ranbir Atkar - Front-end Lead
- Jose Ramirez - Front-end Lead Helper
- Xiaoxuan Wang - GitHub Master
