"""
Dashboard Overview Page.
Displays executive KPI cards, daily activity charts, revenue trends in Indian Rupees (₹),
status distributions, and top performers.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timezone, timedelta

from services.analytics_service import (
    get_dashboard_kpis,
    get_revenue_trends,
    get_status_breakdown,
    get_revenue_by_cuisine,
    get_order_volume_by_day
)
from services.query_service import (
    query_top_drivers_by_completed_rides,
    query_top_restaurants_by_revenue
)
from ui_components import (
    render_header,
    render_kpi,
    render_empty_state,
    get_plotly_theme_layout,
    inject_custom_css,
    format_inr
)


def render():
    inject_custom_css()
    
    # Header with Refresh and Live Demo Badge
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown("""
        <div class="dashboard-header">
            <div class="header-content-wrapper">
                <div class="header-icon-box" style="background: linear-gradient(135deg, #0F9D8A 0%, #3B82F6 100%); color: #fff; font-size: 1.6rem; box-shadow: 0 4px 14px rgba(15, 157, 138, 0.35);">
                    🚖
                </div>
                <div>
                    <div class="main-title" style="display: flex; align-items: center; gap: 0.6rem;">
                        <span>SwiftRoute &amp; Bite Dashboard</span>
                        <span style="font-size: 0.72rem; font-weight: 700; background: linear-gradient(135deg, #0F9D8A 0%, #3B82F6 100%); color: #fff; padding: 0.2rem 0.6rem; border-radius: 9999px; letter-spacing: 0.05em; text-transform: uppercase;">Live Demo</span>
                    </div>
                    <div class="sub-title">
                        Comprehensive Indian mobility, food delivery logistics, and revenue intelligence powered by MongoDB.
                    </div>
                </div>
            </div>
            <div class="header-gradient-bar"></div>
        </div>
        """, unsafe_allow_html=True)
    with col_h2:
        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Refresh Data", type="secondary", use_container_width=True):
            st.rerun()

    # 1. KPI Cards (Total Users, Total Drivers, Total Rides, Total Food Orders, Ride Revenue, Food Order Revenue)
    try:
        kpis = get_dashboard_kpis()
    except Exception as e:
        st.error(f"⚠️ Unable to query dashboard KPIs from MongoDB: {e}")
        kpis = {
            "total_users": 0, "total_rides": 0, "total_orders": 0, "completed_rides": 0,
            "delivered_orders": 0, "ride_revenue": 0.0, "order_revenue": 0.0,
            "total_platform_revenue": 0.0, "active_drivers": 0, "total_drivers": 0, "total_restaurants": 0
        }

    # Top KPI Row (6 Core Metrics with format_inr)
    r1, r2, r3, r4, r5, r6 = st.columns(6)
    render_kpi(r1, "Total Users", f"{kpis['total_users']:,}", "Registered accounts", "#3B82F6")
    render_kpi(r2, "Total Drivers", f"{kpis['total_drivers']:,}", f"{kpis.get('active_drivers', 0)} active now", "#0F9D8A")
    render_kpi(r3, "Total Rides", f"{kpis['total_rides']:,}", f"{kpis.get('completed_rides', 0)} completed", "#10B981")
    render_kpi(r4, "Total Orders", f"{kpis['total_orders']:,}", f"{kpis.get('delivered_orders', 0)} delivered", "#8B5CF6")
    render_kpi(r5, "Ride Revenue", format_inr(kpis['ride_revenue']), "Excl. cancelled", "#F59E0B")
    render_kpi(r6, "Food Revenue", format_inr(kpis['order_revenue']), "Excl. cancelled", "#EC4899")

    # If completely empty, show friendly prompt
    if kpis["total_rides"] == 0 and kpis["total_orders"] == 0:
        render_empty_state(
            "No Operational Data Found",
            "The database currently has no rides or orders. Use the 'Database Seeder & Reset' tool in the sidebar to populate realistic sample data.",
            "🌱"
        )
        return

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 2. Charts Section: Daily Activity & Revenue Trends
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.markdown("<div class='kpi-title'>📅 Daily Activity (Rides & Food Orders)</div>", unsafe_allow_html=True)
        try:
            vol_data = get_order_volume_by_day()
            if vol_data:
                df_vol = pd.DataFrame(vol_data)
                fig_act = go.Figure()
                fig_act.add_trace(go.Bar(
                    x=df_vol["date"], y=df_vol["rides"],
                    name="Rides", marker=dict(color="#0F9D8A", cornerradius=4)
                ))
                fig_act.add_trace(go.Bar(
                    x=df_vol["date"], y=df_vol["food_orders"],
                    name="Food Orders", marker=dict(color="#3B82F6", cornerradius=4)
                ))
                layout = get_plotly_theme_layout()
                layout.update(
                    barmode="group",
                    height=290,
                    xaxis_title="Date",
                    yaxis_title="Volume Count"
                )
                fig_act.update_layout(**layout)
                st.plotly_chart(fig_act, use_container_width=True)
            else:
                render_empty_state("No Daily Activity", "No transaction records available for daily volume.")
        except Exception as e:
            st.warning(f"Error rendering daily activity: {e}")

    with col_c2:
        st.markdown("<div class='kpi-title'>📈 Revenue Trends Over Time (₹ INR)</div>", unsafe_allow_html=True)
        try:
            trends = get_revenue_trends(period="daily")
            r_trend = pd.DataFrame(trends.get("rides", []))
            o_trend = pd.DataFrame(trends.get("orders", []))
            
            fig_rev = go.Figure()
            if not r_trend.empty:
                fig_rev.add_trace(go.Scatter(
                    x=r_trend["period"], y=r_trend["revenue"],
                    name="Ride Revenue (₹)", mode="lines+markers",
                    line=dict(color="#0F9D8A", width=2.5),
                    marker=dict(size=6),
                    hovertemplate="%{x}<br>Ride Revenue: ₹%{y:,.2f}<extra></extra>"
                ))
            if not o_trend.empty:
                fig_rev.add_trace(go.Scatter(
                    x=o_trend["period"], y=o_trend["revenue"],
                    name="Food Revenue (₹)", mode="lines+markers",
                    line=dict(color="#F59E0B", width=2.5),
                    marker=dict(size=6),
                    hovertemplate="%{x}<br>Food Revenue: ₹%{y:,.2f}<extra></extra>"
                ))
            layout = get_plotly_theme_layout()
            layout.update(
                height=290,
                xaxis_title="Timeline",
                yaxis_title="Revenue (₹)",
                hovermode="x unified"
            )
            fig_rev.update_layout(**layout)
            st.plotly_chart(fig_rev, use_container_width=True)
        except Exception as e:
            st.warning(f"Error rendering revenue trends: {e}")

    # 3. Status Distributions
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    col_d1, col_d2 = st.columns(2)
    
    status_data = get_status_breakdown()
    with col_d1:
        st.markdown("<div class='kpi-title'>🚕 Ride Status Distribution</div>", unsafe_allow_html=True)
        rides_stat = status_data.get("rides", [])
        if rides_stat:
            df_rs = pd.DataFrame(rides_stat)
            fig_rs = px.pie(
                df_rs, values="count", names="status",
                hole=0.55,
                color="status",
                color_discrete_map={
                    "completed": "#0F9D8A",
                    "in_progress": "#3B82F6",
                    "accepted": "#8B5CF6",
                    "requested": "#F59E0B",
                    "cancelled": "#EF4444"
                }
            )
            layout = get_plotly_theme_layout()
            layout.update(height=265)
            fig_rs.update_layout(**layout)
            st.plotly_chart(fig_rs, use_container_width=True)
        else:
            render_empty_state("No Rides", "No rides recorded yet.")

    with col_d2:
        st.markdown("<div class='kpi-title'>🍔 Food Order Status Distribution</div>", unsafe_allow_html=True)
        orders_stat = status_data.get("orders", [])
        if orders_stat:
            df_os = pd.DataFrame(orders_stat)
            fig_os = px.pie(
                df_os, values="count", names="status",
                hole=0.55,
                color="status",
                color_discrete_map={
                    "delivered": "#0F9D8A",
                    "out_for_delivery": "#3B82F6",
                    "preparing": "#F59E0B",
                    "placed": "#8B5CF6",
                    "cancelled": "#EF4444"
                }
            )
            layout = get_plotly_theme_layout()
            layout.update(height=265)
            fig_os.update_layout(**layout)
            st.plotly_chart(fig_os, use_container_width=True)
        else:
            render_empty_state("No Orders", "No food orders recorded yet.")

    # 4. Top Performers (Drivers & Restaurants)
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        st.markdown("<div class='kpi-title'>🏆 Top-Performing Drivers</div>", unsafe_allow_html=True)
        top_drivers = query_top_drivers_by_completed_rides(limit=5)
        if top_drivers:
            df_td = pd.DataFrame(top_drivers)[["driver_name", "vehicle_type", "rating", "completed_rides", "total_fare_earned"]]
            df_td["total_fare_earned"] = df_td["total_fare_earned"].apply(format_inr)
            df_td.columns = ["Driver", "Vehicle", "Rating ⭐", "Completed Trips", "Total Earnings (₹)"]
            st.dataframe(df_td, use_container_width=True, hide_index=True)
        else:
            render_empty_state("No Driver Records", "Completed ride data will appear here once trips are recorded.")

    with col_p2:
        st.markdown("<div class='kpi-title'>🍴 Top-Performing Restaurants</div>", unsafe_allow_html=True)
        top_rests = query_top_restaurants_by_revenue(limit=5)
        if top_rests:
            df_tr = pd.DataFrame(top_rests)[["restaurant_name", "cuisine", "rating", "delivered_orders", "gross_revenue"]]
            df_tr["gross_revenue"] = df_tr["gross_revenue"].apply(format_inr)
            df_tr.columns = ["Restaurant", "Cuisine", "Rating ⭐", "Delivered Orders", "Revenue (₹)"]
            st.dataframe(df_tr, use_container_width=True, hide_index=True)
        else:
            render_empty_state("No Restaurant Records", "Delivered order data will appear here once orders are fulfilled.")


# Fallback execution if loaded directly
if __name__ == "__main__" or not st.session_state.get("_running_via_app", False):
    render()
