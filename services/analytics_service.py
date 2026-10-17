"""
Aggregation pipelines for analytics, metrics, and business intelligence.
All revenue metrics exclude cancelled transactions.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from db import get_db, doc_to_dict


def get_dashboard_kpis(db=None) -> Dict[str, Any]:
    """
    Compute core high-level KPIs across rides and food delivery.
    Excludes cancelled orders and rides from revenue calculations.
    """
    database = db if db is not None else get_db()
    
    # 1. Total counts
    total_users = database.users.count_documents({})
    total_drivers = database.drivers.count_documents({})
    active_drivers = database.drivers.count_documents({"availability": True})
    total_restaurants = database.restaurants.count_documents({})
    active_restaurants = database.restaurants.count_documents({"is_active": True})
    
    total_rides = database.rides.count_documents({})
    total_orders = database.food_orders.count_documents({})
    
    # 2. Rides Revenue and Averages (only completed rides)
    rides_rev_pipe = [
        {"$match": {"status": "completed"}},
        {
            "$group": {
                "_id": None,
                "total_revenue": {"$sum": "$fare"},
                "avg_fare": {"$avg": "$fare"},
                "completed_count": {"$sum": 1},
                "total_distance": {"$sum": "$distance_km"}
            }
        }
    ]
    rides_agg = list(database.rides.aggregate(rides_rev_pipe))
    ride_revenue = round(rides_agg[0]["total_revenue"], 2) if rides_agg else 0.0
    avg_fare = round(rides_agg[0]["avg_fare"], 2) if rides_agg else 0.0
    completed_rides = rides_agg[0]["completed_count"] if rides_agg else 0
    total_distance = round(rides_agg[0]["total_distance"], 2) if rides_agg else 0.0
    
    # 3. Orders Revenue and Averages (only delivered orders)
    orders_rev_pipe = [
        {"$match": {"status": "delivered"}},
        {
            "$group": {
                "_id": None,
                "total_revenue": {"$sum": "$total_amount"},
                "avg_order_value": {"$avg": "$total_amount"},
                "delivered_count": {"$sum": 1},
                "total_delivery_fees": {"$sum": "$delivery_fee"}
            }
        }
    ]
    orders_agg = list(database.food_orders.aggregate(orders_rev_pipe))
    order_revenue = round(orders_agg[0]["total_revenue"], 2) if orders_agg else 0.0
    avg_order_value = round(orders_agg[0]["avg_order_value"], 2) if orders_agg else 0.0
    delivered_orders = orders_agg[0]["delivered_count"] if orders_agg else 0
    delivery_fees = round(orders_agg[0]["total_delivery_fees"], 2) if orders_agg else 0.0
    
    total_platform_revenue = round(ride_revenue + order_revenue, 2)
    
    return {
        "total_users": total_users,
        "total_drivers": total_drivers,
        "active_drivers": active_drivers,
        "total_restaurants": total_restaurants,
        "active_restaurants": active_restaurants,
        "total_rides": total_rides,
        "completed_rides": completed_rides,
        "ride_revenue": ride_revenue,
        "avg_fare": avg_fare,
        "total_distance": total_distance,
        "total_orders": total_orders,
        "delivered_orders": delivered_orders,
        "order_revenue": order_revenue,
        "avg_order_value": avg_order_value,
        "delivery_fees": delivery_fees,
        "total_platform_revenue": total_platform_revenue
    }


def get_revenue_trends(period: str = "daily", db=None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Aggregate daily, weekly, or monthly revenue trends for rides and orders separately.
    period: 'daily' (%Y-%m-%d), 'weekly' (%Y-W%V), 'monthly' (%Y-%m)
    Excludes cancelled records.
    """
    database = db if db is not None else get_db()
    
    date_format = "%Y-%m-%d"
    if period == "weekly":
        date_format = "%Y-W%V"
    elif period == "monthly":
        date_format = "%Y-%m"
        
    rides_pipeline = [
        {"$match": {"status": "completed", "created_at": {"$ne": None}}},
        {
            "$group": {
                "_id": {"$dateToString": {"format": date_format, "date": "$created_at"}},
                "revenue": {"$sum": "$fare"},
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}},
        {
            "$project": {
                "period": "$_id",
                "revenue": {"$round": ["$revenue", 2]},
                "count": 1,
                "_id": 0
            }
        }
    ]
    
    orders_pipeline = [
        {"$match": {"status": "delivered", "created_at": {"$ne": None}}},
        {
            "$group": {
                "_id": {"$dateToString": {"format": date_format, "date": "$created_at"}},
                "revenue": {"$sum": "$total_amount"},
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}},
        {
            "$project": {
                "period": "$_id",
                "revenue": {"$round": ["$revenue", 2]},
                "count": 1,
                "_id": 0
            }
        }
    ]
    
    rides_trends = list(database.rides.aggregate(rides_pipeline))
    orders_trends = list(database.food_orders.aggregate(orders_pipeline))
    
    return {
        "rides": rides_trends,
        "orders": orders_trends
    }


