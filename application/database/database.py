import os
import logging # Import the logging module
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- Configure Logging ---
# Basic configuration for logging. You can customize this further.
logging.basicConfig(level=logging.INFO, format='%(levelname)s: [%(name)s] %(message)s')
logger = logging.getLogger(__name__) # Get a logger for this module

# --- Load .env file from the project root ---
# This path assumes database.py is in application/database/
# and .env is at the project root (e.g., project_root/.env)
env_path = Path(__file__).resolve().parent.parent.parent / '.env'

if env_path.exists():
    logger.info(f"Attempting to load environment variables from: {env_path}")
    load_dotenv(dotenv_path=env_path)
else:
    logger.warning(f".env file not found at {env_path}. Environment variables must be set externally if not found.")

# --- Determine Database Type ---
# Default to 'sqlite' if DB_TYPE is unset, empty, or invalid.
raw_db_type = os.getenv("DB_TYPE")
if not raw_db_type or raw_db_type.strip().lower() not in ['mysql', 'sqlite']:
    DB_TYPE = "sqlite"
    logger.info("DB_TYPE not found or invalid in .env, defaulting to 'sqlite'.")
else:
    DB_TYPE = raw_db_type.strip().lower()
logger.info(f"DB_TYPE resolved to: '{DB_TYPE}'")

SQLALCHEMY_DATABASE_URL = None

# --- Configure Database URL ---
if DB_TYPE == "mysql":
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT_STR = os.getenv("DB_PORT") # Get port as string first
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")

    if not all([DB_HOST, DB_USER, DB_PASSWORD, DB_NAME]):
        logger.critical("Missing required MySQL environment variables (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME). Cannot configure MySQL.")
        raise ValueError("Missing required MySQL environment variables. Please check your .env file.")

    # Construct MySQL URL, handling optional and validating port
    db_url_display = f"mysql+pymysql://{DB_USER}:********@{DB_HOST}" # For logging, hide password

    if DB_PORT_STR and DB_PORT_STR.strip().lower() not in ["", "none"]:
        try:
            DB_PORT = int(DB_PORT_STR) # Validate port is integer
            SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            db_url_display += f":{DB_PORT}/{DB_NAME}"
        except ValueError:
            logger.critical(f"Invalid DB_PORT: '{DB_PORT_STR}'. Must be an integer.")
            raise ValueError(f"Invalid DB_PORT: '{DB_PORT_STR}'. Must be an integer.")
    else:
        # If DB_PORT is None, empty, or "none", omit it (MySQL default port 3306 will be used by the driver)
        SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
        db_url_display += f"/{DB_NAME} (using default port)"
        logger.info(f"DB_PORT not specified or explicitly set to none in .env, using default MySQL port for host {DB_HOST}.")
    
    logger.info(f"Using MySQL database: {db_url_display}")

elif DB_TYPE == "sqlite":
    # Default path relative to project root (where .env is)
    default_sqlite_path_str = "db/agora.db" 
    DB_SQLITE_PATH_STR = os.getenv("DB_SQLITE_PATH", default_sqlite_path_str)
    
    project_root = env_path.parent # The directory containing .env
    sqlite_db_file = (project_root / DB_SQLITE_PATH_STR).resolve()

    # Ensure the directory for the SQLite file exists
    sqlite_db_file.parent.mkdir(parents=True, exist_ok=True)
    
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{sqlite_db_file}"
    logger.info(f"Using SQLite database at: {sqlite_db_file}")
else:
    # This case should ideally be caught by the initial DB_TYPE validation
    logger.critical(f"Unsupported DB_TYPE: '{DB_TYPE}'. Must be 'sqlite' or 'mysql'.")
    raise ValueError(f"Unsupported DB_TYPE: '{DB_TYPE}'. Set DB_TYPE to 'sqlite' or 'mysql' in .env file.")

if not SQLALCHEMY_DATABASE_URL:
    # This should not be reached if logic above is correct, but as a safeguard:
    logger.critical("SQLALCHEMY_DATABASE_URL was not set. This indicates a configuration logic error.")
    raise RuntimeError("Failed to configure SQLALCHEMY_DATABASE_URL.")

# --- Create SQLAlchemy Engine ---
# For SQLite, add connect_args to handle potential multi-threading issues with FastAPI/Uvicorn
connect_args = {"check_same_thread": False} if DB_TYPE == "sqlite" else {}
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
logger.info(f"SQLAlchemy engine created for: {engine.url.drivername}")


# --- SQLAlchemy SessionLocal and Base ---
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
