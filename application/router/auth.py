from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List # Added List
# Removed CryptContext import as it's now in security.py
from datetime import datetime, timedelta # timedelta is used by the imported create_access_token
# jwt and JWTError are no longer directly used here if create_access_token is imported

from application.database import crud, models, database
from application import schemas # Use schemas.<SchemaName>
from application.security import get_current_active_user as get_current_user # Use the centralized one
# Import create_access_token directly from security module
from application.security import get_password_hash, verify_password, create_access_token

# SECRET_KEY, ALGORITHM, and ACCESS_TOKEN_EXPIRE_MINUTES are now centralized in security.py

# pwd_context is now in security.py
router = APIRouter(prefix="/auth", tags=["auth"]) # Changed prefix from /api/auth to /auth

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# verify_password and get_password_hash are imported from application.security
# local create_access_token function is removed, will use the one from security.py

@router.post("/register", response_model=schemas.UserRead)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    db_user = crud.get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    user_obj = crud.create_user(db, user.username, user.email, hashed_password, is_admin=user.is_admin)
    return schemas.UserRead(
        user_id=user_obj.user_id,
        username=user_obj.username,
        email=user_obj.email,
        is_active=user_obj.is_active,
        is_admin=user_obj.is_admin, # Ensure this is returned
        created_at=user_obj.created_at
    )

@router.post("/login")
def login(form_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, form_data.email)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": user.username}) # Use username as JWT subject
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserRead)
def read_users_me(current_user: models.User = Depends(get_current_user)):
   """
   Get the current authenticated user's information.
   """
   # The get_current_user dependency already fetches and returns the user model
   return current_user

@router.get("/users/search", response_model=List[schemas.UserMinimal])
def search_users(
   q: str,
   db: Session = Depends(get_db),
   current_user: models.User = Depends(get_current_user) # Protects the endpoint
):
   """
   Search for users by username or email.
   Requires authentication.
   Returns a list of users (id and username only).
   """
   if not q.strip():
       raise HTTPException(status_code=400, detail="Search query cannot be empty")
   
   users_found = crud.search_users_by_username_or_email(db, query_str=q, limit=10)
   # The crud function returns List[models.User].
   # Pydantic will automatically convert these to List[UserMinimal]
   # if the UserMinimal schema has orm_mode = True / from_attributes = True.
   return users_found