"""
Restaurants Management Page.
Full CRUD: View records, Add new, Edit existing, View details, and Delete with confirmation.
"""

import streamlit as st
import pandas as pd

from services.restaurants_service import (
    create_restaurant, get_restaurants, get_restaurant_by_id,
    update_restaurant, delete_restaurant
)
from config import CUISINE_TYPES
from models.validation import ValidationError, NotFoundError
from ui_components import (
    render_header,
    paginate_dataframe,
    render_empty_state,
    inject_custom_css
)


def render():
    inject_custom_css()
    if "restaurants_success_toast" in st.session_state:
        st.success(st.session_state.pop("restaurants_success_toast"))
        
    render_header(
        "Restaurants",
        "View, register, edit, and manage partner restaurant profiles and operating availability.",
        "🍽️"
    )
    
    tab_list, tab_create = st.tabs(["📋 View Records", "➕ Add New"])
    
    # -------------------------------------------------------------
    # TAB 1: VIEW RECORDS
    # -------------------------------------------------------------
    with tab_list:
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            search_query = st.text_input("🔍 Search Name / Location", key="rest_search")
        with f2:
            cuisine_filter = st.selectbox("Cuisine Category", ["All"] + CUISINE_TYPES, index=0, key="rest_cuis")
        with f3:
            active_filter = st.selectbox("Operating Status", ["All", "Open Only", "Closed Only"], index=0, key="rest_act")
        with f4:
            min_rating = st.slider("Min Rating ⭐", 1.0, 5.0, 1.0, 0.1, key="rest_min_r")
            
        act_val = None
        if active_filter == "Open Only":
            act_val = True
        elif active_filter == "Closed Only":
            act_val = False
            
        try:
            restaurants, total_count = get_restaurants(
                search=search_query,
                cuisine=cuisine_filter if cuisine_filter != "All" else None,
                is_active=act_val,
                min_rating=min_rating if min_rating > 1.0 else None,
                page=1,
                limit=300,
                sort_by="rating",
                sort_dir=-1
            )
        except Exception as e:
            st.error(f"Error querying restaurants: {e}")
            restaurants, total_count = [], 0
            
        st.markdown(f"**Total Records Found:** `{total_count}`")
        
        if restaurants:
            df = pd.DataFrame(restaurants)[["_id", "name", "cuisine", "location", "rating", "is_active"]]
            df["is_active"] = df["is_active"].apply(lambda a: "🟢 Open" if a else "🔴 Closed")
            df.columns = ["Restaurant ID", "Restaurant Name", "Cuisine", "Location", "Rating ⭐", "Operating Status"]
            paginated_df = paginate_dataframe(df, page_size=10, key_prefix="rest_p")
            st.dataframe(paginated_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("🔍 Select a Record to View, Edit, or Delete")
            
            selected_rest_id = st.selectbox(
                "Choose a restaurant record",
                options=[r["_id"] for r in restaurants],
                format_func=lambda rid: next((f"{r['name']} ({r['cuisine']} - {r['location']}) | ⭐{r['rating']} | {'Open' if r.get('is_active') else 'Closed'}" for r in restaurants if r["_id"] == rid), rid),
                key="selected_rest_action"
            )
            
            if selected_rest_id:
                try:
                    rest_detail = get_restaurant_by_id(selected_rest_id)
                    col_view, col_edit = st.columns(2)
                    
                    with col_view:
                        st.markdown("#### 📄 Record Details")
                        st.markdown(f"""
                        <div class="glass-card" style="border-left: 4px solid #0F9D8A;">
                            <p><b>Restaurant ID:</b> <code>{rest_detail['_id']}</code></p>
                            <p><b>Restaurant Name:</b> {rest_detail['name']}</p>
                            <p><b>Cuisine:</b> {rest_detail['cuisine']}</p>
                            <p><b>Location:</b> {rest_detail['location']}</p>
                            <p><b>Rating:</b> ⭐ {rest_detail['rating']} / 5.0</p>
                            <p><b>Operating Status:</b> {'<span class="badge badge-completed">Open & Accepting Orders</span>' if rest_detail['is_active'] else '<span class="badge badge-cancelled">Closed / Inactive</span>'}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                        st.markdown("#### 🗑️ Delete Record")
                        confirm_del = st.checkbox("I confirm I want to permanently delete this restaurant record", key=f"del_chk_rst_{selected_rest_id}")
                        if st.button("Delete Restaurant Record", type="secondary", disabled=not confirm_del, key=f"del_btn_rst_{selected_rest_id}"):
                            try:
                                delete_restaurant(selected_rest_id)
                                st.success(f"Restaurant '{rest_detail['name']}' successfully removed!")
                                st.rerun()
                            except (ValidationError, NotFoundError) as e:
                                st.error(str(e))
                                
                    with col_edit:
                        st.markdown("#### ✏️ Edit Record")
                        with st.form("edit_rest_form"):
                            edit_name = st.text_input("Restaurant Name", value=rest_detail["name"])
                            edit_cuisine = st.selectbox(
                                "Cuisine",
                                options=CUISINE_TYPES,
                                index=CUISINE_TYPES.index(rest_detail["cuisine"]) if rest_detail["cuisine"] in CUISINE_TYPES else 0
                            )
                            edit_loc = st.text_input("Location", value=rest_detail["location"])
                            edit_rating = st.slider("Rating ⭐", 1.0, 5.0, float(rest_detail["rating"]), 0.1)
                            edit_active = st.checkbox("Operating Status (Open)", value=bool(rest_detail["is_active"]))
                            
                            submit_edit = st.form_submit_button("💾 Save Changes", type="primary")
                            if submit_edit:
                                try:
                                    update_restaurant(selected_rest_id, {
                                        "name": edit_name,
                                        "cuisine": edit_cuisine,
                                        "location": edit_loc,
                                        "rating": edit_rating,
                                        "is_active": edit_active
                                    })
                                    st.success("Restaurant updated successfully!")
                                    st.rerun()
                                except (ValidationError, NotFoundError) as e:
                                    st.error(str(e))
                except Exception as ex:
                    st.error(f"Error fetching restaurant details: {ex}")
        else:
            render_empty_state("No Restaurants Found", "No eateries match your active filter criteria.", "🍽️")

    # -------------------------------------------------------------
    # TAB 2: ADD NEW
    # -------------------------------------------------------------
    with tab_create:
        st.subheader("Add a New Restaurant")
        with st.form("add_restaurant_form"):
            c1, c2 = st.columns(2)
            with c1:
                new_name = st.text_input("Restaurant Name *", value="", placeholder="e.g. Spice Symphony", key="add_rst_name")
                new_cuisine = st.selectbox("Cuisine *", options=CUISINE_TYPES, key="add_rst_cuisine")
            with c2:
                new_location = st.text_input("Location *", value="", placeholder="e.g. Koramangala, Bangalore", key="add_rst_loc")
                new_rating = st.slider("Rating", 1.0, 5.0, 4.5, 0.1, key="add_rst_rating")
                new_active = st.checkbox("Operating Status (Open Immediately)", value=True, key="add_rst_active")
                
            submit_add = st.form_submit_button("➕ Add Restaurant", type="primary")
            if submit_add:
                try:
                    clean_name = str(new_name or "").strip()
                    clean_loc = str(new_location or "").strip()
                    
                    new_r = create_restaurant({
                        "name": clean_name,
                        "cuisine": new_cuisine,
                        "location": clean_loc,
                        "rating": float(new_rating),
                        "is_active": bool(new_active)
                    })
                    st.session_state["recent_added_restaurant"] = new_r
                    st.session_state["restaurants_success_toast"] = (
                        f"✅ **Restaurant '{new_r['name']}' successfully added & verified in MongoDB!** ID: `{new_r['_id']}` | "
                        f"Cuisine: {new_r['cuisine']} | Location: {new_r['location']}"
                    )
                    st.rerun()
                except (ValidationError, NotFoundError) as e:
                    st.error(f"⚠️ Validation Error: {e}")
                except Exception as ex:
                    import traceback
                    traceback.print_exc()
                    st.error(f"🔴 Database Operation Error: {type(ex).__name__}: {ex}")
                    print(f"DATABASE WRITE ERROR in add_restaurant: {ex}")


# Fallback execution if loaded directly
if __name__ == "__main__" or not st.session_state.get("_running_via_app", False):
    render()
