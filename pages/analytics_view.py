"""
Aggregation Analytics Page.
In-depth business intelligence powered by multi-stage MongoDB aggregation pipelines ($group, $match, $lookup, $unwind, $facet).
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from services.analytics_service import (
    get_dashboard_kpis,
    get_revenue_trends,
    get_status_breakdown,
    get_revenue_by_cuisine,
    get_order_volume_by_day,
    get_customer_activity_summaries
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
    render_header(
        "Analytics",
        "Deep analytical insights computed via multi-stage MongoDB pipelines ($group, $lookup, $unwind, and $facet).",
        "🧠"
    )
    
    try:
        kpis = get_dashboard_kpis()
    except Exception as e:
        st.error(f"Error executing aggregation pipelines: {e}")
        kpis = {
            "total_platform_revenue": 0.0, "avg_fare": 0.0, "avg_order_value": 0.0,
            "completed_rides": 0, "delivered_orders": 0, "total_rides": 0, "total_orders": 0
        }
        
    # Overview Metrics Row
    c1, c2, c3, c4 = st.columns(4)
    render_kpi(c1, "Platform Gross Revenue", format_inr(kpis['total_platform_revenue']), "Excludes cancelled orders", "#0D9488")
    render_kpi(c2, "Average Ride Fare", format_inr(kpis['avg_fare']), f"{kpis['completed_rides']} completed rides", "#3B82F6")
    render_kpi(c3, "Average Order Value (AOV)", format_inr(kpis['avg_order_value']), f"{kpis['delivered_orders']} delivered orders", "#F59E0B")
    render_kpi(c4, "Total Platform Trips", f"{kpis['total_rides'] + kpis['total_orders']:,}", "Rides + Food Deliveries", "#10B981")

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    
    # Pipeline 1: Multi-Granularity Revenue Trends
    st.subheader("1. Revenue Trends & Grouping ($dateToString & $group)")
    st.markdown("""
    **MongoDB Pipeline Architecture:**  
    `$match: {status: 'completed' / 'delivered'}` ➡️  
    `$group: {_id: {$dateToString: {format: '%Y-%m-%d', date: '$created_at'}}, revenue: {$sum: '$fare'}}` ➡️  
    `$sort: {_id: 1}` ➡️ `$project`
    """)
    
    col_g1, col_g2 = st.columns([1, 3])
    with col_g1:
        gran = st.radio("Time Window", ["daily", "weekly", "monthly"], horizontal=True, key="analytics_gran")
        
    try:
        trends = get_revenue_trends(period=gran)
        r_df = pd.DataFrame(trends.get("rides", []))
        o_df = pd.DataFrame(trends.get("orders", []))
        
        fig_rev = go.Figure()
        if not r_df.empty:
            fig_rev.add_trace(go.Bar(
                x=r_df["period"], y=r_df["revenue"],
                name="Rides Revenue", marker_color="#0D9488",
                hovertemplate="Period: %{x}<br>Revenue: ₹%{y:,.2f}<extra></extra>"
            ))
        if not o_df.empty:
            fig_rev.add_trace(go.Bar(
                x=o_df["period"], y=o_df["revenue"],
                name="Food Orders Revenue", marker_color="#3B82F6",
                hovertemplate="Period: %{x}<br>Revenue: ₹%{y:,.2f}<extra></extra>"
            ))
        layout = get_plotly_theme_layout()
        layout.update(
            barmode="stack",
            height=340,
            xaxis_title=f"Period ({gran.capitalize()})",
            yaxis_title="Total Revenue (₹)"
        )
        fig_rev.update_layout(**layout)
        st.plotly_chart(fig_rev, use_container_width=True)
    except Exception as ex:
        st.warning(f"Error computing revenue trends: {ex}")

    st.markdown("---")

    # Pipeline 2: Combined Activity Volume by Day ($facet)
    st.subheader("2. Combined Order & Ride Volume by Day ($facet stage)")
    st.markdown("""
    **MongoDB Pipeline Architecture:** Demonstrates the powerful `$facet` stage, processing multiple independent aggregation pipelines on the database engine concurrently in a single network round-trip.
    """)
    try:
        volume_days = get_order_volume_by_day()
        if volume_days:
            vol_df = pd.DataFrame(volume_days)
            fig_vol = go.Figure()
            fig_vol.add_trace(go.Scatter(
                x=vol_df["date"], y=vol_df["rides"],
                name="Rides Volume", mode="lines+markers",
                line=dict(color="#0D9488", width=2.5)
            ))
            fig_vol.add_trace(go.Scatter(
                x=vol_df["date"], y=vol_df["food_orders"],
                name="Food Orders Volume", mode="lines+markers",
                line=dict(color="#3B82F6", width=2.5)
            ))
            layout = get_plotly_theme_layout()
            layout.update(
                height=320,
                hovermode="x unified",
                xaxis_title="Date",
                yaxis_title="Volume Count"
            )
            fig_vol.update_layout(**layout)
            st.plotly_chart(fig_vol, use_container_width=True)
        else:
            render_empty_state("No Activity Records", "No daily transactions recorded yet.")
    except Exception as ex:
        st.warning(f"Error executing $facet volume query: {ex}")

    st.markdown("---")

    # Pipeline 3: Revenue by Cuisine ($lookup & $unwind)
    st.subheader("3. Food Sales Revenue by Cuisine ($lookup & $unwind)")
    st.markdown("""
    **MongoDB Pipeline Architecture:**  
    `$match: {status: 'delivered'}` ➡️  
    `$lookup: {from: 'restaurants', localField: 'restaurant_id', foreignField: '_id', as: 'restaurant'}` ➡️  
    `$unwind: '$restaurant'` ➡️  
    `$group: {_id: '$restaurant.cuisine', total_revenue: {$sum: '$total_amount'}, order_count: {$sum: 1}}` ➡️  
    `$sort: {total_revenue: -1}`
    """)
    try:
        cuisine_data = get_revenue_by_cuisine()
        if cuisine_data:
            df_c = pd.DataFrame(cuisine_data)
            fig_c = px.bar(
                df_c, x="cuisine", y="total_revenue",
                text="total_revenue",
                color="order_count",
                labels={"cuisine": "Cuisine", "total_revenue": "Total Revenue (₹)", "order_count": "Orders"},
                color_continuous_scale="Teal"
            )
            fig_c.update_traces(
                texttemplate='₹%{text:,.2f}',
                textposition='outside',
                hovertemplate="Cuisine: %{x}<br>Revenue: ₹%{y:,.2f}<br>Orders: %{marker.color}<extra></extra>"
            )
            layout = get_plotly_theme_layout()
            layout.update(height=340)
            fig_c.update_layout(**layout)
            st.plotly_chart(fig_c, use_container_width=True)
        else:
            render_empty_state("No Delivered Orders", "Delivered orders joined with restaurant cuisines will appear here.")
    except Exception as ex:
        st.warning(f"Error computing cuisine revenue: {ex}")

    st.markdown("---")

    # Pipeline 4: Customer Activity Profiles ($lookup & $filter)
    st.subheader("4. Comprehensive Customer Activity Profiles ($lookup & $filter)")
    st.markdown("""
    **MongoDB Pipeline Architecture:** Joins each user with their corresponding `rides` and `food_orders`, computes array lengths with `$size`, and filters completed transactions with `$filter`.
    """)
    try:
        cust_activity = get_customer_activity_summaries(limit=15)
        if cust_activity:
            df_ca = pd.DataFrame(cust_activity)[["name", "email", "total_rides", "completed_rides", "total_orders", "delivered_orders", "total_activity"]]
            df_ca.columns = ["Customer Name", "Email", "Total Rides", "Completed Rides", "Total Orders", "Delivered Orders", "Combined Activity"]
            st.dataframe(df_ca, use_container_width=True, hide_index=True)
        else:
            render_empty_state("No Customer Data", "Customer records will appear once accounts are registered.")
    except Exception as ex:
        st.warning(f"Error retrieving customer activity summaries: {ex}")


# Fallback execution if loaded directly
if __name__ == "__main__" or not st.session_state.get("_running_via_app", False):
    render()
