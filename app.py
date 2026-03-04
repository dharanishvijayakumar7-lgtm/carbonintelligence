"""
Carbon Intelligence System — Complete Flask Application
Single-file implementation for reliability
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import duckdb
import os
from datetime import datetime, timedelta
import random

# ---------------------------------------------------------------------------
# Flask App Setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)

DB_PATH = os.path.join(os.path.dirname(__file__), "carbon_flask.duckdb")

# ---------------------------------------------------------------------------
# Database Helpers
# ---------------------------------------------------------------------------
def get_db():
    """Get database connection."""
    return duckdb.connect(DB_PATH)


def init_db():
    """Initialize database tables."""
    conn = get_db()
    
    # Emissions table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS emissions (
            id INTEGER PRIMARY KEY,
            date DATE NOT NULL,
            category VARCHAR NOT NULL,
            subcategory VARCHAR,
            department VARCHAR,
            description VARCHAR,
            quantity DOUBLE NOT NULL,
            unit VARCHAR NOT NULL,
            emission_factor DOUBLE NOT NULL,
            co2e_kg DOUBLE NOT NULL,
            scope INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Emission factors table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS emission_factors (
            id INTEGER PRIMARY KEY,
            category VARCHAR NOT NULL,
            subcategory VARCHAR,
            factor_value DOUBLE NOT NULL,
            unit VARCHAR NOT NULL,
            source VARCHAR,
            region VARCHAR DEFAULT 'global'
        )
    """)
    
    conn.close()


def seed_db():
    """Seed database with sample data."""
    conn = get_db()
    
    # Check if already seeded
    count = conn.execute("SELECT COUNT(*) FROM emissions").fetchone()[0]
    if count > 0:
        print(f"Database already has {count} records. Skipping seed.")
        conn.close()
        return
    
    # Seed emission factors
    factors = [
        (1, 'electricity', 'grid_us', 0.417, 'kg CO2e/kWh', 'EPA', 'US'),
        (2, 'electricity', 'grid_eu', 0.276, 'kg CO2e/kWh', 'EEA', 'EU'),
        (3, 'electricity', 'grid_uk', 0.212, 'kg CO2e/kWh', 'DEFRA', 'UK'),
        (4, 'electricity', 'renewable', 0.0, 'kg CO2e/kWh', 'IPCC', 'global'),
        (5, 'travel', 'flight_short', 0.255, 'kg CO2e/km', 'DEFRA', 'global'),
        (6, 'travel', 'flight_long', 0.195, 'kg CO2e/km', 'DEFRA', 'global'),
        (7, 'travel', 'train', 0.041, 'kg CO2e/km', 'DEFRA', 'global'),
        (8, 'travel', 'car_petrol', 0.171, 'kg CO2e/km', 'DEFRA', 'global'),
        (9, 'travel', 'car_diesel', 0.168, 'kg CO2e/km', 'DEFRA', 'global'),
        (10, 'travel', 'car_electric', 0.053, 'kg CO2e/km', 'DEFRA', 'global'),
        (11, 'commuting', 'car', 0.171, 'kg CO2e/km', 'DEFRA', 'global'),
        (12, 'commuting', 'bus', 0.089, 'kg CO2e/km', 'DEFRA', 'global'),
        (13, 'commuting', 'bike', 0.0, 'kg CO2e/km', 'IPCC', 'global'),
        (14, 'cloud', 'compute', 0.0005, 'kg CO2e/vCPU-hr', 'IEA', 'global'),
        (15, 'cloud', 'storage', 0.0001, 'kg CO2e/GB-month', 'IEA', 'global'),
        (16, 'waste', 'general', 0.587, 'kg CO2e/kg', 'EPA', 'global'),
        (17, 'waste', 'recycled', 0.021, 'kg CO2e/kg', 'EPA', 'global'),
        (18, 'equipment', 'laptop', 300.0, 'kg CO2e/unit', 'Dell', 'global'),
        (19, 'equipment', 'monitor', 350.0, 'kg CO2e/unit', 'Dell', 'global'),
        (20, 'equipment', 'phone', 70.0, 'kg CO2e/unit', 'Apple', 'global'),
    ]
    
    conn.executemany(
        "INSERT INTO emission_factors VALUES (?, ?, ?, ?, ?, ?, ?)",
        factors
    )
    
    # Generate 12 months of emission data
    departments = ["Engineering", "Marketing", "Sales", "Operations", "HR", "Finance"]
    records = []
    rec_id = 1
    
    for month_offset in range(12):
        record_date = datetime(2025, 1, 1) + timedelta(days=30 * month_offset)
        date_str = record_date.strftime('%Y-%m-%d')
        
        # Electricity per department
        for dept in departments:
            kwh = random.uniform(1500, 4000)
            factor = 0.417
            records.append((
                rec_id, date_str, 'electricity', 'grid_us', dept,
                f'Monthly electricity - {dept}', round(kwh, 1), 'kWh',
                factor, round(kwh * factor, 2), 2, datetime.now()
            ))
            rec_id += 1
        
        # Business travel
        for _ in range(random.randint(2, 5)):
            dept = random.choice(departments)
            mode = random.choice(['flight_short', 'flight_long', 'train'])
            km = random.uniform(300, 5000)
            factors_map = {'flight_short': 0.255, 'flight_long': 0.195, 'train': 0.041}
            factor = factors_map[mode]
            records.append((
                rec_id, date_str, 'travel', mode, dept,
                f'Business travel - {mode}', round(km, 1), 'km',
                factor, round(km * factor, 2), 3, datetime.now()
            ))
            rec_id += 1
        
        # Commuting per department
        for dept in departments:
            km = random.uniform(500, 3000)
            factor = 0.171
            records.append((
                rec_id, date_str, 'commuting', 'car', dept,
                f'Employee commuting - {dept}', round(km, 1), 'km',
                factor, round(km * factor, 2), 3, datetime.now()
            ))
            rec_id += 1
        
        # Cloud computing
        for dept in ['Engineering', 'Marketing', 'Operations']:
            hours = random.uniform(1000, 8000)
            factor = 0.0005
            records.append((
                rec_id, date_str, 'cloud', 'compute', dept,
                f'Cloud compute - {dept}', round(hours, 1), 'vCPU-hours',
                factor, round(hours * factor, 2), 3, datetime.now()
            ))
            rec_id += 1
        
        # Waste
        kg_waste = random.uniform(100, 400)
        factor = 0.587
        records.append((
            rec_id, date_str, 'waste', 'general', 'Operations',
            'Office waste', round(kg_waste, 1), 'kg',
            factor, round(kg_waste * factor, 2), 3, datetime.now()
        ))
        rec_id += 1
    
    conn.executemany(
        "INSERT INTO emissions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        records
    )
    
    total = conn.execute("SELECT SUM(co2e_kg) FROM emissions").fetchone()[0]
    print(f"✅ Seeded {rec_id - 1} emission records | Total: {total:,.0f} kg CO₂e")
    conn.close()


