"""
Natural Language Chat Engine

Provides a conversational interface for querying carbon emissions data.
Uses rule-based NLU with optional LLM enhancement.
Works fully offline — no API keys required.
"""
from __future__ import annotations

import re
import json
from datetime import date, datetime
from typing import Optional

from database import get_connection
from engine.carbon_estimator import (
    get_total_emissions,
    get_emissions_by_category,
    get_emissions_by_department,
    get_monthly_trends,
)
from engine.insights_engine import generate_insights
from engine.prediction import predict_emissions
from config import OPENAI_API_KEY


# ── Intent Detection ─────────────────────────────────────────────────

INTENT_PATTERNS: list[tuple[str, list[str]]] = [
    ("total_emissions", [
        r"total.*(?:emissions?|footprint|carbon)",
        r"(?:what|how much).*(?:carbon|co2|emissions?|footprint)",
        r"overall.*(?:emissions?|footprint)",
    ]),
    ("monthly_trend", [
        r"month(?:ly|s).*(?:trend|emissions?|breakdown)",
        r"(?:trend|over time|progress)",
        r"emissions?.*(?:over|by)\s*month",
    ]),
    ("compare_months", [
        r"compare.*(?:month|january|february|march|april|may|june|july|august|september|october|november|december)",
        r"(?:january|february|march|april|may|june|july|august|september|october|november|december).*(?:vs|versus|compared|and).*(?:january|february|march|april|may|june|july|august|september|october|november|december)",
        r"difference.*between.*(?:month|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)",
    ]),
    ("by_category", [
        r"(?:by|per|each)\s*(?:category|type|source)",
        r"(?:which|what).*(?:category|type|source).*(?:most|highest|biggest)",
        r"breakdown.*(?:category|type)",
        r"(?:electricity|travel|commuting|cloud|equipment|waste).*(?:emissions?|footprint)",
    ]),
    ("by_department", [
        r"(?:by|per|each)\s*(?:department|team|group|unit)",
        r"(?:which|what).*(?:department|team).*(?:most|highest|biggest)",
        r"department.*(?:comparison|breakdown)",
    ]),
    ("reduction", [
        r"(?:how|ways?).*(?:reduce|lower|decrease|cut|minimize)",
        r"(?:reduce|lower|decrease|cut).*(?:emissions?|carbon|footprint)",
        r"(?:recommendation|suggestion|advice|tip)",
        r"(?:save|saving).*(?:carbon|co2|emissions?)",
    ]),
    ("prediction", [
        r"(?:predict|forecast|project|future|next)",
        r"(?:what will|expected|estimated).*(?:next|future)",
        r"(?:trend|trajectory|outlook)",
    ]),
    ("scope_breakdown", [
        r"scope\s*[123]",
        r"(?:by|per)\s*scope",
        r"(?:direct|indirect).*(?:emissions?)",
    ]),
    ("last_month", [
        r"last\s*month",
        r"previous\s*month",
        r"(?:past|recent)\s*month",
    ]),
    ("help", [
        r"help",
        r"what\s*can\s*you\s*do",
        r"(?:commands?|options?|features?)",
    ]),
]

MONTH_NAMES = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "jun": "06", "jul": "07", "aug": "08", "sep": "09",
    "oct": "10", "nov": "11", "dec": "12",
}


def chat(message: str) -> dict:
    """
    Process a natural language query about carbon emissions.

    Returns:
        dict with 'answer' (str) and optional 'data' (dict)
    """
    # Store message
    _store_chat("user", message)

    # Detect intent
    intent = _detect_intent(message)

    # Route to handler
    handler = INTENT_HANDLERS.get(intent, _handle_general)
    result = handler(message)

    # Store response
    _store_chat("assistant", result["answer"])

    return result


def _detect_intent(message: str) -> str:
    """Detect the user's intent from the message."""
    msg_lower = message.lower().strip()

    for intent, patterns in INTENT_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, msg_lower):
                return intent

    return "general"


# ── Intent Handlers ──────────────────────────────────────────────────

def _handle_total_emissions(message: str) -> dict:
    """Handle queries about total emissions."""
    dates = _extract_date_range(message)
    summary = get_total_emissions(**dates)

    total_kg = summary["total_co2e_kg"]
    total_t = summary["total_co2e_tonnes"]

    if total_kg == 0:
        answer = "📊 No emission data found for the specified period. Try uploading some data first!"
    else:
        answer = (
            f"🌍 **Total Carbon Footprint**\n\n"
            f"- **Total Emissions:** {total_kg:,.1f} kg CO₂e ({total_t:,.2f} tonnes)\n"
            f"- **Records:** {summary['record_count']}\n\n"
        )

        if summary.get("by_category"):
            answer += "**Breakdown by Category:**\n"
            for cat, val in summary["by_category"].items():
                pct = (val / total_kg * 100) if total_kg > 0 else 0
                answer += f"  - {cat.title()}: {val:,.1f} kg ({pct:.1f}%)\n"

    return {"answer": answer, "data": summary}


