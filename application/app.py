import os
from pathlib import Path # For robust path manipulation
import logging # For better logging

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
# from fastapi.templating import Jinja2Templates # Only if you still use Jinja2 for server-side templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile, File

# Import database components
from application.database.database import Base, engine 

# Import routers
from application.router import search
from application.router import auth
from application.router import messaging
from application.router import listings as listings_router
from application.router import admin # Import the new admin router

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: [%(name)s] %(message)s')
logger = logging.getLogger(__name__)

# --- Create tables in the database (if they don't exist) ---
# Note: Your seed.py also handles table creation (and dropping).
# For production, Alembic or another migration tool is recommended over create_all in app startup.
try:
    logger.info("Attempting to create database tables if they don't exist (Base.metadata.create_all)...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables checked/created successfully.")
except Exception as e:
    logger.error(f"Error during Base.metadata.create_all: {e}")
    # Depending on the error, you might want to raise it or handle it.

# --- Create FastAPI app ---
app = FastAPI(
    title="Agora API",
    description="SFSU Community Marketplace API",
    version="0.1.0"
)

# --- Add CORS middleware ---
# Adjust allow_origins for your production frontend URL
origins = [
    "http://localhost:5173", # For local frontend development
    "https://team02sfsu.org",
    "https://3.138.184.33"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Define Project Root and Static/Distribution Directories ---
# Assuming this app.py file is in project_root/application/app.py
PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent
logger.info(f"PROJECT_ROOT_DIR resolved to: {PROJECT_ROOT_DIR}")

# For backend-specific static files (e.g., user uploads, images managed by seed.py)
# This points to project_root/application/static/
BACKEND_STATIC_DIR = PROJECT_ROOT_DIR / "static"
logger.info(f"BACKEND_STATIC_DIR resolved to: {BACKEND_STATIC_DIR}")

# For built frontend assets deployed by deploy.sh
# This points to project_root/frontend-dist/
FRONTEND_DIST_DIR = PROJECT_ROOT_DIR / "frontend-dist"
logger.info(f"FRONTEND_DIST_DIR resolved to: {FRONTEND_DIST_DIR}")


# --- Create static directories if they don't exist (for backend static) ---
try:
    # For images uploaded via listings, etc.
    (BACKEND_STATIC_DIR / "images" / "listings").mkdir(parents=True, exist_ok=True)
    # For team member images if served from backend static
    (BACKEND_STATIC_DIR / "Team-Members").mkdir(parents=True, exist_ok=True)
    logger.info("Ensured backend static directories exist.")
except Exception as e:
    logger.error(f"Error creating backend static directories: {e}")


# --- Mount Backend Static Directories ---
# Serves files from project_root/application/static/
if BACKEND_STATIC_DIR.exists() and BACKEND_STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=BACKEND_STATIC_DIR), name="static_backend")
    logger.info(f"Mounted backend /static from: {BACKEND_STATIC_DIR}")
    
    # Example: if you have Team-Members HTMLs/images inside application/static/Team-Members
    team_members_static_path = BACKEND_STATIC_DIR / "Team-Members"
    if team_members_static_path.exists() and team_members_static_path.is_dir():
        app.mount("/Team-Members", StaticFiles(directory=team_members_static_path), name="team_members_static")
        logger.info(f"Mounted /Team-Members from: {team_members_static_path}")
    else:
        logger.warning(f"Directory for /Team-Members not found at {team_members_static_path}")
else:
    logger.warning(f"Backend static directory not found at {BACKEND_STATIC_DIR}. /static will not be served from backend.")


# --- API Endpoints (Health Check, Team Info) ---
# Define these before including general API routers
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

@app.get("/api/team")
async def team_info():
    return {
        "team": "Team 02",
        "members": [
            {"name": "Jeshwanth Ravindra Singh", "role": "Back-end Lead"},
            {"name": "Ranbir Atkar", "role": "Front-end Lead"},
            {"name": "Jose Ramirez", "role": "Front-end Lead Helper"},
            {"name": "Nathan Delos Reyes", "role": "Team Lead"},
            {"name": "Xiaoxuan Wang", "role": "GitHub Master"}
        ]
    }

# --- Include API Routers ---
app.include_router(auth.router, prefix="/api", tags=["Authentication"]) # Consistent tagging
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(messaging.router, prefix="/api", tags=["Messaging"])
app.include_router(listings_router.router, prefix="/api", tags=["Listings & Reviews"]) # Combined tag for clarity
app.include_router(admin.router, prefix="/api", tags=["Admin"]) # Include the new admin router


# --- Mount Frontend Static Assets ---
# Serves assets from project_root/frontend-dist/assets/
frontend_assets_dir = FRONTEND_DIST_DIR / "assets"
if frontend_assets_dir.exists() and frontend_assets_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=frontend_assets_dir), name="dist_assets")
    logger.info(f"Mounted frontend /assets from directory: {frontend_assets_dir}")
else:
    logger.warning(f"Frontend assets directory not found at {frontend_assets_dir}. Frontend /assets may not be served correctly.")

# --- SPA Fallback Route (Serves index.html for any other GET request) ---
# This should be one of the LAST routes defined.
# It allows client-side routing for your SPA to handle paths like /login, /products/123, etc.
if FRONTEND_DIST_DIR.exists() and FRONTEND_DIST_DIR.is_dir():
    @app.get("/{full_path:path}", response_class=FileResponse, include_in_schema=False)
    async def serve_spa_host(request: Request, full_path: str):
        index_html_path = FRONTEND_DIST_DIR / "index.html"
        if not index_html_path.exists():
            logger.error(f"SPA index.html not found at {index_html_path} for path: /{full_path}")
            raise HTTPException(status_code=500, detail="Frontend build index.html not found. Deployment issue.")
        
        # Prevent API calls from being caught by SPA fallback
        # This check might be redundant if API routers are correctly prefixed and Nginx handles /api separately
        if full_path.startswith("api/") or full_path.startswith("static/") or full_path.startswith("assets/") or full_path.startswith("Team-Members/"):
             logger.warning(f"Path '{full_path}' looks like an API or static asset call but was caught by SPA fallback. Check route ordering or Nginx config.")
             # For truly unhandled API-like paths, you might want a 404 from an API perspective
             # For now, we'll let it fall through to index.html if not caught by other mounts/routers,
             # but ideally, Nginx should route /api to backend and / to frontend static.
             # If Nginx is properly configured, this FastAPI SPA fallback mainly handles client-side routes.

        logger.info(f"Serving SPA index.html for path: /{full_path}")
        return FileResponse(index_html_path)
    logger.info(f"SPA fallback configured to serve index.html from: {FRONTEND_DIST_DIR}")
else:
    logger.warning(f"Frontend distribution directory not found at {FRONTEND_DIST_DIR}. SPA fallback route not configured.")

# Note on Jinja2Templates:
# If you are NOT using Jinja2 for any server-side HTML rendering by FastAPI
# (i.e., your frontend is a pure SPA served as static files),
# then the `templates = Jinja2Templates(directory=FRONTEND_DIR)` line
# and its import can be removed. FRONTEND_DIR pointed to application/Frontend.
# If your index.html is in FRONTEND_DIST_DIR and is pure static, Jinja2 is not needed for it.
