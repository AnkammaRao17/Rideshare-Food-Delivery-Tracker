"""
Main Application Entry Point for Rideshare & Food Delivery Tracker.
Uses Streamlit st.navigation with st.Page for robust, conflict-free multi-page routing.
Features clean white sidebar (#FFFFFF) with dark readable text (#1F2937),
light teal active state (#CCFBF1), and Indian Rupee (INR ₹) currency formatting.
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import DATABASE_NAME, MONGO_URI
from db import ping_db, reset_db
from ui_components import inject_custom_css, format_inr
from scripts.seed_data import seed_database

# Import page views
from pages import (
    dashboard_view,
    users_view,
    drivers_view,
    rides_view,
    restaurants_view,
    orders_view,
    advanced_queries_view,
    analytics_view,
    indexes_view,
    performance_view,
    validation_testing_view
)

# 1. Page Configuration (Must be first Streamlit call)
st.set_page_config(
    page_title="Rideshare & Food Delivery Tracker",
    page_icon="🚖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Track execution flag to prevent duplicate rendering
st.session_state["_running_via_app"] = True

# 3. Inject Polished CSS Theme (Light Sidebar & Crisp Theme)
inject_custom_css()

# 4. Check MongoDB Connection
is_connected, db_info = ping_db()

# 5. Define Navigation Pages without repetitive 'Manage' labels
pages = {
    "OVERVIEW": [
        st.Page(dashboard_view.render, title="Dashboard", icon="📊", url_path="dashboard", default=True),
    ],
    "OPERATIONS": [
        st.Page(rides_view.render, title="Rides", icon="🚕", url_path="rides"),
        st.Page(orders_view.render, title="Food Orders", icon="🍔", url_path="orders"),
        st.Page(drivers_view.render, title="Drivers", icon="🚖", url_path="drivers"),
        st.Page(restaurants_view.render, title="Restaurants", icon="🍽️", url_path="restaurants"),
        st.Page(users_view.render, title="Users", icon="👥", url_path="users"),
    ],
    "ANALYTICS & DATABASE": [
        st.Page(analytics_view.render, title="Analytics", icon="🧠", url_path="analytics"),
        st.Page(advanced_queries_view.render, title="Advanced Queries", icon="⚡", url_path="advanced_queries"),
        st.Page(indexes_view.render, title="Indexes", icon="🗂️", url_path="indexes"),
        st.Page(performance_view.render, title="Performance", icon="📈", url_path="performance"),
        st.Page(validation_testing_view.render, title="Validation & Testing", icon="🛡️", url_path="validation_testing"),
    ]
}

pg = st.navigation(pages)

# 6. Sidebar Branding & DB Status
with st.sidebar:
    st.markdown("""
    <div style="padding: 0.35rem 0 0.75rem 0; text-align: left;">
        <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.25rem;">
            <div style="width: 38px; height: 38px; border-radius: 10px; background: linear-gradient(135deg, #0F9D8A 0%, #3B82F6 100%); display: flex; align-items: center; justify-content: center; font-size: 1.25rem; box-shadow: 0 4px 12px rgba(15, 157, 138, 0.28); flex-shrink: 0;">
                🚖
            </div>
            <div>
                <h2 style="font-size: 1.18rem; font-weight: 800; background: linear-gradient(135deg, #0F9D8A 0%, #2563EB 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; line-height: 1.15; letter-spacing: -0.01em;">
                    SwiftRoute &amp; Bite
                </h2>
                <p style="font-size: 0.72rem; color: #64748B; margin: 0.15rem 0 0 0; font-weight: 500;">
                    Indian Mobility &amp; Delivery Tracker
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # DB Status Badge (Glass styling with glowing dot)
    if is_connected:
        st.markdown(f"""
        <div style="background: rgba(240, 253, 244, 0.9); border: 1px solid #BBF7D0; border-radius: 8px; padding: 0.45rem 0.65rem; margin-bottom: 0.65rem; box-shadow: 0 2px 6px rgba(22, 163, 74, 0.06);">
            <div style="display: flex; align-items: center; gap: 0.4rem;">
                <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: #16A34A; box-shadow: 0 0 8px #22C55E;"></span>
                <span style="color: #15803D; font-weight: 700; font-size: 0.8rem;">MongoDB Connected</span>
            </div>
            <div style="color: #475569; font-size: 0.71rem; margin-top: 0.15rem; margin-left: 1.2rem;">Engine: v{db_info.get('version', '8.x')} | DB: {DATABASE_NAME}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: rgba(254, 242, 242, 0.9); border: 1px solid #FECACA; border-radius: 8px; padding: 0.45rem 0.65rem; margin-bottom: 0.65rem; box-shadow: 0 2px 6px rgba(220, 38, 38, 0.06);">
            <div style="display: flex; align-items: center; gap: 0.4rem;">
                <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: #DC2626; box-shadow: 0 0 8px #EF4444;"></span>
                <span style="color: #B91C1C; font-weight: 700; font-size: 0.8rem;">MongoDB Offline</span>
            </div>
            <div style="color: #64748B; font-size: 0.71rem; margin-top: 0.15rem; margin-left: 1.2rem;">Run: net start MongoDB</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<hr style='margin: 0.4rem 0 0.6rem 0; border: none; border-top: 1px solid rgba(226, 232, 240, 0.8);'>", unsafe_allow_html=True)
    
    # Quick DB Seed / Reset Tool in Sidebar
    with st.expander("🌱 Indian Sample Data & Reseed"):
        st.caption("Populate realistic Indian users, drivers, restaurants, and trips.")
        num_seed_rides = st.number_input("Rides to seed", min_value=10, max_value=500, value=100, step=25)
        num_seed_orders = st.number_input("Orders to seed", min_value=10, max_value=500, value=100, step=25)
        do_reset = st.checkbox("Reset (Clear) Database First", value=False)
        confirm_reset = True
        if do_reset:
            confirm_reset = st.checkbox("⚠️ Confirm: Clear existing data and reseed fresh Indian dataset", value=False)
        
        if st.button("Generate Indian Records", type="primary", use_container_width=True):
            if do_reset and not confirm_reset:
                st.warning("Please check the confirmation box above to proceed with database reset.")
            else:
                with st.spinner("Seeding database with authentic Indian records..."):
                    try:
                        seed_database(
                            num_users=40,
                            num_drivers=24,
                            num_restaurants=16,
                            num_rides=int(num_seed_rides),
                            num_orders=int(num_seed_orders),
                            reset=do_reset
                        )
                        st.success("Database populated with authentic Indian data!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Seeding failed: {e}")

    st.markdown("""
    <div style="font-size: 0.7rem; color: #94A3B8; text-align: center; margin-top: 1.25rem;">
        Full-Stack MongoDB & Streamlit<br>
        Indian Logistics Architecture (INR ₹)
    </div>
    """, unsafe_allow_html=True)

# 7. Execute Active Page View
if not is_connected:
    st.error(f"""
    ⚠️ **Unable to connect to MongoDB server.**  
    Please ensure your local MongoDB service is running (`net start MongoDB` in PowerShell)  
    or verify your `MONGO_URI` in `.env`.
    """)
else:
    pg.run()