def _handle_monthly_trend(message: str) -> dict:
    """Handle monthly trend queries."""
    trends = get_monthly_trends()

    if not trends:
        return {"answer": "📈 No monthly data available yet. Upload data to see trends!", "data": None}

    answer = "📈 **Monthly Emission Trends**\n\n"
    answer += "| Month | Emissions (kg CO₂e) |\n|-------|--------------------:|\n"
    for t in trends:
        answer += f"| {t['month']} | {t['co2e_kg']:,.1f} |\n"

    if len(trends) >= 2:
        first = trends[0]["co2e_kg"]
        last = trends[-1]["co2e_kg"]
        change = ((last - first) / first * 100) if first > 0 else 0
        direction = "📈 increased" if change > 0 else "📉 decreased"
        answer += f"\n*Emissions have {direction} by {abs(change):.1f}% from {trends[0]['month']} to {trends[-1]['month']}*"

    return {"answer": answer, "data": {"trends": trends}}


def _handle_compare_months(message: str) -> dict:
    """Handle month comparison queries."""
    months = _extract_months(message)
    trends = get_monthly_trends()

    if len(months) < 2:
        return {
            "answer": "Please specify two months to compare, e.g., 'Compare January and February'",
            "data": None,
        }

    trend_map = {t["month"]: t["co2e_kg"] for t in trends}

    # Find matching months
    year = date.today().year
    month_keys = []
    for m in months[:2]:
        key = f"{year}-{m}"
        if key not in trend_map:
            key = f"{year - 1}-{m}"
        month_keys.append(key)

    val1 = trend_map.get(month_keys[0], 0)
    val2 = trend_map.get(month_keys[1], 0)

    if val1 == 0 and val2 == 0:
        return {"answer": f"No data found for the specified months.", "data": None}

    diff = val2 - val1
    pct = (diff / val1 * 100) if val1 > 0 else 0

    answer = (
        f"📊 **Month Comparison**\n\n"
        f"| Month | Emissions (kg CO₂e) |\n|-------|--------------------:|\n"
        f"| {month_keys[0]} | {val1:,.1f} |\n"
        f"| {month_keys[1]} | {val2:,.1f} |\n\n"
        f"**Difference:** {diff:+,.1f} kg CO₂e ({pct:+.1f}%)"
    )

    return {"answer": answer, "data": {"months": month_keys, "values": [val1, val2], "diff": diff}}


def _handle_by_category(message: str) -> dict:
    """Handle category breakdown queries."""
    dates = _extract_date_range(message)
    categories = get_emissions_by_category(**dates)

    if not categories:
        return {"answer": "📊 No category data available.", "data": None}

    answer = "📊 **Emissions by Category**\n\n"
    answer += "| Category | Subcategory | Emissions (kg CO₂e) |\n|----------|-------------|--------------------:|\n"

    for cat in categories:
        answer += f"| {cat['category'].title()} | {cat['subcategory']} | {cat['co2e_kg']:,.1f} |\n"

    return {"answer": answer, "data": {"categories": categories}}


def _handle_by_department(message: str) -> dict:
    """Handle department breakdown queries."""
    dates = _extract_date_range(message)
    departments = get_emissions_by_department(**dates)

    if not departments:
        return {"answer": "🏢 No department data available.", "data": None}

    answer = "🏢 **Emissions by Department**\n\n"
    answer += "| Department | Emissions (kg CO₂e) | Records |\n|------------|--------------------:|--------:|\n"

    total = sum(d["co2e_kg"] for d in departments)
    for dept in departments:
        pct = (dept["co2e_kg"] / total * 100) if total > 0 else 0
        answer += f"| {dept['department']} | {dept['co2e_kg']:,.1f} ({pct:.1f}%) | {dept['records']} |\n"

    return {"answer": answer, "data": {"departments": departments}}


