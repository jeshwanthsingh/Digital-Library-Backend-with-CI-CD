import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import sys

# Add application to Python path
# Ensure this path points correctly from tests/ to the project root containing 'application'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import necessary components AFTER adjusting path
from application.app import app
from application.database.database import Base, get_db # Import Base and get_db

# --- Test Database Setup ---
# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool, # Use StaticPool for in-memory DB with TestClient
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables before running tests
Base.metadata.create_all(bind=engine)

# --- Dependency Override ---
def override_get_db():
    """Dependency override for test database sessions."""
    database = None
    try:
        database = TestingSessionLocal()
        yield database
    finally:
        if database:
            database.close()

# Apply the dependency override to the app
app.dependency_overrides[get_db] = override_get_db

# Create test client *after* dependency override
client = TestClient(app)

# --- Tests ---

def test_health_check():
    """Test that the health check endpoint returns 200 OK."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "healthy"

def test_categories_endpoint():
    """Test that the categories endpoint returns a list of categories."""
    response = client.get("/api/categories")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_search_endpoint():
    """Test that the search endpoint returns results."""
    response = client.get("/api/search")
    assert response.status_code == 200
    assert "total" in response.json()
    assert "results" in response.json()
    assert isinstance(response.json()["results"], list)
