"""
🌍 Carbon Intelligence Dashboard
Beautiful, simple carbon footprint tracking
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_BASE = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="🌍 Carbon Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    div[data-testid="stSidebarNav"] { padding-top: 1rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #f1f5f9;
        border-radius: 8px;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# API Helpers
# ---------------------------------------------------------------------------
def api_get(path: str):
    """GET request to API."""
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.ConnectionError:
        return None
    except requests.HTTPError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def api_post(path: str, data: dict):
    """POST request to API."""
    try:
        r = requests.post(f"{API_BASE}{path}", json=data, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🌍 Carbon Intelligence")
    st.caption("Zero-budget carbon tracking")
    st.markdown("---")
    
    # Check API health
    health = api_get("/api/health")
    
    if health is None:
        st.error("❌ API Offline")
        st.markdown("""
        **Start the API:**
        ```bash
        python start.py
        ```
        """)
        st.stop()
    elif isinstance(health, dict) and "error" in health:
        st.warning(f"⚠️ {health['error']}")
    else:
        st.success(f"✅ Connected")
        if isinstance(health, dict):
            st.caption(f"{health.get('records', 0)} emission records")
    
    st.markdown("---")
    
    # Navigation
    page = st.radio(
        "📍 Navigate",
        ["📊 Overview", "📈 Trends", "🏢 Departments", "💡 Insights", "💬 Chat", "📋 Data"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.caption("v1.0 • Made with ❤️")


# ---------------------------------------------------------------------------
# 📊 OVERVIEW PAGE
# ---------------------------------------------------------------------------
if page == "📊 Overview":
    st.title("📊 Carbon Footprint Overview")
    st.caption("Real-time emissions across your organization")
    
    # Fetch all data
    summary = api_get("/api/emissions/summary")
    by_category = api_get("/api/emissions/by-category")
    by_month = api_get("/api/emissions/monthly")
    
    # Handle errors
    if summary and isinstance(summary, dict) and "error" not in summary:
        # Top metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Emissions",
                f"{summary.get('total_co2e_tonnes', 0):,.1f} t",
                help="Total CO₂ equivalent in tonnes"
            )
        
        with col2:
            st.metric(
                "Total (kg)",
                f"{summary.get('total_co2e_kg', 0):,.0f}",
                help="Total CO₂ equivalent in kilograms"
            )
        
        with col3:
            cat_count = len(by_category) if isinstance(by_category, list) else 0
            st.metric("Categories", cat_count)
        
        with col4:
            if isinstance(by_category, list) and len(by_category) > 0:
                top_cat = by_category[0].get('category', 'N/A').title()
            else:
                top_cat = "N/A"
            st.metric("Top Source", top_cat)
    else:
        st.error("Could not load summary data. Make sure the API is running.")
    
    st.markdown("---")
    
    # Charts
    col_left, col_right = st.columns(2)
    
    # Pie chart - emissions by category
    with col_left:
        if isinstance(by_category, list) and len(by_category) > 0:
            df_cat = pd.DataFrame(by_category)
            fig = px.pie(
                df_cat,
                names="category",
                values="co2e_kg",
                title="🥧 Emissions by Category",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(showlegend=False, margin=dict(t=50, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No category data available")
    
    # Bar chart - monthly trend
    with col_right:
        if isinstance(by_month, list) and len(by_month) > 0:
            df_month = pd.DataFrame(by_month)
            fig = px.bar(
                df_month,
                x="month",
                y="co2e_kg",
                title="📅 Monthly Emissions",
                color_discrete_sequence=["#10b981"]
            )
            fig.update_layout(
                xaxis_title="", 
                yaxis_title="kg CO₂e",
                margin=dict(t=50, b=20, l=20, r=20)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No monthly data available")
    
    # Full-width category bar
    if isinstance(by_category, list) and len(by_category) > 0:
        st.markdown("### 📊 Category Breakdown")
        df_cat = pd.DataFrame(by_category)
        fig = px.bar(
            df_cat,
            x="category",
            y="co2e_kg",
            color="category",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_layout(
            showlegend=False,
            xaxis_title="",
            yaxis_title="kg CO₂e",
            margin=dict(t=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# 📈 TRENDS PAGE
# ---------------------------------------------------------------------------
elif page == "📈 Trends":
    st.title("📈 Emission Trends")
    st.caption("Track your carbon footprint over time")
    
    by_month = api_get("/api/emissions/monthly")
    
    if isinstance(by_month, list) and len(by_month) > 0:
        df = pd.DataFrame(by_month)
        
        # Line chart
        fig = px.line(
            df,
            x="month",
            y="co2e_kg",
            markers=True,
            title="Monthly Emission Trend"
        )
        fig.update_traces(line_color="#3b82f6", marker_size=10)
        fig.update_layout(xaxis_title="Month", yaxis_title="kg CO₂e")
        st.plotly_chart(fig, use_container_width=True)
        
        # Month comparison
        if len(df) >= 2:
            st.markdown("### 📊 Month-over-Month")
            c1, c2, c3 = st.columns(3)
            
            latest = df.iloc[-1]["co2e_kg"]
            prev = df.iloc[-2]["co2e_kg"]
            delta = latest - prev
            pct = (delta / prev * 100) if prev > 0 else 0
            
            c1.metric("Latest Month", f"{latest:,.0f} kg", f"{df.iloc[-1]['month']}")
            c2.metric("Previous Month", f"{prev:,.0f} kg", f"{df.iloc[-2]['month']}")
            c3.metric(
                "Change",
                f"{delta:+,.0f} kg",
                f"{pct:+.1f}%",
                delta_color="inverse"
            )
        
        # Data table
        st.markdown("### 📋 Monthly Data")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No trend data available yet. Add some emission records first.")


# ---------------------------------------------------------------------------
# 🏢 DEPARTMENTS PAGE
# ---------------------------------------------------------------------------
elif page == "🏢 Departments":
    st.title("🏢 Department Comparison")
    st.caption("See which teams contribute most to your footprint")
    
    by_dept = api_get("/api/emissions/by-department")
    
    if isinstance(by_dept, list) and len(by_dept) > 0:
        df = pd.DataFrame(by_dept)
        
        # Bar chart
        fig = px.bar(
            df,
            x="department",
            y="co2e_kg",
            color="department",
            title="Emissions by Department",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="kg CO₂e")
        st.plotly_chart(fig, use_container_width=True)
        
        # Treemap
        fig_tree = px.treemap(
            df,
            path=["department"],
            values="co2e_kg",
            title="Department Treemap",
            color="co2e_kg",
            color_continuous_scale="RdYlGn_r"
        )
        fig_tree.update_layout(margin=dict(t=50, b=20, l=20, r=20))
        st.plotly_chart(fig_tree, use_container_width=True)
        
        # Ranking
        st.markdown("### 🏆 Department Ranking")
        total = df['co2e_kg'].sum()
        for i, row in df.iterrows():
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}."
            pct = row['co2e_kg'] / total * 100 if total > 0 else 0
            st.write(f"{medal} **{row['department']}** — {row['co2e_kg']:,.0f} kg ({pct:.1f}%)")
    else:
        st.info("No department data available.")


# ---------------------------------------------------------------------------
# 💡 INSIGHTS PAGE
# ---------------------------------------------------------------------------
elif page == "💡 Insights":
    st.title("💡 AI Reduction Insights")
    st.caption("Smart recommendations to cut your carbon footprint")
    
    response = api_get("/api/emissions/insights")
    
    # Handle both dict and list responses
    insights = []
    total_potential = 0
    
    if response:
        if isinstance(response, dict) and "error" not in response:
            insights = response.get("insights", [])
            total_potential = response.get("total_potential_reduction_kg", 0)
        elif isinstance(response, list):
            insights = response
            total_potential = sum(
                i.get("estimated_savings_kg", i.get("estimated_reduction_kg", 0)) 
                for i in insights if isinstance(i, dict)
            )
    
    if insights and len(insights) > 0:
        # Summary banner
        st.success(f"💰 **Total potential savings: {total_potential:,.0f} kg CO₂e**")
        st.markdown("---")
        
        # Display each insight
        for i, item in enumerate(insights):
            if not isinstance(item, dict):
                continue
                
            priority = item.get("priority", "medium")
            icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
            
            # Get reduction percentage (try multiple key names)
            reduction = item.get("estimated_reduction_pct", 
                       item.get("potential_reduction_pct", 0))
            
            # Get savings (try multiple key names)
            savings = item.get("estimated_savings_kg", 
                      item.get("estimated_reduction_kg", 0))
            
            title = item.get("title", "Recommendation")
            description = item.get("description", "")
            category = item.get("category", "general")
            
            with st.expander(f"{icon} **{title}** — ↓{reduction}%", expanded=(i < 2)):
                st.write(description)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Category", category.title())
                col2.metric("Reduction", f"{reduction}%")
                col3.metric("Savings", f"{savings:,.0f} kg")
                
                # Progress bar
                st.progress(min(reduction / 100, 1.0))
    else:
        st.info("No insights available. Add more emission data first.")


# ---------------------------------------------------------------------------
# 💬 CHAT PAGE
# ---------------------------------------------------------------------------
elif page == "💬 Chat":
    st.title("💬 Carbon Assistant")
    st.caption("Ask questions about your emissions in natural language")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": """👋 **Hi! I'm your Carbon Intelligence assistant.**

