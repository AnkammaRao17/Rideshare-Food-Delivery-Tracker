"""
Unit tests for data validation, schema enforcement, and error handling.
"""

import pytest
from bson import ObjectId
from pymongo.errors import WriteError
from services.users_service import create_user
from services.rides_service import create_ride
from services.orders_service import create_order
from services.drivers_service import create_driver
from models.validation import (
    ValidationError,
    NotFoundError,
    DuplicateRecordError,
    validate_email,
    validate_rating,
    validate_positive_number,
    validate_object_id
)


def test_invalid_email_format():
    """Verify malformed emails are rejected."""
    with pytest.raises(ValidationError):
        validate_email("not-an-email")
    with pytest.raises(ValidationError):
        validate_email("user@")
    with pytest.raises(ValidationError):
        validate_email("@domain.com")


def test_duplicate_email_rejection(test_db):
    """Verify unique email constraint prevents duplicates."""
    email = f"duplicate_{ObjectId()}@example.com"
    payload1 = {"name": "User One", "email": email, "phone": "+1-555-0101"}
    payload2 = {"name": "User Two", "email": email, "phone": "+1-555-0102"}
    
    create_user(payload1, db=test_db)
    with pytest.raises(DuplicateRecordError):
        create_user(payload2, db=test_db)


def test_rating_bounds():
    """Verify rating must be between 1.0 and 5.0."""
    assert validate_rating(4.5) == 4.5
    assert validate_rating("5.0") == 5.0
    
    with pytest.raises(ValidationError):
        validate_rating(0.5)
    with pytest.raises(ValidationError):
        validate_rating(5.5)
    with pytest.raises(ValidationError):
        validate_rating("invalid")


def test_positive_number_validation():
    """Verify distance and amounts cannot be negative."""
    assert validate_positive_number(12.5, "fare") == 12.5
    with pytest.raises(ValidationError):
        validate_positive_number(-5.0, "fare")
    with pytest.raises(ValidationError):
        validate_positive_number(0, "distance_km", allow_zero=False)


def test_invalid_object_id():
    """Verify malformed ObjectIds raise ValidationError."""
    with pytest.raises(ValidationError):
        validate_object_id("12345", "test_id")
    with pytest.raises(ValidationError):
        validate_object_id("", "test_id")
    with pytest.raises(ValidationError):
        validate_object_id(None, "test_id")


def test_foreign_key_missing_user_or_driver(test_db):
    """Verify ride creation fails if referenced user or driver doesn't exist."""
    fake_user_id = str(ObjectId())
    fake_driver_id = str(ObjectId())
    
    payload = {
        "user_id": fake_user_id,
        "driver_id": fake_driver_id,
        "pickup_location": "Point A",
        "dropoff_location": "Point B",
        "distance_km": 5.0,
        "fare": 150.0,
        "status": "requested"
    }
    with pytest.raises(NotFoundError):
        create_ride(payload, db=test_db)


def test_invalid_ride_status(test_db, sample_user, sample_driver):
    """Verify invalid ride status is rejected."""
    payload = {
        "user_id": str(sample_user["_id"]),
        "driver_id": str(sample_driver["_id"]),
        "pickup_location": "Point A",
        "dropoff_location": "Point B",
        "distance_km": 5.0,
        "fare": 150.0,
        "status": "flying"  # Invalid status
    }
    with pytest.raises(ValidationError):
        create_ride(payload, db=test_db)


def test_order_empty_items(test_db, sample_user, sample_restaurant):
    """Verify food order requires at least one valid item."""
    payload = {
        "user_id": str(sample_user["_id"]),
        "restaurant_id": str(sample_restaurant["_id"]),
        "items": [],  # Empty items
        "delivery_fee": 30.0,
        "status": "placed"
    }
    with pytest.raises(ValidationError):
        create_order(payload, db=test_db)
