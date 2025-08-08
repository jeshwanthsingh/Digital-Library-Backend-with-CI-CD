# Agora Repository Structure Guide

This document outlines the repository structure for the Agora SFSU Community Marketplace project.

## Directory Structure (Post-Cleanup)

```
csc648-fa25-0104-team02/
├── .github/                    # GitHub Actions workflows
├── application/                # Main application source code
│   ├── .gitignore              # Application specific ignores (if any)
│   ├── app.py                  # FastAPI application entry point
│   ├── database/               # Database models, CRUD operations, connection
│   ├── Frontend/               # Frontend code (Svelte)
│   │   ├── dist/               # Built frontend artifacts (ignored by git)
│   │   ├── public/             # Static assets copied by Vite build (e.g., Images)
│   │   ├── src/                # Svelte source files (components, stores)
│   │   ├── index.html          # Svelte entry HTML
│   │   ├── package.json        # Frontend dependencies
│   │   ├── package-lock.json   # Frontend dependency lock file
│   │   ├── svelte.config.js    # Svelte configuration
│   │   └── vite.config.mjs     # Vite configuration (includes dev server proxy)
│   ├── gunicorn_conf.py        # Gunicorn configuration (used by deploy.sh on server)
│   ├── router/                 # API route definitions
│   ├── schemas.py              # Pydantic schemas for API validation
│   ├── seed.py                 # Database seeding script (run via python -m application.seed)
│   └── static/                 # Static files served directly by the backend (FastAPI)
│       ├── images/             # Image storage (e.g., uploaded listing images)
│       │   └── listings/       # Specific directory for listing images
│       └── Team-Members/       # Static HTML team member pages (served at /Team-Members)
├── db/                         # Local database files (e.g., agora.db for SQLite - ignored by git)
├── docs/                       # Project documentation
│   ├── deployment/             # Deployment guides
│   ├── setup/                  # Setup documentation
│   ├── testing/                # Testing documentation
│   └── milestones/             # Project milestones documentation (if any)
├── logs/                       # Log files (ignored by git)
├── Milestones/                 # Root Milestones folder (contains actual milestone documents)
├── scripts/                    # Utility and operational scripts
│   ├── build_frontend.sh       # Builds the Svelte frontend (used by deploy.yml)
│   ├── deploy.sh               # AWS deployment script (run on server by deploy.yml)
│   ├── js/                     # JavaScript utility scripts (if any)
│   ├── setup-aws.sh            # AWS setup script (purpose?)
│   ├── start_local.sh          # Starts local backend dev server (non-Docker) + seeds DB
│   └── transfer_to_server.sh   # Helper for AWS deployment? (Likely unused if deploy.yml uses scp-action)
└── tests/                      # Automated tests
    ├── api/                    # API tests (using TestClient)
    └── data/                   # Test data fixtures (if any)
```

*Note: Directories like `myenv/`, `node_modules/`, `.vscode/`, `__pycache__/` are typically present locally but ignored by git.*

## Key Files

### Root Files
- `.env.example` - Template for environment variables
- `.gitignore` - Controls which files are excluded from version control
- `LICENSE` - Project license information
- `Makefile` - Build automation
- `README.md` - Project overview and instructions
- `requirements.txt` - Python dependencies

### Configuration Files
# Configuration is primarily handled by .env at the root.

### Scripts
- `scripts/start_local.sh`     # Starts local backend dev server (FastAPI/Uvicorn) & seeds DB.
- `scripts/build_frontend.sh`  # Builds the Svelte frontend (`dist` folder) - used by deploy.yml.
- `application/seed.py`        # Seeds the database (run via `python application/seed.py`).
- `scripts/deploy.sh`          # AWS deployment script (run on server by deploy.yml).
- `scripts/setup-aws.sh`       # AWS setup script (purpose needs clarification).
- `scripts/transfer_to_server.sh` # Likely unused if deploy.yml uses scp-action.

### Documentation
- `docs/deployment/DEPLOYMENT_GUIDE.md` - Guide for deploying the application.
- `docs/setup/database_setup.md`    # Database setup instructions (SQLite/RDS).
- `docs/setup/LOCAL_SETUP.md`       # Local development setup guide (non-Docker).
- `docs/setup/SERVER_SETUP.md`      # Server configuration guide.
- `docs/testing/testing_github_actions.md` # Guide for testing GitHub Actions.
- `docs/REPOSITORY_STRUCTURE.md`    # This document.

## Migration Notes

This structure represents a significant cleanup and reorganization:

1. Removed redundant `application/backend/` directory.
2. Consolidated backend code (FastAPI app, routers, schemas, db logic) directly under `application/`.
3. Consolidated Svelte frontend code under `application/Frontend/`, removing nested `Frontend` directory.
4. Standardized frontend static asset location to `application/Frontend/public/`.
5. Moved static HTML pages (`Team-Members`) to `application/static/`.
6. Removed unused/legacy directories (`legacy`, `assets`, `credentials`, `docker`, `config/docker`, `config/nginx`, `application/fastapi_app`).
7. Removed redundant/unused scripts.
8. Kept root `Milestones/` directory as requested.

## Best Practices

When working with this repository:

1. **Environment Variables**: Never commit sensitive information. Use `.env.example` as a template.
2. **Dependencies**: Use `requirements.txt` for Python dependencies and `package.json` for JavaScript.
3. **Testing**: Add tests in the `tests/` directory following the same structure as the code being tested.
4. **Documentation**: Update documentation when making significant changes.
5. **Branch Management**: Use feature branches and pull requests for development.
6. **Logs**: Don't commit log files; they should be added to .gitignore.
7. **Database Files**: Local database files should not be committed to the repository.
