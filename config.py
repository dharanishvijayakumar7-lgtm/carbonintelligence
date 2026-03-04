"""
Carbon Intelligence System — Configuration
"""
import os
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SAMPLE_DIR = DATA_DIR / "sample"
UPLOAD_DIR = DATA_DIR / "uploads"
REPORTS_DIR = BASE_DIR / "reports"
DB_PATH = BASE_DIR / "carbon.duckdb"

# Create directories
for d in [DATA_DIR, SAMPLE_DIR, UPLOAD_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Database ──────────────────────────────────────────────────────────
DATABASE_URL = str(DB_PATH)

# ── API ───────────────────────────────────────────────────────────────
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# ── LLM (optional — system works without it) ─────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")  # ignored if no key

# ── Dashboard ─────────────────────────────────────────────────────────
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8501"))
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# ── Organisation defaults ─────────────────────────────────────────────
DEFAULT_ORG = os.getenv("ORG_NAME", "My Organisation")
DEFAULT_COUNTRY = os.getenv("ORG_COUNTRY", "US")
FISCAL_YEAR_START_MONTH = int(os.getenv("FISCAL_YEAR_START", "1"))