def _handle_reduction(message: str) -> dict:
    """Handle emission reduction queries."""
    insights_data = generate_insights()
    insights = insights_data.get("insights", [])

    if not insights:
        return {
            "answer": "💡 No specific reduction recommendations at this time. Upload more data for personalized suggestions!",
            "data": None,
        }

    # Check if user specified a percentage target
    target_match = re.search(r"(\d+)\s*%", message)
    target_pct = int(target_match.group(1)) if target_match else None

    answer = "💡 **Carbon Reduction Recommendations**\n\n"

    for i, insight in enumerate(insights, 1):
        answer += (
            f"**{i}. {insight['title']}** [{insight['priority'].upper()}]\n"
            f"   {insight['description']}\n"
            f"   *Potential reduction: {insight['estimated_reduction_kg']:,.0f} kg CO₂e "
            f"({insight['estimated_reduction_pct']:.0f}% of {insight['category']})*\n\n"
        )

    total_red = insights_data["total_potential_reduction_kg"]
    total_pct = insights_data["total_potential_reduction_pct"]
    answer += f"\n**Total Potential Reduction: {total_red:,.0f} kg CO₂e ({total_pct:.1f}%)**"

    if target_pct and total_pct < target_pct:
        answer += (
            f"\n\n⚠️ To achieve your {target_pct}% reduction target, additional measures "
            f"beyond these recommendations may be needed."
        )
    elif target_pct:
        answer += f"\n\n✅ These recommendations can help you achieve your {target_pct}% reduction target!"

    return {"answer": answer, "data": insights_data}


def _handle_prediction(message: str) -> dict:
    """Handle prediction/forecast queries."""
    pred = predict_emissions(months_ahead=6)

    if pred.get("trend") == "insufficient_data":
        return {
            "answer": "🔮 Not enough historical data for predictions. Need at least 2 months of data.",
            "data": None,
        }

    answer = (
        f"🔮 **Emission Forecast**\n\n"
        f"- **Trend:** {pred['trend'].title()}\n"
        f"- **Monthly Average:** {pred['monthly_average_kg']:,.1f} kg CO₂e\n"
        f"- **Annual Forecast:** {pred['annual_forecast_kg']:,.1f} kg CO₂e "
        f"({pred['annual_forecast_tonnes']:,.2f} tonnes)\n"
        f"- **Monthly Change:** {pred['slope_kg_per_month']:+,.1f} kg/month\n\n"
    )

    if pred.get("predicted"):
        answer += "**Predicted Monthly Emissions:**\n"
        answer += "| Month | Predicted (kg CO₂e) |\n|-------|--------------------:|\n"
        for p in pred["predicted"]:
            answer += f"| {p['month']} | {p['co2e_kg']:,.1f} |\n"

    return {"answer": answer, "data": pred}


def _handle_scope(message: str) -> dict:
    """Handle scope breakdown queries."""
    summary = get_total_emissions()
    by_scope = summary.get("by_scope", {})

    if not by_scope:
        return {"answer": "No scope data available.", "data": None}

    total = summary["total_co2e_kg"]
    scope_desc = {1: "Direct emissions", 2: "Purchased electricity", 3: "Value chain"}

    answer = "🔍 **Emissions by GHG Scope**\n\n"
    answer += "| Scope | Description | Emissions (kg CO₂e) | % |\n|-------|-------------|--------------------:|---:|\n"

    for scope, val in sorted(by_scope.items()):
        pct = (val / total * 100) if total > 0 else 0
        answer += f"| Scope {scope} | {scope_desc.get(scope, '')} | {val:,.1f} | {pct:.1f}% |\n"

    return {"answer": answer, "data": {"by_scope": by_scope}}


def _handle_last_month(message: str) -> dict:
    """Handle 'last month' queries."""
    today = date.today()
    if today.month == 1:
        last_month_start = date(today.year - 1, 12, 1)
        last_month_end = date(today.year - 1, 12, 31)
    else:
        last_month_start = date(today.year, today.month - 1, 1)
        last_month_end = date(today.year, today.month, 1) - __import__("datetime").timedelta(days=1)

    summary = get_total_emissions(last_month_start, last_month_end)
    total_kg = summary["total_co2e_kg"]

    period = f"{last_month_start.year}-{last_month_start.month:02d}"

    if total_kg == 0:
        return {"answer": f"📊 No emission data for {period}.", "data": None}

    answer = (
        f"📊 **Last Month's Emissions ({period})**\n\n"
        f"- **Total:** {total_kg:,.1f} kg CO₂e ({summary['total_co2e_tonnes']:,.2f} tonnes)\n"
        f"- **Records:** {summary['record_count']}\n"
    )

    if summary.get("by_category"):
        answer += "\n**By Category:**\n"
        for cat, val in summary["by_category"].items():
            answer += f"  - {cat.title()}: {val:,.1f} kg\n"

    return {"answer": answer, "data": summary}


