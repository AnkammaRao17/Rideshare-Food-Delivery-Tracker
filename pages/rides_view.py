"""
Rides Management Page.
Full CRUD: View records, Add new, Edit existing, View details, and Delete with confirmation.
All monetary amounts formatted in Indian Rupees (₹).
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timezone

from services.rides_service import (
    create_ride, get_rides, get_ride_by_id, update_ride, delete_ride
)
from services.users_service import get_all_users_dropdown
from services.drivers_service import get_all_drivers_dropdown
from config import RIDE_STATUSES
from models.validation import ValidationError, NotFoundError
from ui_components import (
    render_header,
    paginate_dataframe,
    render_empty_state,
    inject_custom_css,
    format_inr
)


def render():
    inject_custom_css()
    if "rides_success_toast" in st.session_state:
        st.success(st.session_state.pop("rides_success_toast"))
        
    render_header(
        "Rides",
        "View, dispatch, edit, and track rideshare trips across the city.",
        "🚕"
    )
    
    tab_list, tab_create = st.tabs(["📋 View Records", "➕ Add New"])
    
    try:
        users_dropdown = get_all_users_dropdown()
        drivers_dropdown = get_all_drivers_dropdown()
    except Exception as e:
        st.error(f"Error loading dropdown references: {e}")
        users_dropdown, drivers_dropdown = [], []
    
    # -------------------------------------------------------------
    # TAB 1: VIEW RECORDS
    # -------------------------------------------------------------
    with tab_list:
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            status_filter = st.selectbox("Trip Status", ["All"] + RIDE_STATUSES, index=0, key="rf_status")
        with f2:
            driver_filter = st.selectbox(
                "Driver Filter",
                options=["All"] + [d["_id"] for d in drivers_dropdown],
                format_func=lambda did: "All Drivers" if did == "All" else next((d["label"] for d in drivers_dropdown if d["_id"] == did), did),
                key="rf_driver"
            )
        with f3:
            user_filter = st.selectbox(
                "Customer Filter",
                options=["All"] + [u["_id"] for u in users_dropdown],
                format_func=lambda uid: "All Customers" if uid == "All" else next((u["label"] for u in users_dropdown if u["_id"] == uid), uid),
                key="rf_user"
            )
        with f4:
            min_fare = st.number_input("Min Fare (₹)", min_value=0.0, value=0.0, step=50.0, key="rf_fare")
            
        col_sort1, col_sort2 = st.columns(2)
        with col_sort1:
            sort_by = st.selectbox("Sort By", ["created_at", "fare", "distance_km"], index=0, key="rf_sort")
        with col_sort2:
            sort_dir_txt = st.selectbox("Sort Order", ["Descending (Newest / Highest)", "Ascending"], index=0, key="rf_dir")
            
        sort_dir = -1 if "Descending" in sort_dir_txt else 1
        
        try:
            rides, total_count = get_rides(
                status=status_filter if status_filter != "All" else None,
                driver_id=driver_filter if driver_filter != "All" else None,
                user_id=user_filter if user_filter != "All" else None,
                min_fare=min_fare if min_fare > 0 else None,
                page=1,
                limit=300,
                sort_by=sort_by,
                sort_dir=sort_dir
            )
        except Exception as e:
            st.error(f"Error querying rides: {e}")
            rides, total_count = [], 0
            
        st.markdown(f"**Total Records Found:** `{total_count}`")
        
        if rides:
            display_cols = [
                "_id", "user_name", "driver_name", "driver_vehicle",
                "pickup_location", "dropoff_location", "distance_km", "fare", "status", "created_at"
            ]
            df = pd.DataFrame(rides)[display_cols]
            df["fare"] = df["fare"].apply(format_inr)
            df.columns = ["Trip ID", "User", "Driver", "Vehicle", "Pickup", "Dropoff", "Dist (km)", "Fare (₹)", "Status", "Booked At"]
            paginated_df = paginate_dataframe(df, page_size=10, key_prefix="rides_p")
            st.dataframe(paginated_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("🔍 Select a Record to View, Edit, or Delete")
            
            selected_ride_id = st.selectbox(
                "Choose a ride record",
                options=[r["_id"] for r in rides],
                format_func=lambda rid: next((f"{r.get('user_name', 'Customer')} ➡️ {r.get('driver_name', 'Driver')} | {format_inr(r.get('fare', 0))} | {r.get('status').upper()}" for r in rides if r["_id"] == rid), rid),
                key="selected_ride_action"
            )
            
            if selected_ride_id:
                try:
                    ride_detail = get_ride_by_id(selected_ride_id)
                    col_view, col_edit = st.columns(2)
                    
                    with col_view:
                        st.markdown("#### 📄 Record Details")
                        user_info = ride_detail.get("user") or {}
                        driver_info = ride_detail.get("driver") or {}
                        
                        st.markdown(f"""
                        <div class="glass-card" style="border-left: 4px solid #0F9D8A;">
                            <p><b>Trip ID:</b> <code>{ride_detail['_id']}</code></p>
                            <p><b>Status:</b> <b>{ride_detail['status'].upper()}</b></p>
                            <p><b>User:</b> {user_info.get('name', 'N/A')} ({user_info.get('email', 'N/A')})</p>
                            <p><b>Driver:</b> {driver_info.get('name', 'N/A')} - {driver_info.get('vehicle_type', '')} ({driver_info.get('vehicle_number', '')})</p>
                            <p><b>Pickup Location:</b> {ride_detail['pickup_location']}</p>
                            <p><b>Drop-off Destination:</b> {ride_detail['dropoff_location']}</p>
                            <p><b>Distance:</b> {ride_detail['distance_km']} km</p>
                            <p><b>Fare:</b> {format_inr(ride_detail['fare'])}</p>
                            <p><b>Booked At:</b> {ride_detail['created_at']}</p>
                            <p><b>Completed At:</b> {ride_detail.get('completed_at') or 'Pending / In Progress'}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                        st.markdown("#### 🗑️ Delete Record")
                        confirm_del = st.checkbox("I confirm I want to permanently delete this ride record", key=f"del_chk_{selected_ride_id}")
                        if st.button("Delete Ride Record", type="secondary", disabled=not confirm_del, key=f"del_btn_{selected_ride_id}"):
                            try:
                                delete_ride(selected_ride_id)
                                st.success("Ride record successfully deleted!")
                                st.rerun()
                            except (ValidationError, NotFoundError) as e:
                                st.error(str(e))
                                
                    with col_edit:
                        st.markdown("#### ✏️ Edit Record")
                        with st.form("edit_ride_form"):
                            current_status = ride_detail["status"]
                            edit_status = st.selectbox(
                                "Ride Status",
                                options=RIDE_STATUSES,
                                index=RIDE_STATUSES.index(current_status) if current_status in RIDE_STATUSES else 0
                            )
                            edit_pickup = st.text_input("Pickup Location", value=ride_detail["pickup_location"])
                            edit_dropoff = st.text_input("Dropoff Location", value=ride_detail["dropoff_location"])
                            edit_dist = st.number_input("Distance (km)", min_value=0.1, value=float(ride_detail["distance_km"]), step=0.5)
                            edit_fare = st.number_input("Fare (₹)", min_value=0.0, value=float(ride_detail["fare"]), step=25.0)
                            
                            submit_edit = st.form_submit_button("💾 Save Changes", type="primary")
                            if submit_edit:
                                try:
                                    update_ride(selected_ride_id, {
                                        "user_id": str(ride_detail["user_id"]),
                                        "driver_id": str(ride_detail["driver_id"]),
                                        "pickup_location": edit_pickup,
                                        "dropoff_location": edit_dropoff,
                                        "distance_km": edit_dist,
                                        "fare": edit_fare,
                                        "status": edit_status
                                    })
                                    st.success("Ride updated successfully!")
                                    st.rerun()
                                except (ValidationError, NotFoundError) as e:
                                    st.error(str(e))
                except Exception as ex:
                    st.error(f"Error fetching ride details: {ex}")
        else:
            render_empty_state("No Rides Found", "No trips match your current filter settings.", "🚕")

    # -------------------------------------------------------------
    # TAB 2: ADD NEW
    # -------------------------------------------------------------
    with tab_create:
        st.subheader("Add a New Ride")
        if not users_dropdown or not drivers_dropdown:
            st.warning("Please ensure at least one customer and one driver exist before adding a ride.")
            return
            
        with st.form("add_ride_form", clear_on_submit=False):
            c1, c2 = st.columns(2)
            with c1:
                new_user = st.selectbox(
                    "Select User *",
                    options=[u["_id"] for u in users_dropdown],
                    format_func=lambda uid: next((u["label"] for u in users_dropdown if u["_id"] == uid), uid),
                    key="add_ride_user"
                )
                new_pickup = st.text_input("Pickup Location *", value="Hitec City, Hyderabad", key="add_ride_pickup")
                new_distance = st.number_input("Distance in kilometres *", min_value=0.1, value=12.5, step=0.5, key="add_ride_dist")
            with c2:
                new_driver = st.selectbox(
                    "Select Driver *",
                    options=[d["_id"] for d in drivers_dropdown],
                    format_func=lambda did: next((d["label"] for d in drivers_dropdown if d["_id"] == did), did),
                    key="add_ride_driver"
                )
                new_dropoff = st.text_input("Drop-off Location *", value="Airport Terminal, Hyderabad", key="add_ride_dropoff")
                new_fare = st.number_input("Fare in Indian Rupees (₹) *", min_value=0.0, value=480.0, step=25.0, key="add_ride_fare")
                
            new_status = st.selectbox("Initial Status", options=RIDE_STATUSES, index=0, key="add_ride_status")
            
            submit_add = st.form_submit_button("➕ Add Ride", type="primary")
            if submit_add:
                try:
                    # Explicitly read and strip submitted values
                    clean_pickup = str(new_pickup or "").strip()
                    clean_dropoff = str(new_dropoff or "").strip()
                    
                    new_r = create_ride({
                        "user_id": new_user,
                        "driver_id": new_driver,
                        "pickup_location": clean_pickup,
                        "dropoff_location": clean_dropoff,
                        "distance_km": float(new_distance),
                        "fare": float(new_fare),
                        "status": new_status
                    })
                    st.session_state["recent_added_ride"] = new_r
                    st.session_state["rides_success_toast"] = (
                        f"✅ **Ride successfully added & verified in MongoDB!** ID: `{new_r['_id']}` | "
                        f"Route: {new_r['pickup_location']} ➡️ {new_r['dropoff_location']} | Fare: {format_inr(new_r['fare'])}"
                    )
                    st.rerun()
                except (ValidationError, NotFoundError) as ve:
                    st.error(f"⚠️ Validation Error: {ve}")
                except Exception as ex:
                    import traceback
                    traceback.print_exc()
                    st.error(f"🔴 Database Operation Error: {type(ex).__name__}: {ex}")
                    print(f"DATABASE WRITE ERROR in add_ride: {ex}")
                    
        if "recent_added_ride" in st.session_state:
            last = st.session_state["recent_added_ride"]
            st.markdown(f"""
            <div style="background: #F0FDF4; border: 1px solid #86EFAC; border-radius: 8px; padding: 0.75rem 1rem; margin-top: 1rem;">
                <p style="color: #166534; font-weight: 600; margin: 0;">✨ Last Added Record (Verified in MongoDB):</p>
                <p style="color: #1F2937; margin: 0.25rem 0 0 0; font-size: 0.88rem;">
                    <b>ID:</b> <code>{last['_id']}</code> | <b>Customer:</b> {last.get('user_name', 'N/A')} | <b>Driver:</b> {last.get('driver_name', 'N/A')}<br>
                    <b>Route:</b> {last['pickup_location']} ➡️ {last['dropoff_location']} | <b>Fare:</b> {format_inr(last['fare'])}
                </p>
            </div>
            """, unsafe_allow_html=True)


# Fallback execution if loaded directly
if __name__ == "__main__" or not st.session_state.get("_running_via_app", False):
    render()
