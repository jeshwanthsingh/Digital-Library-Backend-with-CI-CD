import pytest
from fastapi.testclient import TestClient
import os
import sys

# Add application root to Python path
# Ensure this path points correctly from tests/api/ to the project root containing 'application'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import necessary components AFTER adjusting path
from application.app import app
# Note: The TestClient uses the app instance which should already have the
# database dependency override applied from tests/test_app.py if pytest
# discovers and runs tests in the intended order/context.

# Create test client
# It's generally better practice to create the client within a fixture
# if setup/teardown is needed per test/module, but for simplicity here,
# we'll use the globally configured app instance.
client = TestClient(app)

# --- Tests ---

def test_health():
    """Test the health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"

def test_categories():
    """Test the categories endpoint."""
    # Note: This test assumes the database is seeded or categories are created.
    # If the DB is empty, this might pass with an empty list, which could be valid.
    response = client.get("/api/categories")
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
    assert isinstance(response.json(), list)
    # Add more specific assertions if seed data is known, e.g.:
    # assert len(response.json()) > 0
    # assert any(cat['name'] == 'Electronics' for cat in response.json())

def test_search():
    """Test the search endpoint with various parameters."""
    # Note: These tests assume the database is seeded or listings exist.
    # If the DB is empty, 'total' might be 0 and 'results' an empty list.

    # Test 1: Basic search without parameters
    response = client.get("/api/search")
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
    data = response.json()
    assert "total" in data
    assert "results" in data
    assert isinstance(data["results"], list)
    # Store the initial total for comparison if needed
    # initial_total = data["total"]

    # Test 2: Search with a query parameter (adapt 'testquery' if needed)
    params = {"query": "testquery"}
    response = client.get("/api/search", params=params)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
    data = response.json()
    assert "total" in data
    assert "results" in data
    # Add assertions: e.g., check if results contain 'testquery' or total <= initial_total

    # Test 3: Search with category filter (adapt category_id if needed)
    # Ensure category ID 1 exists in your test/seed data or adjust the ID
    params = {"category_id": 1}
    response = client.get("/api/search", params=params)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
    data = response.json()
    assert "total" in data
    assert "results" in data
    # Add assertions: e.g., check if all results have category_id == 1

    # Test 4: Search with price range
    params = {"min_price": 10, "max_price": 50}
    response = client.get("/api/search", params=params)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
    data = response.json()
    assert "total" in data
    assert "results" in data
    # Add assertions: e.g., check if all results have price between 10 and 50

    # Test 5: Search with condition filter
    params = {"condition": "new"}
    response = client.get("/api/search", params=params)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
    data = response.json()
    assert "total" in data
    assert "results" in data
    # Add assertions: e.g., check if all results have condition 'new'

    # Test 6: Combined search (adapt params based on seed data)
    params = {
        "query": "item", # Generic query
        "category_id": 1, # Adjust if needed
        "min_price": 5,
        "condition": "used"
    }
    response = client.get("/api/search", params=params)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
    data = response.json()
    assert "total" in data
    assert "results" in data
    # Add more specific assertions for combined filters

    # Test 7: Search with pagination (limit and offset)
    params = {"limit": 2, "offset": 1} # Get 2 items, skipping the first 1
    response = client.get("/api/search", params=params)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
    data = response.json()
    assert "total" in data
    assert "results" in data
    assert len(data["results"]) <= 2
    # Add assertions to check pagination logic if possible (e.g., compare results with different offsets)

    # Test 8: Search for skill sharing listings
    params = {"is_skill_sharing": True}
    response = client.get("/api/search", params=params)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
    data = response.json()
    assert "total" in data
    assert "results" in data
    # Add assertions: e.g., check if all results have is_skill_sharing == True
