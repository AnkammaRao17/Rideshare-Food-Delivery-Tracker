"""
Pytest configuration and fixtures.
Provides isolated test database connection to prevent mutating development data.
"""

import pytest
from datetime import datetime, timezone
from bson import ObjectId
from config import TEST_DATABASE_NAME
from db import get_db, init_db, reset_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Initialize and teardown test database once per session."""
    reset_db(TEST_DATABASE_NAME, confirm=True)
    yield get_db(TEST_DATABASE_NAME)
    # Cleanup test db after test session
    reset_db(TEST_DATABASE_NAME, confirm=True)


@pytest.fixture(scope="function")
def test_db():
    """Provides a clean or fresh test database per test function."""
    db = get_db(TEST_DATABASE_NAME)
    return db


@pytest.fixture
def sample_user(test_db):
    """Create a sample user in the test database."""
    user_doc = {
        "_id": ObjectId(),
        "name": "Alice Wonderland",
        "email": f"alice_{ObjectId()}@example.com",
        "phone": "+1-555-0199",
        "created_at": datetime.now(timezone.utc)
    }
    test_db.users.insert_one(user_doc)
    return user_doc


@pytest.fixture
def sample_driver(test_db):
    """Create a sample driver in the test database."""
    driver_doc = {
        "_id": ObjectId(),
        "name": "John Driver",
        "phone": "+1-555-0144",
        "vehicle_type": "Sedan",
        "vehicle_number": "KA01AB1234",
        "rating": 4.8,
        "availability": True
    }
    test_db.drivers.insert_one(driver_doc)
    return driver_doc


@pytest.fixture
def sample_restaurant(test_db):
    """Create a sample restaurant in the test database."""
    rest_doc = {
        "_id": ObjectId(),
        "name": "Spice Pavilion",
        "cuisine": "North Indian",
        "location": "MG Road",
        "rating": 4.5,
        "is_active": True
    }
    test_db.restaurants.insert_one(rest_doc)
    return rest_doc