def _handle_help(message: str) -> dict:
    """Handle help queries."""
    answer = (
        "🤖 **Carbon Intelligence Assistant — What I Can Do**\n\n"
        "Ask me questions like:\n\n"
        "📊 **Emissions Data:**\n"
        '- "What is our total carbon footprint?"\n'
        '- "Show emissions by category"\n'
        '- "Which department has the most emissions?"\n'
        '- "What was our footprint last month?"\n\n'
        "📈 **Trends & Comparisons:**\n"
        '- "Show monthly trends"\n'
        '- "Compare January and February"\n'
        '- "Show emissions by scope"\n\n'
        "💡 **Recommendations:**\n"
        '- "How can we reduce emissions?"\n'
        '- "How to reduce emissions by 20%?"\n\n'
        "🔮 **Predictions:**\n"
        '- "What will our emissions be next quarter?"\n'
        '- "Show forecast"\n'
    )
    return {"answer": answer, "data": None}


def _handle_general(message: str) -> dict:
    """Handle general/unrecognized queries using data context."""
    # Try LLM if available
    if OPENAI_API_KEY:
        return _handle_with_llm(message)

    # Fallback: provide summary + suggest specific questions
    summary = get_total_emissions()
    total = summary["total_co2e_kg"]

    answer = (
        f"I'm not sure I understood your question exactly. Here's what I know:\n\n"
        f"📊 **Current Status:** {total:,.1f} kg CO₂e total emissions across "
        f"{summary['record_count']} records.\n\n"
        f"Try asking me something specific like:\n"
        f'- "What is our total carbon footprint?"\n'
        f'- "Show emissions by category"\n'
        f'- "How can we reduce emissions?"\n'
        f'- Type "help" for all available queries'
    )

    return {"answer": answer, "data": summary}


def _handle_with_llm(message: str) -> dict:
    """Use OpenAI LLM for complex queries (optional)."""
    try:
        from langchain_community.chat_models import ChatOpenAI
        from langchain.schema import SystemMessage, HumanMessage

        # Build context
        summary = get_total_emissions()
        categories = get_emissions_by_category()
        departments = get_emissions_by_department()
        trends = get_monthly_trends()

        context = (
            f"You are a sustainability assistant for an organization.\n\n"
            f"Current emission data:\n"
            f"- Total emissions: {summary['total_co2e_kg']:,.1f} kg CO₂e\n"
            f"- By category: {json.dumps(summary.get('by_category', {}))}\n"
            f"- By department: {json.dumps(summary.get('by_department', {}))}\n"
            f"- Monthly trends: {json.dumps(trends[-6:] if len(trends) > 6 else trends)}\n"
            f"\nAnswer the user's question accurately and concisely."
        )

        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)
        response = llm.invoke([
            SystemMessage(content=context),
            HumanMessage(content=message),
        ])

        return {"answer": response.content, "data": summary}
    except Exception as e:
        return _handle_general(message)


# ── Utility Functions ────────────────────────────────────────────────

def _extract_date_range(message: str) -> dict:
    """Extract date range from message if present."""
    today = date.today()

    if re.search(r"last\s*month", message, re.IGNORECASE):
        if today.month == 1:
            start = date(today.year - 1, 12, 1)
            end = date(today.year - 1, 12, 31)
        else:
            start = date(today.year, today.month - 1, 1)
            end = date(today.year, today.month, 1) - __import__("datetime").timedelta(days=1)
        return {"start_date": start, "end_date": end}

    if re.search(r"this\s*month", message, re.IGNORECASE):
        start = date(today.year, today.month, 1)
        return {"start_date": start, "end_date": today}

    if re.search(r"this\s*year|ytd", message, re.IGNORECASE):
        start = date(today.year, 1, 1)
        return {"start_date": start, "end_date": today}

    if re.search(r"last\s*year", message, re.IGNORECASE):
        start = date(today.year - 1, 1, 1)
        end = date(today.year - 1, 12, 31)
        return {"start_date": start, "end_date": end}

    return {}


def _extract_months(message: str) -> list[str]:
    """Extract month numbers from message."""
    months_found = []
    msg_lower = message.lower()
    for name, num in MONTH_NAMES.items():
        if name in msg_lower:
            if num not in months_found:
                months_found.append(num)
    return months_found


def _store_chat(role: str, content: str) -> None:
    """Store chat message in database."""
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO chat_history (id, role, content) VALUES (nextval('seq_chat'), ?, ?)",
            [role, content[:2000]],
        )
    except Exception:
        pass  # Non-critical


# ── Intent handler mapping ───────────────────────────────────────────

INTENT_HANDLERS = {
    "total_emissions": _handle_total_emissions,
    "monthly_trend": _handle_monthly_trend,
    "compare_months": _handle_compare_months,
    "by_category": _handle_by_category,
    "by_department": _handle_by_department,
    "reduction": _handle_reduction,
    "prediction": _handle_prediction,
    "scope_breakdown": _handle_scope,
    "last_month": _handle_last_month,
    "help": _handle_help,
    "general": _handle_general,
}