I can help you understand your carbon footprint. Try asking:

• "What is our total carbon footprint?"
• "Which category emits the most?"
• "Show emissions by department"
• "How can we reduce our emissions?"
• "What were the monthly trends?"
"""
        }]
    
    # Display chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about your carbon footprint..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get response from API
        with st.spinner("Thinking..."):
            response = api_post("/api/chat", {"message": prompt})
        
        if response and isinstance(response, dict) and "error" not in response:
            answer = response.get("response", response.get("answer", "I couldn't process that."))
        else:
            answer = "Sorry, I couldn't connect to the API. Please try again."
        
        # Add assistant response
        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)
    
    # Clear button
    st.markdown("---")
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = [st.session_state.messages[0]]
        st.rerun()


# ---------------------------------------------------------------------------
# 📋 DATA PAGE
# ---------------------------------------------------------------------------
elif page == "📋 Data":
    st.title("📋 Emission Records")
    st.caption("View and export your raw emission data")
    
    records = api_get("/api/emissions/records?limit=500")
    
    if isinstance(records, list) and len(records) > 0:
        df = pd.DataFrame(records)
        
        # Summary
        total = df["co2e_kg"].sum() if "co2e_kg" in df.columns else 0
        st.info(f"📊 **{len(df)} records** | Total: **{total:,.0f} kg CO₂e**")
        
        # Filters
        col1, col2 = st.columns(2)
        
        with col1:
            categories = ["All"] + sorted(df["category"].unique().tolist()) if "category" in df.columns else ["All"]
            selected_cat = st.selectbox("🏷️ Category", categories)
        
        with col2:
            departments = ["All"] + sorted(df["department"].dropna().unique().tolist()) if "department" in df.columns else ["All"]
            selected_dept = st.selectbox("🏢 Department", departments)
        
        # Apply filters
        df_filtered = df.copy()
        if selected_cat != "All":
            df_filtered = df_filtered[df_filtered["category"] == selected_cat]
        if selected_dept != "All":
            df_filtered = df_filtered[df_filtered["department"] == selected_dept]
        
        st.markdown(f"**Showing {len(df_filtered)} records**")
        
        # Display table
        st.dataframe(df_filtered, use_container_width=True, height=400, hide_index=True)
        
        # Download
        csv = df_filtered.to_csv(index=False)
        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name="carbon_emissions.csv",
            mime="text/csv"
        )
    else:
        st.info("No records found. Make sure the database has been seeded.")
        st.markdown("""
        **To seed the database, run:**
        ```bash
        python scripts/seed_data.py
        ```
        """)
