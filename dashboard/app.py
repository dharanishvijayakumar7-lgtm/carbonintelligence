"""
Carbon Intelligence Dashboard

Interactive Streamlit dashboard with:
- Total carbon footprint overview
- Emissions by category (pie chart)
- Monthly trends (line chart)
- Department comparisons (bar chart)
- AI chatbot interface
- Reduction recommendations
- File upload for data ingestion
- Report generation
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import date, datetime

from database import get_connection
from models.emission_factors import seed_emission_factors
from engine.carbon_estimator import (
    get_total_emissions,
    get_emissions_by_category,
    get_emissions_by_department,
    get_monthly_trends,
    process_all_unprocessed,
)
from engine.insights_engine import generate_insights
from engine.prediction import predict_emissions
from engine.report_generator import generate_monthly_report
from chatbot.chat_engine import chat
from ingestion.csv_loader import load_csv_bytes, insert_activities

# ── Page Configuration ────────────────────────────────────────────────

st.set_page_config(
    page_title="🌍 Carbon Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1B5E20;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-top: -10px;
        margin-bottom: 30px;
    }
    .metric-card {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        padding: 20px;
        border-radius: 12px;
        border-left: 4px solid #2E7D32;
    }
    .stMetric label {
        font-size: 0.9rem !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    .insight-card {
        background: #FFF3E0;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #FF9800;
        margin-bottom: 10px;
    }
    .chat-user {
        background: #E3F2FD;
        padding: 10px 15px;
        border-radius: 10px;
        margin: 5px 0;
    }
    .chat-bot {
        background: #F1F8E9;
        padding: 10px 15px;
        border-radius: 10px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/earth-planet.png", width=60)
        st.markdown("## 🌍 Carbon Intelligence")
        st.markdown("*AI-Powered Sustainability*")
        st.markdown("---")

        page = st.radio(
            "Navigate",
            [
                "📊 Dashboard",
                "💬 Chat Assistant",
                "📤 Upload Data",
                "💡 Insights",
                "📈 Forecast",
                "📋 Reports",
            ],
            label_visibility="collapsed",
        )

        st.markdown("---")

        # Quick stats
        try:
            summary = get_total_emissions()
            st.metric("Total Emissions", f"{summary['total_co2e_tonnes']:,.2f} t CO₂e")
            st.metric("Records", f"{summary['record_count']:,}")
        except Exception:
            st.info("No data loaded yet")

        st.markdown("---")
        st.markdown(
            "**Data Sources:** EPA, DEFRA, IPCC, IEA\n\n"
            "**Version:** 1.0.0"
        )

    return page


# ── Dashboard Page ────────────────────────────────────────────────────

def render_dashboard():
    st.markdown('<p class="main-header">📊 Carbon Footprint Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Real-time emission monitoring and analysis</p>', unsafe_allow_html=True)

    summary = get_total_emissions()
    total_kg = summary["total_co2e_kg"]
    total_t = summary["total_co2e_tonnes"]

    if total_kg == 0:
        st.warning("⚠️ No emission data found. Go to **Upload Data** to import your data, or run `python scripts/seed_data.py` to load sample data.")
        return

    # ── KPI Cards ─────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "🌍 Total Emissions",
            f"{total_t:,.2f} t",
            help="Total carbon dioxide equivalent in tonnes",
        )
    with col2:
        categories = len(summary.get("by_category", {}))
        st.metric("📂 Categories", categories)
    with col3:
        departments = len(summary.get("by_department", {}))
        st.metric("🏢 Departments", departments)
    with col4:
        st.metric("📄 Records", f"{summary['record_count']:,}")

    st.markdown("---")

    # ── Charts Row 1 ──────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Emissions by Category")
        if summary.get("by_category"):
            cat_df = pd.DataFrame(
                list(summary["by_category"].items()),
                columns=["Category", "CO₂e (kg)"],
            )
            cat_df["Category"] = cat_df["Category"].str.title()

            fig = px.pie(
                cat_df,
                values="CO₂e (kg)",
                names="Category",
                color_discrete_sequence=px.colors.qualitative.Set2,
                hole=0.4,
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            fig.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2),
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Emissions by Scope")
        if summary.get("by_scope"):
            scope_labels = {1: "Scope 1 (Direct)", 2: "Scope 2 (Electricity)", 3: "Scope 3 (Value Chain)"}
            scope_df = pd.DataFrame(
                [(scope_labels.get(k, f"Scope {k}"), v) for k, v in sorted(summary["by_scope"].items())],
                columns=["Scope", "CO₂e (kg)"],
            )

            fig = px.bar(
                scope_df,
                x="Scope",
                y="CO₂e (kg)",
                color="Scope",
                color_discrete_sequence=["#EF5350", "#FFA726", "#66BB6A"],
            )
            fig.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=False,
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)

    # ── Charts Row 2 ──────────────────────────────────────────────────
    col_left2, col_right2 = st.columns(2)

    with col_left2:
        st.subheader("Monthly Trends")
        trends = get_monthly_trends()
        if trends:
            trend_df = pd.DataFrame(trends)
            fig = px.line(
                trend_df,
                x="month",
                y="co2e_kg",
                markers=True,
                labels={"month": "Month", "co2e_kg": "CO₂e (kg)"},
            )
            fig.update_traces(
                line=dict(color="#2E7D32", width=3),
                marker=dict(size=8, color="#1B5E20"),
            )
            fig.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_right2:
        st.subheader("Department Comparison")
        depts = get_emissions_by_department()
        if depts:
            dept_df = pd.DataFrame(depts)
            fig = px.bar(
                dept_df,
                x="department",
                y="co2e_kg",
                color="department",
                labels={"department": "Department", "co2e_kg": "CO₂e (kg)"},
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=False,
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)

    # ── Detailed Category Breakdown ───────────────────────────────────
    st.markdown("---")
    st.subheader("Detailed Category Breakdown")

    categories_detail = get_emissions_by_category()
    if categories_detail:
        detail_df = pd.DataFrame(categories_detail)
        detail_df["category"] = detail_df["category"].str.title()
        detail_df["subcategory"] = detail_df["subcategory"].str.replace("_", " ").str.title()
        detail_df.columns = ["Category", "Subcategory", "CO₂e (kg)", "Records"]

        fig = px.treemap(
            detail_df,
            path=["Category", "Subcategory"],
            values="CO₂e (kg)",
            color="CO₂e (kg)",
            color_continuous_scale="Greens",
        )
        fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=450)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(detail_df, use_container_width=True, hide_index=True)


# ── Chat Assistant Page ───────────────────────────────────────────────

def render_chat():
    st.markdown('<p class="main-header">💬 Carbon Intelligence Assistant</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Ask questions about your carbon footprint in natural language</p>', unsafe_allow_html=True)

    # Example queries
    with st.expander("💡 Example Questions", expanded=False):
        cols = st.columns(2)
        examples = [
            "What is our total carbon footprint?",
            "Show emissions by category",
            "Which department has the most emissions?",
            "How can we reduce emissions by 20%?",
            "Show monthly trends",
            "Compare January and February",
            "What was our footprint last month?",
            "Show forecast",
        ]
        for i, ex in enumerate(examples):
            with cols[i % 2]:
                if st.button(f"📝 {ex}", key=f"ex_{i}", use_container_width=True):
                    st.session_state.chat_input = ex

    # Chat history
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # Display chat history
    for msg in st.session_state.chat_messages:
        if msg["role"] == "user":
            st.chat_message("user").markdown(msg["content"])
        else:
            st.chat_message("assistant").markdown(msg["content"])

    # Chat input
    default_input = st.session_state.pop("chat_input", "")
    user_input = st.chat_input("Ask about your carbon footprint...")

    query = default_input or user_input
    if query:
        # Show user message
        st.chat_message("user").markdown(query)
        st.session_state.chat_messages.append({"role": "user", "content": query})

        # Get response
        with st.spinner("Analyzing..."):
            response = chat(query)

        # Show response
        st.chat_message("assistant").markdown(response["answer"])
        st.session_state.chat_messages.append({"role": "assistant", "content": response["answer"]})

        # Show data visualization if available
        if response.get("data"):
            data = response["data"]
            if "trends" in data:
                trend_df = pd.DataFrame(data["trends"])
                fig = px.line(trend_df, x="month", y="co2e_kg", markers=True)
                fig.update_traces(line=dict(color="#2E7D32", width=2))
                st.plotly_chart(fig, use_container_width=True)

            if "categories" in data:
                cat_df = pd.DataFrame(data["categories"])
                fig = px.bar(cat_df, x="category", y="co2e_kg", color="subcategory")
                st.plotly_chart(fig, use_container_width=True)

            if "departments" in data:
                dept_df = pd.DataFrame(data["departments"])
                fig = px.pie(dept_df, values="co2e_kg", names="department", hole=0.3)
                st.plotly_chart(fig, use_container_width=True)

    if st.button("🗑️ Clear Chat", use_container_width=False):
        st.session_state.chat_messages = []
        st.rerun()


# ── Upload Page ───────────────────────────────────────────────────────

def render_upload():
    st.markdown('<p class="main-header">📤 Upload Data</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Import CSV, Excel, or PDF files to track emissions</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["csv", "xlsx", "xls", "pdf"],
            help="Upload CSV, Excel, or PDF utility bills",
        )

        category_override = st.selectbox(
            "Category Override (optional)",
            ["Auto-detect", "electricity", "travel", "commuting", "cloud", "equipment", "waste"],
        )

        department = st.text_input("Department (optional)", placeholder="e.g., Engineering, Marketing")

    with col2:
        st.markdown("### 📋 Expected CSV Format")
        st.markdown("""
        | Column | Required | Example |
        |--------|----------|---------|
        | category | ✅ | electricity |
        | quantity | ✅ | 4500 |
        | unit | ❌ | kWh |
        | date | ❌ | 2025-01-15 |
        | subcategory | ❌ | grid_us |
        | department | ❌ | Engineering |
        """)

    if uploaded_file and st.button("🚀 Upload & Process", type="primary", use_container_width=True):
        with st.spinner("Processing file..."):
            try:
                content = uploaded_file.read()
                filename = uploaded_file.name

                if filename.lower().endswith(".pdf"):
                    from ingestion.pdf_parser import parse_pdf_bytes
                    records = parse_pdf_bytes(content, filename)
                else:
                    records = load_csv_bytes(content, filename)

                # Apply overrides
                if category_override != "Auto-detect":
                    for r in records:
                        r["category"] = category_override
                if department:
                    for r in records:
                        r["department"] = department

                records_count = insert_activities(records)
                emissions_count = process_all_unprocessed()

                st.success(
                    f"✅ Successfully imported **{records_count}** records and "
                    f"calculated **{emissions_count}** emission entries from `{filename}`"
                )

                # Show preview
                if records:
                    st.subheader("Imported Records Preview")
                    preview_df = pd.DataFrame(records[:20])
                    st.dataframe(preview_df, use_container_width=True, hide_index=True)

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


# ── Insights Page ─────────────────────────────────────────────────────

def render_insights():
    st.markdown('<p class="main-header">💡 AI Reduction Insights</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Personalized recommendations to reduce your carbon footprint</p>', unsafe_allow_html=True)

    insights_data = generate_insights()
    insights = insights_data.get("insights", [])

    if not insights:
        st.info("No specific recommendations at this time. Upload more data for personalized insights!")
        return

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💡 Recommendations", len(insights))
    with col2:
        total_red = insights_data["total_potential_reduction_kg"]
        st.metric("🎯 Potential Reduction", f"{total_red:,.0f} kg CO₂e")
    with col3:
        total_pct = insights_data["total_potential_reduction_pct"]
        st.metric("📉 Reduction Potential", f"{total_pct:.1f}%")

    st.markdown("---")

    # Reduction waterfall chart
    st.subheader("Reduction Potential by Recommendation")
    insight_df = pd.DataFrame(insights)
    fig = px.bar(
        insight_df,
        x="title",
        y="estimated_reduction_kg",
        color="priority",
        color_discrete_map={"high": "#EF5350", "medium": "#FFA726", "low": "#66BB6A"},
        labels={"title": "Recommendation", "estimated_reduction_kg": "Potential Reduction (kg CO₂e)"},
    )
    fig.update_layout(xaxis_tickangle=-45, margin=dict(t=20, b=120), height=450)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Detail cards
    for i, insight in enumerate(insights, 1):
        priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(insight["priority"], "⚪")
        with st.expander(
            f"{priority_emoji} {i}. {insight['title']} — "
            f"Save {insight['estimated_reduction_kg']:,.0f} kg CO₂e",
            expanded=(i <= 3),
        ):
            st.markdown(f"**Category:** {insight['category'].title()}")
            st.markdown(f"**Priority:** {insight['priority'].upper()}")
            st.markdown(f"**Potential Reduction:** {insight['estimated_reduction_kg']:,.0f} kg CO₂e "
                        f"({insight['estimated_reduction_pct']:.0f}% of category)")
            st.markdown("---")
            st.markdown(insight["description"])


# ── Forecast Page ─────────────────────────────────────────────────────

def render_forecast():
    st.markdown('<p class="main-header">📈 Emission Forecast</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-powered emission predictions and trend analysis</p>', unsafe_allow_html=True)

    months_ahead = st.slider("Forecast horizon (months)", 3, 24, 6)

    pred = predict_emissions(months_ahead=months_ahead)

    if pred.get("trend") == "insufficient_data":
        st.warning("Not enough data for predictions. Need at least 2 months of historical data.")
        return

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        trend_emoji = {"increasing": "📈", "decreasing": "📉", "stable": "➡️"}.get(pred["trend"], "❓")
        st.metric("Trend", f"{trend_emoji} {pred['trend'].title()}")
    with col2:
        st.metric("Monthly Average", f"{pred['monthly_average_kg']:,.0f} kg")
    with col3:
        st.metric("Annual Forecast", f"{pred['annual_forecast_tonnes']:,.2f} t")
    with col4:
        st.metric("Monthly Change", f"{pred['slope_kg_per_month']:+,.0f} kg/mo")

    st.markdown("---")

    # Combined chart
    historical = pred.get("historical", [])
    predicted = pred.get("predicted", [])

    if historical or predicted:
        hist_df = pd.DataFrame(historical)
        hist_df["type"] = "Historical"

        pred_df = pd.DataFrame(predicted)
        pred_df["type"] = "Predicted"

        # Connect the two series
        if not hist_df.empty and not pred_df.empty:
            connector = pd.DataFrame([{
                "month": hist_df.iloc[-1]["month"],
                "co2e_kg": hist_df.iloc[-1]["co2e_kg"],
                "type": "Predicted",
            }])
            pred_df = pd.concat([connector, pred_df], ignore_index=True)

        combined = pd.concat([hist_df, pred_df], ignore_index=True)

        fig = px.line(
            combined,
            x="month",
            y="co2e_kg",
            color="type",
            markers=True,
            color_discrete_map={"Historical": "#2E7D32", "Predicted": "#FF9800"},
            labels={"month": "Month", "co2e_kg": "CO₂e (kg)", "type": ""},
        )
        fig.update_layout(
            margin=dict(t=20, b=20, l=20, r=20),
            height=450,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)


# ── Reports Page ──────────────────────────────────────────────────────

def render_reports():
    st.markdown('<p class="main-header">📋 Sustainability Reports</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Generate and download automated sustainability reports</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Generate Report")

        report_type = st.radio("Report Type", ["Monthly", "Quarterly"])

        if report_type == "Monthly":
            year = st.selectbox("Year", [2025, 2024, 2026], index=0)
            month = st.selectbox("Month", list(range(1, 13)), format_func=lambda x: date(2025, x, 1).strftime("%B"))
            period = f"{year}-{month:02d}"
        else:
            year = st.selectbox("Year", [2025, 2024, 2026], index=0, key="q_year")
            quarter = st.selectbox("Quarter", [1, 2, 3, 4], format_func=lambda x: f"Q{x}")
            period = f"{year}-Q{quarter}"

        if st.button("📊 Generate Report", type="primary", use_container_width=True):
            with st.spinner("Generating report..."):
                try:
                    report = generate_monthly_report(period)
                    st.success(f"✅ Report generated for {period}")
                    st.session_state.current_report = report
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    with col2:
        st.subheader("Report Preview")

        report = st.session_state.get("current_report")
        if report:
            summary = report["summary"]
            st.markdown(f"### 📊 Report: {report['period']}")
            st.markdown(f"**Organization:** {report['organization']}")
            st.markdown(f"**Total Emissions:** {summary['total_co2e_kg']:,.1f} kg CO₂e "
                        f"({summary['total_co2e_tonnes']:,.2f} tonnes)")

            st.markdown("#### By Category")
            if summary.get("by_category"):
                cat_df = pd.DataFrame(
                    list(summary["by_category"].items()),
                    columns=["Category", "CO₂e (kg)"],
                )
                st.dataframe(cat_df, use_container_width=True, hide_index=True)

            st.markdown("#### Recommendations")
            st.markdown(report.get("recommendations", "No recommendations."))

            # Download button
            report_path = report.get("report_file")
            if report_path and Path(report_path).exists():
                report_content = Path(report_path).read_text()
                st.download_button(
                    "📥 Download Full Report (Markdown)",
                    report_content,
                    file_name=f"sustainability_report_{report['period']}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
        else:
            st.info("Select a period and click 'Generate Report' to create a sustainability report.")


# ── Main App ──────────────────────────────────────────────────────────

def main():
    page = render_sidebar()

    if page == "📊 Dashboard":
        render_dashboard()
    elif page == "💬 Chat Assistant":
        render_chat()
    elif page == "📤 Upload Data":
        render_upload()
    elif page == "💡 Insights":
        render_insights()
    elif page == "📈 Forecast":
        render_forecast()
    elif page == "📋 Reports":
        render_reports()


if __name__ == "__main__":
    main()