# ---------------------------------------------------------------------------
# API Routes — Health
# ---------------------------------------------------------------------------
@app.route('/')
def home():
    """Home page with API info."""
    return jsonify({
        "service": "Carbon Intelligence System",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "summary": "/api/emissions/summary",
            "by_category": "/api/emissions/by-category",
            "by_department": "/api/emissions/by-department",
            "monthly": "/api/emissions/monthly",
            "records": "/api/emissions/records",
            "insights": "/api/emissions/insights",
            "chat": "/api/chat"
        }
    })


@app.route('/api/health')
def health():
    """Health check endpoint."""
    try:
        conn = get_db()
        count = conn.execute("SELECT COUNT(*) FROM emissions").fetchone()[0]
        conn.close()
        return jsonify({"status": "ok", "database": "connected", "records": count})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ---------------------------------------------------------------------------
# API Routes — Emissions
# ---------------------------------------------------------------------------
@app.route('/api/emissions/summary')
def emissions_summary():
    """Get total emissions summary."""
    try:
        conn = get_db()
        result = conn.execute(
            "SELECT COALESCE(SUM(co2e_kg), 0) as total FROM emissions"
        ).fetchone()
        total_kg = result[0]
        conn.close()
        
        return jsonify({
            "total_co2e_kg": round(total_kg, 2),
            "total_co2e_tonnes": round(total_kg / 1000, 2)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/emissions/by-category')
def emissions_by_category():
    """Get emissions grouped by category."""
    try:
        conn = get_db()
        rows = conn.execute("""
            SELECT category, SUM(co2e_kg) as total
            FROM emissions
            GROUP BY category
            ORDER BY total DESC
        """).fetchall()
        conn.close()
        
        return jsonify([
            {"category": row[0], "co2e_kg": round(row[1], 2)}
            for row in rows
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/emissions/by-department')
def emissions_by_department():
    """Get emissions grouped by department."""
    try:
        conn = get_db()
        rows = conn.execute("""
            SELECT department, SUM(co2e_kg) as total
            FROM emissions
            GROUP BY department
            ORDER BY total DESC
        """).fetchall()
        conn.close()
        
        return jsonify([
            {"department": row[0], "co2e_kg": round(row[1], 2)}
            for row in rows
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/emissions/monthly')
def emissions_monthly():
    """Get monthly emission trends."""
    try:
        conn = get_db()
        rows = conn.execute("""
            SELECT strftime('%Y-%m', date) as month, SUM(co2e_kg) as total
            FROM emissions
            GROUP BY month
            ORDER BY month
        """).fetchall()
        conn.close()
        
        return jsonify([
            {"month": row[0], "co2e_kg": round(row[1], 2)}
            for row in rows
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/emissions/records')
def emissions_records():
    """Get individual emission records."""
    try:
        conn = get_db()
        limit = request.args.get('limit', 100, type=int)
        rows = conn.execute(f"""
            SELECT id, date, category, subcategory, department, 
                   description, quantity, unit, emission_factor, co2e_kg, scope
            FROM emissions
            ORDER BY date DESC
            LIMIT {limit}
        """).fetchall()
        conn.close()
        
        cols = ["id", "date", "category", "subcategory", "department",
                "description", "quantity", "unit", "emission_factor", "co2e_kg", "scope"]
        return jsonify([dict(zip(cols, row)) for row in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# API Routes — Insights
# ---------------------------------------------------------------------------
@app.route('/api/emissions/insights')
def emissions_insights():
    """Generate AI-powered reduction insights."""
    try:
        conn = get_db()
        
        # Get emissions by category
        rows = conn.execute("""
            SELECT category, SUM(co2e_kg) as total
            FROM emissions
            GROUP BY category
        """).fetchall()
        conn.close()
        
        categories = {row[0]: row[1] for row in rows}
        total = sum(categories.values())
        
        insights = []
        
        # Electricity insights
        if categories.get('electricity', 0) > total * 0.25:
            pct = categories['electricity'] / total * 100
            insights.append({
                "priority": "high",
                "category": "electricity",
                "title": "Switch to Renewable Energy",
                "description": f"Electricity accounts for {pct:.0f}% of your emissions. "
                              "Switching to a renewable energy provider could reduce this by 80-100%. "
                              "Consider solar panels or green energy tariffs.",
                "estimated_reduction_pct": 40,
                "estimated_savings_kg": round(categories['electricity'] * 0.4, 0)
            })
        
        # Travel insights
        if categories.get('travel', 0) > 0:
            insights.append({
                "priority": "high",
                "category": "travel",
                "title": "Reduce Business Air Travel",
                "description": "Replace flights with video conferencing where possible. "
                              "When travel is necessary, prefer trains over flights for distances under 500km. "
                              "Each avoided flight saves 200-500 kg CO₂e.",
                "estimated_reduction_pct": 30,
                "estimated_savings_kg": round(categories.get('travel', 0) * 0.3, 0)
            })
        
        # Commuting insights
        if categories.get('commuting', 0) > 0:
            insights.append({
                "priority": "medium",
                "category": "commuting",
                "title": "Implement Hybrid Work Policy",
                "description": "Allow 2-3 remote work days per week to reduce commuting emissions by 40-60%. "
                              "Encourage carpooling, cycling, or public transit for in-office days.",
                "estimated_reduction_pct": 50,
                "estimated_savings_kg": round(categories.get('commuting', 0) * 0.5, 0)
            })
        
        # Cloud insights
        if categories.get('cloud', 0) > 0:
            insights.append({
                "priority": "medium",
                "category": "cloud",
                "title": "Optimize Cloud Infrastructure",
                "description": "Right-size instances, enable auto-scaling, and shut down idle resources. "
                              "Choose cloud regions powered by renewable energy (e.g., AWS eu-north-1, GCP europe-north1).",
                "estimated_reduction_pct": 25,
                "estimated_savings_kg": round(categories.get('cloud', 0) * 0.25, 0)
            })
        
        # Waste insights
        if categories.get('waste', 0) > 0:
            insights.append({
                "priority": "low",
                "category": "waste",
                "title": "Improve Waste Management",
                "description": "Increase recycling rates to 80%+. Eliminate single-use plastics. "
                              "Compost food waste. This can reduce waste emissions by 50-70%.",
                "estimated_reduction_pct": 15,
                "estimated_savings_kg": round(categories.get('waste', 0) * 0.15, 0)
            })
        
        # Always add equipment insight
        insights.append({
            "priority": "low",
            "category": "equipment",
            "title": "Extend Equipment Lifecycle",
            "description": "Keep laptops and devices for 5+ years instead of 3. "
                          "Buy refurbished when possible. Each avoided laptop saves ~300 kg CO₂e.",
            "estimated_reduction_pct": 10,
            "estimated_savings_kg": 500
        })
        
        return jsonify(insights)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# API Routes — Chat
# ---------------------------------------------------------------------------
@app.route('/api/chat', methods=['POST'])
def chat():
    """Natural language chat interface."""
    try:
        data = request.get_json()
        message = data.get('message', '').lower()
        
        conn = get_db()
        
        # Get summary data for responses
        total = conn.execute("SELECT SUM(co2e_kg) FROM emissions").fetchone()[0] or 0
        
        categories = conn.execute("""
            SELECT category, SUM(co2e_kg) as total
            FROM emissions GROUP BY category ORDER BY total DESC
        """).fetchall()
        
        departments = conn.execute("""
            SELECT department, SUM(co2e_kg) as total
            FROM emissions GROUP BY department ORDER BY total DESC
        """).fetchall()
        
        monthly = conn.execute("""
            SELECT strftime('%Y-%m', date) as month, SUM(co2e_kg) as total
            FROM emissions GROUP BY month ORDER BY month DESC LIMIT 3
        """).fetchall()
        
        conn.close()
        
        # Intent detection and response
        if any(w in message for w in ['total', 'footprint', 'overall', 'all']):
            response = f"🌍 Your total carbon footprint is **{total/1000:,.1f} tonnes CO₂e** ({total:,.0f} kg)."
        
        elif any(w in message for w in ['category', 'categories', 'breakdown', 'biggest']):
            lines = [f"• **{c[0].title()}**: {c[1]:,.0f} kg ({c[1]/total*100:.1f}%)" for c in categories]
            response = "📊 **Emissions by category:**\n" + "\n".join(lines)
        
        elif any(w in message for w in ['department', 'team', 'dept']):
            lines = [f"• **{d[0]}**: {d[1]:,.0f} kg" for d in departments]
            response = "🏢 **Emissions by department:**\n" + "\n".join(lines)
        
        elif any(w in message for w in ['month', 'trend', 'time', 'history']):
            lines = [f"• **{m[0]}**: {m[1]:,.0f} kg" for m in monthly]
            response = "📈 **Recent monthly emissions:**\n" + "\n".join(lines)
        
        elif any(w in message for w in ['reduce', 'cut', 'lower', 'decrease', 'improve', 'save', 'recommend', 'suggest', 'tip']):
            response = """💡 **Top recommendations to reduce emissions:**

1. **Switch to renewable energy** — Could cut electricity emissions by 80%+
2. **Reduce air travel** — Use video calls instead, prefer trains
3. **Hybrid work policy** — 2-3 remote days reduces commuting 50%
4. **Optimize cloud** — Right-size instances, use green regions
5. **Extend equipment life** — Keep laptops 5+ years"""
        
        elif any(w in message for w in ['hello', 'hi', 'hey', 'help']):
            response = """👋 Hi! I'm your Carbon Intelligence assistant. I can help you understand your emissions.

**Try asking:**
• "What is our total footprint?"
• "Show emissions by category"
• "Which department has the most emissions?"
• "How can we reduce our emissions?"
• "What were last month's trends?" """
        
        else:
            response = """🤔 I can help you with:
• **Total footprint** — "What's our total?"
• **By category** — "Show breakdown by category"
• **By department** — "Which team emits most?"
• **Trends** — "Show monthly trends"
• **Reduction tips** — "How can we reduce?"

Try rephrasing your question!"""
        
        return jsonify({"response": response})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# API Routes — Emission Factors
# ---------------------------------------------------------------------------
@app.route('/api/factors')
def get_factors():
    """Get all emission factors."""
    try:
        conn = get_db()
        rows = conn.execute("""
            SELECT id, category, subcategory, factor_value, unit, source, region
            FROM emission_factors
            ORDER BY category, subcategory
        """).fetchall()
        conn.close()
        
        cols = ["id", "category", "subcategory", "factor_value", "unit", "source", "region"]
        return jsonify([dict(zip(cols, row)) for row in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Initialize and Run
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    print("🌍 Carbon Intelligence System — Flask Backend")
    print("=" * 50)
    
    # Initialize database
    init_db()
    seed_db()
    
    print("\n📡 Starting server on http://127.0.0.1:8000")
    print("📊 Dashboard: http://127.0.0.1:8501 (run Streamlit separately)")
    print("📖 API Docs: http://127.0.0.1:8000/")
    print("\nPress Ctrl+C to stop\n")
    
    app.run(host='127.0.0.1', port=8000, debug=True)