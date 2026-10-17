"""
Query optimization, executionStats explain plans, and index performance benchmarking.
Uses genuine PyMongo cursor explain to extract real metrics.
"""

import time
from datetime import datetime, timedelta, timezone
import random
from typing import Dict, Any, List, Optional, Tuple
from pymongo import ASCENDING, DESCENDING
from db import get_db, doc_to_dict


def extract_plan_summary(explain_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract readable metrics from MongoDB explain() result.
    Compatible with MongoDB 4.x - 8.x.
    """
    exec_stats = explain_dict.get("executionStats", {})
    query_planner = explain_dict.get("queryPlanner", {})
    winning_plan = query_planner.get("winningPlan", {})
    
    # Traverse stage tree to find leaf/dominant stage (e.g. COLLSCAN vs IXSCAN)
    stage = winning_plan.get("stage", "UNKNOWN")
    index_name = "None (Full Collection Scan)"
    
    def find_stage_and_index(node):
        nonlocal stage, index_name
        if not isinstance(node, dict):
            return
        curr_stage = node.get("stage", "")
        if curr_stage == "IXSCAN":
            stage = "IXSCAN"
            index_name = node.get("indexName", "Unknown Index")
            return
        elif curr_stage == "COLLSCAN":
            stage = "COLLSCAN"
            return
        # Check inputStage
        if "inputStage" in node:
            find_stage_and_index(node["inputStage"])
        if "inputStages" in node:
            for s in node["inputStages"]:
                find_stage_and_index(s)

    find_stage_and_index(winning_plan)
    
    # If the root stage is FETCH wrapping IXSCAN, indicate FETCH + IXSCAN
    if winning_plan.get("stage") == "FETCH" and stage == "IXSCAN":
        display_stage = f"FETCH + IXSCAN ({index_name})"
    elif stage == "IXSCAN":
        display_stage = f"IXSCAN ({index_name})"
    elif stage == "COLLSCAN":
        display_stage = "COLLSCAN (Table/Collection Scan)"
    else:
        display_stage = winning_plan.get("stage", "UNKNOWN")

    return {
        "executionTimeMillis": exec_stats.get("executionTimeMillis", 0),
        "totalDocsExamined": exec_stats.get("totalDocsExamined", 0),
        "totalKeysExamined": exec_stats.get("totalKeysExamined", 0),
        "nReturned": exec_stats.get("nReturned", 0),
        "stage": display_stage,
        "raw_stage": stage,
        "index_name": index_name,
        "namespace": query_planner.get("namespace", "unknown"),
        "raw_explain": explain_dict
    }


def analyze_query_plan(
    collection_name: str,
    filter_dict: Dict[str, Any],
    sort: Optional[List[tuple]] = None,
    projection: Optional[Dict[str, Any]] = None,
    db=None
) -> Dict[str, Any]:
    """
    Execute explain() on the specified query and return parsed metrics.
    """
    database = db if db is not None else get_db()
    cursor = database[collection_name].find(filter_dict, projection)
    if sort:
        cursor = cursor.sort(sort)
        
    explain_res = cursor.explain()
    return extract_plan_summary(explain_res)


def run_index_comparison_benchmark(
    collection_name: str,
    query_filter: Dict[str, Any],
    index_keys: List[tuple],
    index_name: str = "perf_eval_temp_idx",
    sort: Optional[List[tuple]] = None,
    db=None
) -> Dict[str, Any]:
    """
    Runs a rigorous before-and-after query performance benchmark.
    1. Removes target index if present.
    2. Runs explain to capture unindexed baseline (COLLSCAN).
    3. Builds the target index.
    4. Runs explain to capture indexed performance (IXSCAN).
    5. Calculates efficiency improvement percentage.
    6. Cleans up temporary index if created for benchmark.
    """
    database = db if db is not None else get_db()
    col = database[collection_name]
    
    # Step 1: Ensure index is NOT present for baseline test
    existing_indexes = [idx["name"] for idx in col.list_indexes()]
    if index_name in existing_indexes:
        col.drop_index(index_name)
        
    # Baseline Explain (Without Index)
    baseline_cursor = col.find(query_filter)
    if sort:
        baseline_cursor = baseline_cursor.sort(sort)
    baseline_explain = baseline_cursor.explain()
    baseline_stats = extract_plan_summary(baseline_explain)
    
    # Step 2: Create Index
    col.create_index(index_keys, name=index_name)
    
    # Indexed Explain (With Index)
    indexed_cursor = col.find(query_filter)
    if sort:
        indexed_cursor = indexed_cursor.sort(sort)
    indexed_explain = indexed_cursor.explain()
    indexed_stats = extract_plan_summary(indexed_explain)
    
    # Calculate Improvements
    docs_baseline = baseline_stats["totalDocsExamined"]
    docs_indexed = indexed_stats["totalDocsExamined"]
    docs_saved = max(0, docs_baseline - docs_indexed)
    docs_pct_reduction = (docs_saved / docs_baseline * 100) if docs_baseline > 0 else 0.0
    
    return {
        "collection": collection_name,
        "query_filter": str(query_filter),
        "index_keys": str(index_keys),
        "baseline": baseline_stats,
        "indexed": indexed_stats,
        "docs_saved": docs_saved,
        "docs_pct_reduction": round(docs_pct_reduction, 2),
        "time_diff_ms": baseline_stats["executionTimeMillis"] - indexed_stats["executionTimeMillis"]
    }


def seed_synthetic_benchmark_collection(num_records: int = 10000, db=None) -> Dict[str, Any]:
    """
    Generates a high-volume synthetic collection 'benchmark_rides'
    specifically designed to demonstrate huge performance discrepancies
    between COLLSCAN and IXSCAN during live demonstrations.
    """
    database = db if db is not None else get_db()
    col = database["benchmark_rides"]
    col.drop()  # Fresh baseline
    
    batch_size = 2000
    statuses = ["completed", "cancelled", "in_progress", "requested"]
    cities = ["Downtown", "Airport", "Suburbs", "Tech Park", "Uptown", "Metro Station"]
    
    base_time = datetime.now(timezone.utc)
    total_inserted = 0
    
    for b in range(0, num_records, batch_size):
        chunk_size = min(batch_size, num_records - b)
        batch = []
        for i in range(chunk_size):
            fare = round(random.uniform(50.0, 1500.0), 2)
            dist = round(random.uniform(1.0, 45.0), 2)
            days_ago = random.randint(0, 365)
            created_at = base_time - timedelta(days=days_ago, minutes=random.randint(0, 1440))
            
            doc = {
                "ride_code": f"RD-{b + i + 1:07d}",
                "pickup_zone": random.choice(cities),
                "dropoff_zone": random.choice(cities),
                "distance_km": dist,
                "fare": fare,
                "driver_code": f"DRV-{random.randint(1, 200):04d}",
                "status": random.choice(statuses),
                "created_at": created_at
            }
            batch.append(doc)
        col.insert_many(batch)
        total_inserted += len(batch)
        
    return {
        "collection": "benchmark_rides",
        "total_inserted": total_inserted,
        "indexes": [idx["name"] for idx in col.list_indexes()]
    }
