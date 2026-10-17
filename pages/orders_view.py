"""
Food Orders Management Page.
Full CRUD: View records, Add new, Edit existing, View details, and Delete with confirmation.
All monetary amounts formatted in Indian Rupees (₹).
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from services.orders_service import (
    create_order, get_orders, get_order_by_id, update_order, delete_order
)
from services.users_service import get_all_users_dropdown
from services.restaurants_service import get_all_restaurants_dropdown
from config import ORDER_STATUSES
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
    if "orders_success_toast" in st.session_state:
        st.success(st.session_state.pop("orders_success_toast"))
        
    render_header(
        "Food Orders",
        "View, place, edit, and track food delivery orders with item-level details.",
        "🍔"
    )
    
    tab_list, tab_create = st.tabs(["📋 View Records", "➕ Add New"])
    
    try:
        users_dropdown = get_all_users_dropdown()
        restaurants_dropdown = get_all_restaurants_dropdown()
    except Exception as e:
        st.error(f"Error loading dropdown references: {e}")
        users_dropdown, restaurants_dropdown = [], []
    
    # -------------------------------------------------------------
    # TAB 1: VIEW RECORDS
    # -------------------------------------------------------------
    with tab_list:
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            status_filter = st.selectbox("Order Status", ["All"] + ORDER_STATUSES, index=0, key="of_status")
        with f2:
            restaurant_filter = st.selectbox(
                "Restaurant Filter",
                options=["All"] + [r["_id"] for r in restaurants_dropdown],
                format_func=lambda rid: "All Restaurants" if rid == "All" else next((r["label"] for r in restaurants_dropdown if r["_id"] == rid), rid),
                key="of_restaurant"
            )
        with f3:
            user_filter = st.selectbox(
                "Customer Filter",
                options=["All"] + [u["_id"] for u in users_dropdown],
                format_func=lambda uid: "All Customers" if uid == "All" else next((u["label"] for u in users_dropdown if u["_id"] == uid), uid),
                key="of_user"
            )
        with f4:
            min_amount = st.number_input("Min Total (₹)", min_value=0.0, value=0.0, step=50.0, key="of_amt")
            
        col_sort1, col_sort2 = st.columns(2)
        with col_sort1:
            sort_by = st.selectbox("Sort Field", ["created_at", "total_amount", "item_count"], index=0, key="of_sort")
        with col_sort2:
            sort_dir_txt = st.selectbox("Sort Order", ["Descending (Newest / Highest)", "Ascending"], index=0, key="of_dir")
            
        sort_dir = -1 if "Descending" in sort_dir_txt else 1
        
        try:
            orders, total_count = get_orders(
                status=status_filter if status_filter != "All" else None,
                restaurant_id=restaurant_filter if restaurant_filter != "All" else None,
                user_id=user_filter if user_filter != "All" else None,
                min_amount=min_amount if min_amount > 0 else None,
                page=1,
                limit=300,
                sort_by=sort_by,
                sort_dir=sort_dir
            )
        except Exception as e:
            st.error(f"Error querying food orders: {e}")
            orders, total_count = [], 0
            
        st.markdown(f"**Total Records Found:** `{total_count}`")
        
        if orders:
            display_cols = [
                "_id", "user_name", "restaurant_name", "cuisine",
                "item_count", "total_amount", "delivery_fee", "status", "created_at"
            ]
            df = pd.DataFrame(orders)[display_cols]
            df["total_amount"] = df["total_amount"].apply(format_inr)
            df["delivery_fee"] = df["delivery_fee"].apply(format_inr)
            df.columns = ["Order ID", "Customer", "Restaurant", "Cuisine", "Items Count", "Total (₹)", "Delivery Fee (₹)", "Status", "Placed At"]
            paginated_df = paginate_dataframe(df, page_size=10, key_prefix="orders_p")
            st.dataframe(paginated_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("🔍 Select a Record to View, Edit, or Delete")
            
            selected_order_id = st.selectbox(
                "Choose an order record",
                options=[o["_id"] for o in orders],
                format_func=lambda oid: next((f"{o.get('user_name', 'Customer')} ➡️ {o.get('restaurant_name', 'Restaurant')} | {format_inr(o.get('total_amount', 0))} | {o.get('status').upper()}" for o in orders if o["_id"] == oid), oid),
                key="selected_order_action"
            )
            
            if selected_order_id:
                try:
                    order_detail = get_order_by_id(selected_order_id)
                    col_view, col_edit = st.columns(2)
                    
                    with col_view:
                        st.markdown("#### 📄 Record Details")
                        u_info = order_detail.get("user") or {}
                        r_info = order_detail.get("restaurant") or {}
                        
                        st.markdown(f"""
                        <div class="glass-card" style="border-left: 4px solid #3B82F6;">
                            <p><b>Order ID:</b> <code>{order_detail['_id']}</code></p>
                            <p><b>Status:</b> <b>{order_detail['status'].upper()}</b></p>
                            <p><b>Customer:</b> {u_info.get('name', 'N/A')} ({u_info.get('phone', 'N/A')})</p>
                            <p><b>Restaurant:</b> {r_info.get('name', 'N/A')} ({r_info.get('cuisine', 'N/A')} - {r_info.get('location', 'N/A')})</p>
                            <p><b>Delivery Fee:</b> {format_inr(order_detail['delivery_fee'])}</p>
                            <p><b>Total Amount:</b> {format_inr(order_detail['total_amount'])}</p>
                            <p><b>Placed At:</b> {order_detail['created_at']}</p>
                            <p><b>Delivered At:</b> {order_detail.get('delivered_at') or 'Fulfilling / In Transit'}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        items_list = order_detail.get("items", [])
                        st.markdown("##### 🛒 Ordered Items:")
                        if items_list:
                            df_items = pd.DataFrame(items_list)
                            df_items["subtotal"] = df_items["quantity"] * df_items["price"]
                            df_items["price"] = df_items["price"].apply(format_inr)
                            df_items["subtotal"] = df_items["subtotal"].apply(format_inr)
                            df_items.columns = ["Item Name", "Quantity", "Unit Price (₹)", "Subtotal (₹)"]
                            st.dataframe(df_items, use_container_width=True, hide_index=True)
                            
                        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                        st.markdown("#### 🗑️ Delete Record")
                        confirm_del = st.checkbox("I confirm I want to permanently delete this order record", key=f"del_chk_ord_{selected_order_id}")
                        if st.button("Delete Order Record", type="secondary", disabled=not confirm_del, key=f"del_btn_ord_{selected_order_id}"):
                            try:
                                delete_order(selected_order_id)
                                st.success("Order record successfully deleted!")
                                st.rerun()
                            except (ValidationError, NotFoundError) as e:
                                st.error(str(e))
                                
                    with col_edit:
                        st.markdown("#### ✏️ Edit Record")
                        with st.form("edit_order_form"):
                            current_status = order_detail["status"]
                            edit_status = st.selectbox(
                                "Fulfillment Status",
                                options=ORDER_STATUSES,
                                index=ORDER_STATUSES.index(current_status) if current_status in ORDER_STATUSES else 0
                            )
                            edit_del_fee = st.number_input("Delivery Fee (₹)", min_value=0.0, value=float(order_detail["delivery_fee"]), step=10.0)
                            edit_total = st.number_input("Total Amount (₹)", min_value=0.0, value=float(order_detail["total_amount"]), step=50.0)
                            
                            submit_edit = st.form_submit_button("💾 Save Changes", type="primary")
                            if submit_edit:
                                try:
                                    update_order(selected_order_id, {
                                        "user_id": str(order_detail["user_id"]),
                                        "restaurant_id": str(order_detail["restaurant_id"]),
                                        "items": order_detail["items"],
                                        "delivery_fee": edit_del_fee,
                                        "total_amount": edit_total,
                                        "status": edit_status
                                    })
                                    st.success("Order updated successfully!")
                                    st.rerun()
                                except (ValidationError, NotFoundError) as e:
                                    st.error(str(e))
                except Exception as ex:
                    st.error(f"Error fetching order details: {ex}")
        else:
            render_empty_state("No Orders Found", "No orders match your filter criteria.", "🍔")

    # -------------------------------------------------------------
    # TAB 2: ADD NEW
    # -------------------------------------------------------------
    with tab_create:
        st.subheader("Add a New Food Order")
        if not users_dropdown or not restaurants_dropdown:
            st.warning("Please ensure customer accounts and restaurants exist before adding food orders.")
            return
            
        with st.form("add_order_form"):
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                add_user = st.selectbox(
                    "Select User *",
                    options=[u["_id"] for u in users_dropdown],
                    format_func=lambda uid: next((u["label"] for u in users_dropdown if u["_id"] == uid), uid),
                    key="add_order_user"
                )
            with col_c2:
                add_rest = st.selectbox(
                    "Select Restaurant *",
                    options=[r["_id"] for r in restaurants_dropdown],
                    format_func=lambda rid: next((r["label"] for r in restaurants_dropdown if r["_id"] == rid), rid),
                    key="add_order_rest"
                )
                
            st.markdown("#### 🍜 Food Items")
            item_name = st.text_input("Food Item Name *", value="Chicken Biryani", key="add_item_name")
            col_q, col_p = st.columns(2)
            with col_q:
                quantity = st.number_input("Quantity *", min_value=1, max_value=20, value=2, step=1, key="add_item_qty")
            with col_p:
                unit_price = st.number_input("Price per item in ₹ *", min_value=0.0, value=320.0, step=10.0, key="add_item_price")
                
            col_df, col_st = st.columns(2)
            with col_df:
                delivery_fee = st.number_input("Delivery Fee in ₹", min_value=0.0, value=40.0, step=5.0, key="add_order_fee")
            with col_st:
                order_status = st.selectbox("Initial Order Status", options=ORDER_STATUSES, index=0, key="add_order_status")
                
            # Automatic subtotal and total computation
            subtotal = quantity * unit_price
            total_amount = subtotal + delivery_fee
            
            st.info(f"**Computed Subtotal:** {format_inr(subtotal)} + **Delivery Fee:** {format_inr(delivery_fee)} = **Final Total:** {format_inr(total_amount)}")
            
            submit_order = st.form_submit_button("➕ Add Order", type="primary")
            if submit_order:
                try:
                    items_payload = [{
                        "item_name": str(item_name or "").strip(),
                        "quantity": int(quantity),
                        "price": float(unit_price)
                    }]
                    new_ord = create_order({
                        "user_id": add_user,
                        "restaurant_id": add_rest,
                        "items": items_payload,
                        "delivery_fee": float(delivery_fee),
                        "total_amount": float(total_amount),
                        "status": order_status
                    })
                    st.session_state["recent_added_order"] = new_ord
                    st.session_state["orders_success_toast"] = (
                        f"✅ **Food order successfully added & verified in MongoDB!** ID: `{new_ord['_id']}` | "
                        f"Items: {quantity}x {item_name} | Total: {format_inr(new_ord['total_amount'])}"
                    )
                    st.rerun()
                except (ValidationError, NotFoundError) as ve:
                    st.error(f"⚠️ Validation Error: {ve}")
                except Exception as ex:
                    import traceback
                    traceback.print_exc()
                    st.error(f"🔴 Database Operation Error: {type(ex).__name__}: {ex}")
                    print(f"DATABASE WRITE ERROR in add_order: {ex}")
                    
        if "recent_added_order" in st.session_state:
            last_ord = st.session_state["recent_added_order"]
            st.markdown(f"""
            <div style="background: #EFF6FF; border: 1px solid #93C5FD; border-radius: 8px; padding: 0.75rem 1rem; margin-top: 1rem;">
                <p style="color: #1E40AF; font-weight: 600; margin: 0;">✨ Last Added Order (Verified in MongoDB):</p>
                <p style="color: #1F2937; margin: 0.25rem 0 0 0; font-size: 0.88rem;">
                    <b>ID:</b> <code>{last_ord['_id']}</code> | <b>Total:</b> {format_inr(last_ord['total_amount'])} | <b>Status:</b> {last_ord['status'].upper()}<br>
                    <b>Delivery Fee:</b> {format_inr(last_ord['delivery_fee'])} | <b>Items Count:</b> {len(last_ord.get('items', []))}
                </p>
            </div>
            """, unsafe_allow_html=True)


# Fallback execution if loaded directly
if __name__ == "__main__" or not st.session_state.get("_running_via_app", False):
    render()
