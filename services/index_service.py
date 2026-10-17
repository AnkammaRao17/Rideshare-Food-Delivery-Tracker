"""
Index management and diagnostic service.
Allows inspecting, creating, dropping, and analyzing MongoDB indexes across collections.
"""

from typing import Dict, Any, List, Optional
from pymongo import ASCENDING, DESCENDING
from db import get_db


def list_collection_indexes(collection_name: str, db=None) -> List[Dict[str, Any]]:
    """List all indexes for a given collection with metadata."""
    database = db if db is not None else get_db()
    collection = database[collection_name]
    
    indexes = []
    for idx in collection.list_indexes():
        info = {
            "name": idx.get("name"),
            "keys": list(idx.get("key", {}).items()),
            "unique": idx.get("unique", False),
            "sparse": idx.get("sparse", False),
            "v": idx.get("v")
        }
        indexes.append(info)
    return indexes


def create_index_on_collection(
    collection_name: str,
    fields: List[tuple],
    unique: bool = False,
    name: Optional[str] = None,
    db=None
) -> str:
    """
    Create an index on specified fields.
    fields example: [("status", 1), ("created_at", -1)]
    """
    database = db if db is not None else get_db()
    collection = database[collection_name]
    
    kwargs = {"unique": unique}
    if name and name.strip():
        kwargs["name"] = name.strip()
        
    created_name = collection.create_index(fields, **kwargs)
    return created_name


def drop_index_from_collection(collection_name: str, index_name: str, db=None) -> bool:
    """Drop an existing index by name (prevent dropping _id_)."""
    if index_name == "_id_":
        raise ValueError("Cannot drop the default unique primary key index '_id_'.")
        
    database = db if db is not None else get_db()
    collection = database[collection_name]
    collection.drop_index(index_name)
    return True


def get_all_collections_index_summary(db=None) -> Dict[str, Any]:
    """Retrieve index statistics across all collections."""
    database = db if db is not None else get_db()
    col_names = ["users", "drivers", "rides", "restaurants", "food_orders"]
    
    summary = {}
    for col in col_names:
        try:
            stats = database.command("collStats", col)
            indexes = list_collection_indexes(col, db=database)
            summary[col] = {
                "count": stats.get("count", 0),
                "size_kb": round(stats.get("size", 0) / 1024, 2),
                "total_index_size_kb": round(stats.get("totalIndexSize", 0) / 1024, 2),
                "num_indexes": len(indexes),
                "indexes": indexes
            }
        except Exception as e:
            indexes = list_collection_indexes(col, db=database)
            summary[col] = {
                "count": database[col].count_documents({}),
                "size_kb": 0,
                "total_index_size_kb": 0,
                "num_indexes": len(indexes),
                "indexes": indexes,
                "error": str(e)
            }
    return summary
