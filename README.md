# 🌍 Carbon Intelligence System

An AI-driven carbon footprint estimation, tracking, and reduction platform for organizations with **zero budget, no IoT sensors, and no sustainability experts**.

## 🎯 What It Does

- **Estimates** carbon emissions from electricity bills, cloud usage, travel, commuting, purchases, and waste
- **Tracks** emissions over time with automatic data imports
- **Analyzes** emissions by category, department, and time period
- **Recommends** actionable reduction strategies using AI
- **Reports** monthly sustainability summaries automatically
- **Chats** — ask natural language questions about your carbon footprint

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CARBON INTELLIGENCE SYSTEM                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Data Ingest  │  │  AI Chatbot  │  │  Dashboard   │       │
│  │  CSV/PDF/XLS  │  │  NL Interface│  │  Streamlit   │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                  │                  │               │
│  ┌──────▼──────────────────▼──────────────────▼───────┐      │
│  │              FastAPI Backend                        │      │
│  │  ┌─────────┐ ┌──────────┐ ┌────────────────────┐  │      │
│  │  │Emission │ │ Insights │ │   Report Generator  │  │      │
│  │  │Engine   │ │ Engine   │ │                     │  │      │
│  │  └────┬────┘ └────┬─────┘ └─────────┬──────────┘  │      │
│  │       │            │                  │             │      │
│  │  ┌────▼────────────▼──────────────────▼──────┐     │      │
│  │  │           DuckDB Database                  │     │      │
│  │  │  emissions │ factors │ reports │ surveys   │     │      │
│  │  └───────────────────────────────────────────┘     │      │
│  └────────────────────────────────────────────────────┘      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
carbonintelligence/
├── README.md
├── requirements.txt
├── setup.py
├── config.py                    # Configuration
├── main.py                      # FastAPI application entry
├── database.py                  # DuckDB database setup
├── models/
│   ├── schemas.py               # Pydantic models
│   └── emission_factors.py      # EPA/IPCC emission factors
├── ingestion/
│   ├── csv_loader.py            # CSV/Excel parser
│   ├── pdf_parser.py            # PDF bill parser
│   └── cloud_billing.py         # Cloud provider billing
├── engine/
│   ├── carbon_estimator.py      # Core emission calculator
│   ├── insights_engine.py       # AI recommendations
│   ├── prediction.py            # Emission forecasting
│   └── report_generator.py      # Monthly report generation
├── chatbot/
│   └── chat_engine.py           # Natural language interface
├── api/
│   ├── routes_data.py           # Data ingestion endpoints
│   ├── routes_emissions.py      # Emission query endpoints
│   ├── routes_chat.py           # Chatbot endpoints
│   └── routes_reports.py        # Report endpoints
├── dashboard/
│   └── app.py                   # Streamlit dashboard
├── data/
│   └── sample/                  # Example datasets
│       ├── electricity_bills.csv
│       ├── travel_expenses.csv
│       ├── employee_commute.csv
│       ├── cloud_usage.csv
│       ├── office_purchases.csv
│       └── waste_records.csv
├── reports/                     # Generated reports
├── tests/
│   └── test_estimator.py
└── scripts/
    ├── seed_data.py             # Load sample data
    └── generate_report.py       # CLI report generation
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd carbonintelligence
python -m venv venv
source venv/bin/activate    # macOS/Linux
pip install -r requirements.txt
```

### 2. Initialize Database & Load Sample Data

```bash
python scripts/seed_data.py
```

### 3. Start the API Server

```bash
uvicorn main:app --reload --port 8000
```

### 4. Launch the Dashboard

```bash
streamlit run dashboard/app.py --server.port 8501
```

### 5. Open in Browser

- **Dashboard**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **Chat API**: POST http://localhost:8000/api/chat

## 💬 Example Chat Queries

```
"What was our carbon footprint last month?"
"Which department produced the most emissions?"
"How can we reduce emissions by 20%?"
"Compare emissions between January and February"
"Show me travel emissions breakdown"
"What's our electricity carbon intensity?"
```

## 📊 Emission Categories

| Category | Data Source | Method |
|---|---|---|
| Electricity | Bills (CSV/PDF) | kWh × Grid Factor |
| Business Travel | Expense reports | Distance × Mode Factor |
| Commuting | Employee surveys | Distance × Days × Mode Factor |
| Cloud Computing | Cloud billing | Usage × PUE × Grid Factor |
| Office Equipment | Purchase records | Lifecycle emission factors |
| Waste | Waste records | Weight × Waste Type Factor |

## 🔬 Emission Factors Used

- **EPA** — US Electricity Grid Factors (2024)
- **IPCC** — AR6 Global Warming Potentials
- **DEFRA** — UK Government Conversion Factors
- **IEA** — International Energy Agency

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Database | DuckDB |
| Dashboard | Streamlit + Plotly |
| AI/Chat | LangChain + Local LLM fallback |
| Data Processing | Pandas |
| PDF Parsing | pdfplumber |
| Forecasting | scikit-learn |

## 📋 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/data/upload` | Upload CSV/Excel/PDF |
| GET | `/api/emissions/summary` | Total emissions summary |
| GET | `/api/emissions/by-category` | Emissions by category |
| GET | `/api/emissions/by-department` | Emissions by department |
| GET | `/api/emissions/monthly` | Monthly trends |
| POST | `/api/chat` | Natural language query |
| GET | `/api/insights` | AI recommendations |
| POST | `/api/reports/generate` | Generate monthly report |
| GET | `/api/reports/latest` | Get latest report |

## 🌱 Zero-Budget Design

- ✅ All open-source tools
- ✅ Runs 100% locally
- ✅ No paid APIs required
- ✅ No IoT sensors needed
- ✅ No sustainability expertise required
- ✅ Uses only existing organizational data

## 📄 License

MIT License — Free for all organizations to use.
