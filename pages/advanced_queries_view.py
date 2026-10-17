"""
Advanced MongoDB Queries Page.
Interactive demonstration of operators ($gt, $gte, $lte, $in, $and, $or, projections, compound filters).
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta

from services.query_service import (
    query_rides_above_fare,
    query_completed_rides_for_driver,
    query_orders_in_date_range,
    query_cancelled_transactions,
    query_restaurants_above_rating,
    query_top_customers_by_order_count,
    query_top_drivers_by_completed_rides,
    query_top_restaurants_by_revenue
)
from services.drivers_service import get_all_drivers_dropdown
from config import RIDE_STATUSES, CUISINE_TYPES
from ui_components import (
    render_header,
    render_empty_state,
    inject_custom_css,
    format_inr
)


def render():
    inject_custom_css()
    render_header(
        "Advanced Queries",
        "Explore targeted PyMongo queries using $gt, $gte, $in, $or, compound filters, and projections.",
        "⚡"
    )
    
    query_option = st.selectbox(
        "Select Query Scenario to Execute",
        options=[
            "1. Rides with Fare Greater Than Specified Amount ($gt)",
            "2. Completed Rides for a Specific Driver ($and / Compound)",
            "3. Food Orders Placed in a Date Range ($gte & $lte)",
            "4. Cancelled Rides and Food Orders ($in / $or)",
            "5. Restaurants Above a Rating Threshold ($gte, Projection)",
            "6. Top Customers by Order Frequency ($group, $sort, $limit)",
            "7. Top Drivers by Completed Rides ($match, $group, $lookup)",
            "8. Top Restaurants by Revenue ($match, $group, $sort)"
        ]
    )
    
    st.markdown("---")
    
    # 1. RIDES ABOVE FARE
    if "1. Rides with Fare" in query_option:
        st.subheader("1. Rides with Fares Above Threshold ($gt)")
        st.markdown("""
        **MongoDB Concepts:** Filtering numeric values with `$gt` / `$gte`, sorted descending, joined with customer and driver profiles.
        """)
        
        c1, c2 = st.columns(2)
        with c1:
            min_fare_val = st.slider("Minimum Fare (₹)", 50.0, 1000.0, 300.0, 25.0)
        with c2:
            status_sel = st.selectbox("Status Filter", ["All"] + RIDE_STATUSES, index=0)
            
        st.markdown(f"""
        ```python
        # PyMongo Query
        query = {{"fare": {{"$gt": {min_fare_val}}}}}
        db.rides.find(query).sort("fare", -1)
        ```
        """)
        
        try:
            res = query_rides_above_fare(min_fare_val, status=status_sel)
            st.write(f"**Found {len(res)} rides matching criteria:**")
            if res:
                df = pd.DataFrame(res)[["_id", "user_name", "driver_name", "pickup_location", "dropoff_location", "fare", "status"]]
                df["fare"] = df["fare"].apply(lambda v: format_inr(v))
                df.columns = ["Ride ID", "User", "Driver", "Pickup", "Dropoff", "Fare (₹)", "Status"]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                render_empty_state("No Rides Matched", f"No trips found with fare > {format_inr(min_fare_val)}.", "🚕")
        except Exception as ex:
            st.error(f"Query error: {ex}")

    # 2. COMPLETED RIDES FOR DRIVER
    elif "2. Completed Rides for a Specific Driver" in query_option:
        st.subheader("2. Completed Rides for a Specific Driver (Compound Equality)")
        st.markdown("""
        **MongoDB Concepts:** Compound matching combining an ObjectId reference (`driver_id`) and status equality (`status: "completed"`).
        """)
        
        try:
            drivers_dropdown = get_all_drivers_dropdown()
        except Exception:
            drivers_dropdown = []
            
        if not drivers_dropdown:
            render_empty_state("No Drivers Found", "Add drivers or seed sample data first.", "🚖")
            return
            
        selected_drv = st.selectbox(
            "Select Driver Partner",
            options=[d["_id"] for d in drivers_dropdown],
            format_func=lambda did: next((d["label"] for d in drivers_dropdown if d["_id"] == did), did)
        )
        
        st.markdown(f"""
        ```python
        # PyMongo Query
        query = {{
            "driver_id": ObjectId("{selected_drv}"),
            "status": "completed"
        }}
        db.rides.find(query).sort("created_at", -1)
        ```
        """)
        
        try:
            res = query_completed_rides_for_driver(selected_drv)
            st.write(f"**Found {len(res)} completed rides for this driver:**")
            if res:
                df = pd.DataFrame(res)[["_id", "user_name", "pickup_location", "dropoff_location", "distance_km", "fare", "completed_at"]]
                df["fare"] = df["fare"].apply(lambda v: format_inr(v))
                df.columns = ["Trip ID", "User", "Pickup", "Dropoff", "Distance (km)", "Fare (₹)", "Completed At"]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                render_empty_state("No Completed Rides", "This driver has no completed rides recorded.", "🚕")
        except Exception as ex:
            st.error(f"Query error: {ex}")

    # 3. DATE RANGE
    elif "3. Food Orders Placed in a Date Range" in query_option:
        st.subheader("3. Orders Placed Within a Date Range ($gte & $lte)")
        st.markdown("""
        **MongoDB Concepts:** Temporal range filtering on BSON Date timestamps using both `$gte` (inclusive lower bound) and `$lte` (inclusive upper bound).
        """)
        
        c1, c2 = st.columns(2)
        with c1:
            days_back = st.slider("Past N Days to Query", 1, 90, 30)
        with c2:
            order_status = st.selectbox("Status", ["All", "delivered", "placed", "preparing", "cancelled"])
            
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days_back)
        
        st.markdown(f"""
        ```python
        # PyMongo Query
        query = {{
            "created_at": {{
                "$gte": datetime({start_time.strftime('%Y, %m, %d')}),
                "$lte": datetime({end_time.strftime('%Y, %m, %d')})
            }}
        }}
        db.food_orders.find(query)
        ```
        """)
        
        try:
            res = query_orders_in_date_range(start_time, end_time, status=order_status)
            st.write(f"**Orders in past {days_back} days:** {len(res)}")
            if res:
                df = pd.DataFrame(res)[["_id", "user_name", "restaurant_name", "cuisine", "item_count", "total_amount", "status", "created_at"]]
                df["total_amount"] = df["total_amount"].apply(lambda v: format_inr(v))
                df.columns = ["Order ID", "Customer", "Restaurant", "Cuisine", "Items Count", "Total (₹)", "Status", "Placed At"]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                render_empty_state("No Orders in Range", "No orders were placed within this date interval.", "🍔")
        except Exception as ex:
            st.error(f"Query error: {ex}")

    # 4. CANCELLED TRANSACTIONS
    elif "4. Cancelled Rides and Food Orders" in query_option:
        st.subheader("4. Cancelled Rides and Food Orders ($in / $or)")
        st.markdown("""
        **MongoDB Concepts:** Auditing cancellations across both collections using `status: "cancelled"`. Demonstrates cross-collection analytics.
        """)
        
        st.markdown("""
        ```python
        # PyMongo Query
        rides_cancelled = db.rides.find({"status": "cancelled"})
        orders_cancelled = db.food_orders.find({"status": "cancelled"})
        ```
        """)
        
        try:
            res = query_cancelled_transactions(limit=25)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"#### Cancelled Rides ({len(res['cancelled_rides'])})")
                if res['cancelled_rides']:
                    df_r = pd.DataFrame(res['cancelled_rides'])[["_id", "pickup_location", "dropoff_location", "fare", "created_at"]]
                    df_r["fare"] = df_r["fare"].apply(lambda v: format_inr(v))
                    df_r.columns = ["Trip ID", "Pickup", "Dropoff", "Fare (₹)", "Booked At"]
                    st.dataframe(df_r, use_container_width=True, hide_index=True)
                else:
                    render_empty_state("No Cancelled Rides", "No rides were cancelled.", "🚕")
            with c2:
                st.markdown(f"#### Cancelled Food Orders ({len(res['cancelled_orders'])})")
                if res['cancelled_orders']:
                    df_o = pd.DataFrame(res['cancelled_orders'])[["_id", "total_amount", "delivery_fee", "created_at"]]
                    df_o["total_amount"] = df_o["total_amount"].apply(lambda v: format_inr(v))
                    df_o["delivery_fee"] = df_o["delivery_fee"].apply(lambda v: format_inr(v))
                    df_o.columns = ["Order ID", "Total (₹)", "Delivery Fee (₹)", "Placed At"]
                    st.dataframe(df_o, use_container_width=True, hide_index=True)
                else:
                    render_empty_state("No Cancelled Orders", "No food orders were cancelled.", "🍔")
        except Exception as ex:
            st.error(f"Query error: {ex}")

    # 5. RESTAURANTS ABOVE RATING
    elif "5. Restaurants Above a Rating Threshold" in query_option:
        st.subheader("5. Restaurants Above Rating Threshold ($gte, Projection)")
        st.markdown("""
        **MongoDB Concepts:** Filtering documents by numeric rating and active state with projections.
        """)
        
        c1, c2 = st.columns(2)
        with c1:
            min_r = st.slider("Rating Threshold", 3.0, 5.0, 4.2, 0.1)
        with c2:
            cuis_filter = st.selectbox("Cuisine", ["All"] + CUISINE_TYPES)
            
        st.markdown(f"""
        ```python
        # PyMongo Query
        query = {{"rating": {{"$gte": {min_r}}}, "is_active": True}}
        db.restaurants.find(query).sort("rating", -1)
        ```
        """)
        
        try:
            res = query_restaurants_above_rating(min_r, cuisine=cuis_filter, is_active=True)
            st.write(f"**Found {len(res)} top-rated restaurants:**")
            if res:
                df = pd.DataFrame(res)[["_id", "name", "cuisine", "location", "rating"]]
                df.columns = ["Restaurant ID", "Name", "Cuisine", "Location", "Rating ⭐"]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                render_empty_state("No Matches", "No restaurants match the specified rating and cuisine.", "🍽️")
        except Exception as ex:
            st.error(f"Query error: {ex}")

    # 6. TOP CUSTOMERS
    elif "6. Top Customers by Order Frequency" in query_option:
        st.subheader("6. Top Customers by Order Volume ($group, $sort, $limit)")
        st.markdown("""
        **MongoDB Concepts:** Aggregating customer order volume using `$group: {_id: "$user_id", count: {$sum: 1}}`, joined with `$lookup` to users collection.
        """)
        
        limit_val = st.slider("Number of Customers", 5, 25, 10)
        try:
            res = query_top_customers_by_order_count(limit=limit_val)
            if res:
                df = pd.DataFrame(res)[["name", "email", "phone", "order_count", "total_spent"]]
                df["total_spent"] = df["total_spent"].apply(lambda v: format_inr(v))
                df.columns = ["Customer Name", "Email", "Phone", "Orders Placed", "Total Spent (₹)"]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                render_empty_state("No Order Records", "No customer order history available.", "👥")
        except Exception as ex:
            st.error(f"Query error: {ex}")

    # 7. TOP DRIVERS
    elif "7. Top Drivers by Completed Rides" in query_option:
        st.subheader("7. Drivers with Most Completed Rides ($match, $group, $lookup)")
        st.markdown("""
        **MongoDB Concepts:** Aggregating driver ride completions: filtering with `$match: {status: 'completed'}`, grouping by `driver_id`, and summing earnings.
        """)
        
        limit_val = st.slider("Number of Drivers", 5, 25, 10)
        try:
            res = query_top_drivers_by_completed_rides(limit=limit_val)
            if res:
                df = pd.DataFrame(res)[["driver_name", "vehicle_type", "rating", "completed_rides", "total_fare_earned", "total_distance"]]
                df["total_fare_earned"] = df["total_fare_earned"].apply(lambda v: format_inr(v))
                df.columns = ["Driver Name", "Vehicle Type", "Rating ⭐", "Completed Rides", "Total Earnings (₹)", "Total Distance (km)"]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                render_empty_state("No Completed Rides", "No completed rides recorded yet.", "🚖")
        except Exception as ex:
            st.error(f"Query error: {ex}")

    # 8. TOP RESTAURANTS BY REVENUE
    elif "8. Top Restaurants by Revenue" in query_option:
        st.subheader("8. Top Restaurants by Gross Revenue ($match, $group, $sort)")
        st.markdown("""
        **MongoDB Concepts:** Filtering delivered food orders, summing `total_amount` per `restaurant_id`, and sorting descending by revenue.
        """)
        
        limit_val = st.slider("Top N Restaurants", 5, 25, 10)
        try:
            res = query_top_restaurants_by_revenue(limit=limit_val)
            if res:
                df = pd.DataFrame(res)[["restaurant_name", "cuisine", "rating", "location", "delivered_orders", "gross_revenue"]]
                df["gross_revenue"] = df["gross_revenue"].apply(lambda v: format_inr(v))
                df.columns = ["Restaurant", "Cuisine", "Rating ⭐", "Location", "Delivered Orders", "Gross Revenue (₹)"]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                render_empty_state("No Delivered Orders", "No delivered orders recorded yet.", "🍽️")
        except Exception as ex:
            st.error(f"Query error: {ex}")


# Fallback execution if loaded directly
if __name__ == "__main__" or not st.session_state.get("_running_via_app", False):
    render()
