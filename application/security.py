# application/security.py
import os
import logging # Import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from typing import Optional # For Python 3.9+, use `from typing import Union` and `Union[timedelta, None]` or `Optional[timedelta]`

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session # Assuming Session is imported for type hinting or direct use

# Attempt to import application-specific modules
# These might not be available in all contexts (e.g., unit testing security functions in isolation)
# but are needed for functions like get_current_user
try:
    from application.database import crud, models # Assuming these are your project's modules
    from application.database.database import get_db # Your dependency to get DB session
    # from application import schemas # If you use Pydantic models for token data, etc.
except ImportError:
    # Handle cases where these modules might not be available, or ensure they are.
    # For now, we'll let it pass and errors will occur if functions depending on them are called.
    logging.warning("SECURITY.PY: Could not import some application-specific modules (crud, models, get_db). Functions like get_current_user might fail if these are not available in the PYTHONPATH.")
    # Define placeholders if necessary for type hinting, though it's better to ensure correct PYTHONPATH
    class Placeholder: pass
    models = Placeholder()
    crud = Placeholder()
    def get_db(): pass


# --- Load .env file from the project root ---
# Assumes security.py is in 'application/' and .env is in the parent directory (project_root)
# Using pathlib for a more modern and robust path handling
from pathlib import Path
env_path = Path(__file__).resolve().parent.parent / '.env'

if env_path.exists():
    logging.info(f"SECURITY.PY: Attempting to load environment variables from: {env_path}")
    load_dotenv(dotenv_path=env_path)
else:
    logging.warning(f"SECURITY.PY: .env file not found at {env_path}. Environment variables must be set externally.")

# --- Configuration ---
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256") # Default to HS256 if not specified
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")) # Default to 30 minutes

# Configure logging
logging.basicConfig(level=logging.INFO) # Set default logging level
logger = logging.getLogger(__name__) # Get a logger for this module

if not SECRET_KEY:
    logger.critical("SECURITY.PY: CRITICAL ERROR - No SECRET_KEY set for JWT encoding/decoding. Please set it in your .env file or environment.")
    raise ValueError("No SECRET_KEY set for JWT encoding/decoding. Please set it in your .env file or environment.")
else:
    # Be cautious about logging the actual key in production. Logging its presence/length is safer.
    logger.info(f"SECURITY.PY: SECRET_KEY loaded successfully (length: {len(SECRET_KEY)}).")

logger.info(f"SECURITY.PY: ALGORITHM set to: {ALGORITHM}")
logger.info(f"SECURITY.PY: ACCESS_TOKEN_EXPIRE_MINUTES set to: {ACCESS_TOKEN_EXPIRE_MINUTES}")


# --- Password Hashing Context ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- OAuth2 Scheme ---
# tokenUrl should point to your token generation endpoint (e.g., in an auth router)
# Make sure this matches the actual endpoint in your application that serves the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False) # For optional authentication


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a password using the configured scheme (bcrypt)."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a new JWT access token.
    :param data: Dictionary containing the payload (e.g., {"sub": username})
    :param expires_delta: Optional timedelta to override default expiration
    :return: Encoded JWT string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # Log before encoding, being mindful of sensitive data in 'to_encode' if any
    logger.debug(f"SECURITY.PY (create_access_token): Encoding payload for user '{data.get('sub')}' with expiration {expire}.")
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> "models.User": # Use string literal for type hint
    """
    Decodes the JWT token, retrieves the user by username (from 'sub' claim),
    and returns the user object if valid and found.
    Raises HTTPException for invalid credentials or errors.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        logger.debug(f"SECURITY.PY (get_current_user): Attempting to decode token (first 10 chars): '{token[:10]}...'")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub") # 'sub' is standard for subject (username)
        
        if username is None:
            logger.warning("SECURITY.PY (get_current_user): 'sub' (username) claim missing from token payload.")
            raise credentials_exception
        
        # Optional: Validate token data structure if you have a Pydantic schema for it
        # from application import schemas # Assuming schemas.TokenData exists
        # token_data = schemas.TokenData(username=username)

    except JWTError as e:
        logger.error(f"SECURITY.PY (get_current_user): JWTError during token decoding: {e}")
        raise credentials_exception
    
    # Retrieve user from database
    # Ensure crud.get_user_by_username is implemented correctly in your application
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        logger.warning(f"SECURITY.PY (get_current_user): User '{username}' from token not found in database.")
        raise credentials_exception
    
    logger.info(f"SECURITY.PY (get_current_user): User '{username}' successfully authenticated.")
    return user

async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional), db: Session = Depends(get_db)
) -> Optional["models.User"]:
    """
    Decodes the JWT token if present, retrieves the user by username,
    and returns the user object or None if token is missing, invalid, or user not found.
    Does not raise HTTPException for auth errors, allowing endpoints to be truly optional.
    """
    if not token:
        logger.debug("SECURITY.PY (get_current_user_optional): No token provided.")
        return None
    try:
        logger.debug(f"SECURITY.PY (get_current_user_optional): Attempting to decode token (first 10 chars): '{token[:10]}...'")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            logger.warning("SECURITY.PY (get_current_user_optional): 'sub' (username) claim missing from token payload.")
            return None
    except JWTError as e:
        logger.warning(f"SECURITY.PY (get_current_user_optional): JWTError during token decoding: {e}")
        return None
    
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        logger.warning(f"SECURITY.PY (get_current_user_optional): User '{username}' from token not found in database.")
        return None
    
    logger.info(f"SECURITY.PY (get_current_user_optional): User '{username}' identified from token.")
    return user

async def get_current_active_user(
    current_user: "models.User" = Depends(get_current_user)
) -> "models.User":
    """
    Dependency that takes a user object (from get_current_user)
    and checks if the user is active.
    Raises HTTPException if the user is inactive.
    """
    if hasattr(current_user, 'is_active') and not current_user.is_active:
        logger.warning(f"SECURITY.PY (get_current_active_user): User '{current_user.username}' is inactive.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

async def get_current_active_user_optional(
    current_user: Optional["models.User"] = Depends(get_current_user_optional)
) -> Optional["models.User"]:
    """
    Dependency that takes an optional user object (from get_current_user_optional)
    and checks if the user is active. Returns None if user is None or inactive.
    Does not raise HTTPException for auth errors or inactivity.
    """
    if current_user and hasattr(current_user, 'is_active') and not current_user.is_active:
        logger.warning(f"SECURITY.PY (get_current_active_user_optional): User '{current_user.username}' is inactive, returning None.")
        return None
    return current_user

async def get_current_admin_user(
    current_user: "models.User" = Depends(get_current_active_user)
) -> "models.User":
    """
    Dependency that checks if the current active user is also an administrator.
    Raises HTTPException if the user is not an admin.
    """
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
        logger.warning(f"SECURITY.PY (get_current_admin_user): User '{current_user.username}' attempted admin access but is not an admin.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized: User is not an administrator"
        )
    return current_user

# Example of how you might use these in your endpoints:
# @router.get("/users/me/", response_model=schemas.User) # Assuming schemas.User is your Pydantic model for user output
# async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
# return current_user
