"""
Unit tests for MongoDB indexing, compound indexes, and explain plan verification.
"""

import pytest
from services.index_service import (
    list_collection_indexes,
    create_index_on_collection,
    drop_index_from_collection,
    get_all_collections_index_summary
)
from services.performance_service import (
    analyze_query_plan,
    run_index_comparison_benchmark
)


def test_required_indexes_present(test_db):
    """Verify default required indexes are present on collections."""
    user_indexes = [idx["name"] for idx in list_collection_indexes("users", db=test_db)]
    assert "idx_users_email_unique" in user_indexes or any("email" in str(idx["keys"]) for idx in list_collection_indexes("users", db=test_db))
    
    ride_indexes = [idx["name"] for idx in list_collection_indexes("rides", db=test_db)]
    assert any("driver_id" in str(idx["keys"]) for idx in list_collection_indexes("rides", db=test_db))


def test_create_and_drop_custom_index(test_db):
    """Verify dynamic index creation and safe deletion."""
    idx_name = "test_custom_pickup_idx"
    
    # 1. Create index
    created_name = create_index_on_collection(
        "rides",
        [("pickup_location", 1)],
        unique=False,
        name=idx_name,
        db=test_db
    )
    assert created_name == idx_name
    
    # 2. Verify existence
    indexes = [idx["name"] for idx in list_collection_indexes("rides", db=test_db)]
    assert idx_name in indexes
    
    # 3. Drop index
    dropped = drop_index_from_collection("rides", idx_name, db=test_db)
    assert dropped is True
    
    # 4. Verify gone
    indexes_after = [idx["name"] for idx in list_collection_indexes("rides", db=test_db)]
    assert idx_name not in indexes_after


def test_cannot_drop_primary_id_index(test_db):
    """Verify attempting to drop _id_ raises ValueError."""
    with pytest.raises(ValueError):
        drop_index_from_collection("users", "_id_", db=test_db)


def test_explain_plan_analysis(test_db):
    """Verify explain execution returns valid stage and metrics."""
    plan = analyze_query_plan("users", {"email": "nonexistent@test.com"}, db=test_db)
    assert "totalDocsExamined" in plan
    assert "totalKeysExamined" in plan
    assert "stage" in plan
    assert plan["stage"] is not None