def get_status_breakdown(db=None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Aggregate counts of completed, pending/in_progress, and cancelled records.
    """
    database = db if db is not None else get_db()
    
    rides_pipe = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    orders_pipe = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    rides_breakdown = [{"status": r["_id"], "count": r["count"]} for r in database.rides.aggregate(rides_pipe)]
    orders_breakdown = [{"status": o["_id"], "count": o["count"]} for o in database.food_orders.aggregate(orders_pipe)]
    
    return {
        "rides": rides_breakdown,
        "orders": orders_breakdown
    }


def get_revenue_by_cuisine(db=None) -> List[Dict[str, Any]]:
    """
    Aggregation pipeline:
    Delivered orders -> $lookup restaurants -> $unwind -> $group by cuisine -> $sort.
    """
    database = db if db is not None else get_db()
    
    pipeline = [
        {"$match": {"status": "delivered"}},
        {
            "$lookup": {
                "from": "restaurants",
                "localField": "restaurant_id",
                "foreignField": "_id",
                "as": "restaurant"
            }
        },
        {"$unwind": "$restaurant"},
        {
            "$group": {
                "_id": "$restaurant.cuisine",
                "total_revenue": {"$sum": "$total_amount"},
                "order_count": {"$sum": 1},
                "avg_order_value": {"$avg": "$total_amount"}
            }
        },
        {"$sort": {"total_revenue": -1}},
        {
            "$project": {
                "cuisine": "$_id",
                "total_revenue": {"$round": ["$total_revenue", 2]},
                "order_count": 1,
                "avg_order_value": {"$round": ["$avg_order_value", 2]},
                "_id": 0
            }
        }
    ]
    return list(database.food_orders.aggregate(pipeline))


def get_order_volume_by_day(db=None) -> List[Dict[str, Any]]:
    """
    Combined volume of rides and food orders by calendar day.
    """
    database = db if db is not None else get_db()
    
    pipeline = [
        {
            "$facet": {
                "rides_by_day": [
                    {"$match": {"created_at": {"$ne": None}}},
                    {
                        "$group": {
                            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                            "ride_count": {"$sum": 1}
                        }
                    }
                ],
                "orders_by_day": [
                    {"$match": {"created_at": {"$ne": None}}},
                    {
                        "$group": {
                            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                            "order_count": {"$sum": 1}
                        }
                    }
                ]
            }
        }
    ]
    
    res = list(database.rides.aggregate(pipeline))
    if not res:
        return []
        
    day_map: Dict[str, Dict[str, Any]] = {}
    for r in res[0].get("rides_by_day", []):
        day = r["_id"]
        if day not in day_map:
            day_map[day] = {"date": day, "rides": 0, "food_orders": 0}
        day_map[day]["rides"] = r["ride_count"]
        
    for o in res[0].get("orders_by_day", []):
        day = o["_id"]
        if day not in day_map:
            day_map[day] = {"date": day, "rides": 0, "food_orders": 0}
        day_map[day]["food_orders"] = o["order_count"]
        
    # Sort chronologically
    sorted_days = sorted(day_map.values(), key=lambda x: x["date"])
    for d in sorted_days:
        d["total_volume"] = d["rides"] + d["food_orders"]
    return sorted_days


def get_customer_activity_summaries(limit: int = 15, db=None) -> List[Dict[str, Any]]:
    """
    Summarize customer activities combining rides taken and food orders placed.
    """
    database = db if db is not None else get_db()
    
    pipeline = [
        {
            "$lookup": {
                "from": "rides",
                "localField": "_id",
                "foreignField": "user_id",
                "as": "rides"
            }
        },
        {
            "$lookup": {
                "from": "food_orders",
                "localField": "_id",
                "foreignField": "user_id",
                "as": "orders"
            }
        },
        {
            "$project": {
                "_id": 1,
                "name": 1,
                "email": 1,
                "phone": 1,
                "total_rides": {"$size": "$rides"},
                "total_orders": {"$size": "$orders"},
                "completed_rides": {
                    "$size": {
                        "$filter": {
                            "input": "$rides",
                            "as": "r",
                            "cond": {"$eq": ["$$r.status", "completed"]}
                        }
                    }
                },
                "delivered_orders": {
                    "$size": {
                        "$filter": {
                            "input": "$orders",
                            "as": "o",
                            "cond": {"$eq": ["$$o.status", "delivered"]}
                        }
                    }
                }
            }
        },
        {
            "$addFields": {
                "total_activity": {"$add": ["$total_rides", "$total_orders"]}
            }
        },
        {"$sort": {"total_activity": -1}},
        {"$limit": limit}
    ]
    return [doc_to_dict(doc) for doc in database.users.aggregate(pipeline)]
