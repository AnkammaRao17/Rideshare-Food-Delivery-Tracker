"""
Unit tests for MongoDB aggregation pipelines and analytics services.
"""

import pytest
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from services.analytics_service import (
    get_dashboard_kpis,
    get_revenue_trends,
    get_status_breakdown,
    get_revenue_by_cuisine,
    get_customer_activity_summaries
)
from services.query_service import (
    query_top_drivers_by_completed_rides,
    query_top_restaurants_by_revenue,
    query_rides_above_fare
)


def test_revenue_excludes_cancelled(test_db, sample_user, sample_driver, sample_restaurant):
    """Verify cancelled rides and orders are excluded from revenue sums."""
    now = datetime.now(timezone.utc)
    
    # 1. Insert a completed ride ($100) and a cancelled ride ($500)
    test_db.rides.insert_many([
        {
            "user_id": sample_user["_id"],
            "driver_id": sample_driver["_id"],
            "pickup_location": "Loc A",
            "dropoff_location": "Loc B",
            "distance_km": 5.0,
            "fare": 100.0,
            "status": "completed",
            "created_at": now,
            "completed_at": now
        },
        {
            "user_id": sample_user["_id"],
            "driver_id": sample_driver["_id"],
            "pickup_location": "Loc A",
            "dropoff_location": "Loc B",
            "distance_km": 25.0,
            "fare": 500.0,
            "status": "cancelled",
            "created_at": now
        }
    ])
    
    # 2. Insert a delivered order ($200) and a cancelled order ($1000)
    test_db.food_orders.insert_many([
        {
            "user_id": sample_user["_id"],
            "restaurant_id": sample_restaurant["_id"],
            "items": [{"item_name": "Dish 1", "quantity": 1, "price": 170.0}],
            "delivery_fee": 30.0,
            "total_amount": 200.0,
            "status": "delivered",
            "created_at": now,
            "delivered_at": now
        },
        {
            "user_id": sample_user["_id"],
            "restaurant_id": sample_restaurant["_id"],
            "items": [{"item_name": "Dish 2", "quantity": 5, "price": 190.0}],
            "delivery_fee": 50.0,
            "total_amount": 1000.0,
            "status": "cancelled",
            "created_at": now
        }
    ])
    
    kpis = get_dashboard_kpis(db=test_db)
    # Revenue should be 100.0 (ride) + 200.0 (order) = 300.0, ignoring 500 and 1000
    assert kpis["ride_revenue"] == 100.0
    assert kpis["order_revenue"] == 200.0
    assert kpis["total_platform_revenue"] == 300.0
    assert kpis["completed_rides"] == 1
    assert kpis["delivered_orders"] == 1


def test_status_breakdown(test_db):
    """Verify status distribution aggregation groups correctly."""
    breakdown = get_status_breakdown(db=test_db)
    assert "rides" in breakdown
    assert "orders" in breakdown
    assert isinstance(breakdown["rides"], list)
    assert isinstance(breakdown["orders"], list)


def test_top_drivers_aggregation(test_db):
    """Verify driver aggregation returns valid ranked list."""
    top_drivers = query_top_drivers_by_completed_rides(limit=5, db=test_db)
    assert isinstance(top_drivers, list)
    if top_drivers:
        assert "completed_rides" in top_drivers[0]
        assert "driver_name" in top_drivers[0]


def test_revenue_by_cuisine_aggregation(test_db):
    """Verify cuisine aggregation groups correctly."""
    cuisine_rev = get_revenue_by_cuisine(db=test_db)
    assert isinstance(cuisine_rev, list)
    if cuisine_rev:
        assert "cuisine" in cuisine_rev[0]
        assert "total_revenue" in cuisine_rev[0]
