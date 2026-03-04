"""
AI Insights Engine

Generates actionable carbon reduction recommendations based on
current emission data. Uses rule-based analysis + optional LLM enhancement.
"""
from __future__ import annotations

from models import Insight
from engine.carbon_estimator import get_total_emissions, get_emissions_by_category


# ── Reduction strategies database ────────────────────────────────────

REDUCTION_STRATEGIES: list[dict] = [
    # Electricity
    {
        "category": "electricity",
        "trigger_pct": 0.10,
        "priority": "high",
        "title": "Switch to renewable energy provider",
        "description": (
            "Your electricity usage accounts for {pct:.0%} of total emissions. "
            "Switching to a certified renewable energy provider (e.g., Green-e certified) "
            "could reduce Scope 2 emissions by up to 100%. Many providers offer competitive "
            "rates. Consider Power Purchase Agreements (PPAs) or Renewable Energy Certificates (RECs)."
        ),
        "reduction_pct": 0.80,
    },
    {
        "category": "electricity",
        "trigger_pct": 0.05,
        "priority": "medium",
        "title": "Implement smart energy management",
        "description": (
            "Install smart power strips, enable power management on all computers, "
            "and use occupancy sensors for lighting. Typical savings: 10-25% of electricity usage. "
            "Set all computers to sleep after 10 minutes of inactivity."
        ),
        "reduction_pct": 0.15,
    },

    # Travel
    {
        "category": "travel",
        "trigger_pct": 0.10,
        "priority": "high",
        "title": "Replace short-haul flights with virtual meetings",
        "description": (
            "Business travel accounts for {pct:.0%} of your emissions. "
            "Replace domestic short-haul flights (<500 km) with video conferencing. "
            "For necessary travel, prefer rail over air for trips under 4 hours. "
            "Implement a travel policy requiring VP approval for flights."
        ),
        "reduction_pct": 0.40,
    },
    {
        "category": "travel",
        "trigger_pct": 0.05,
        "priority": "medium",
        "title": "Optimize travel booking policies",
        "description": (
            "Book economy class (business class has 3x the carbon footprint), "
            "prefer direct flights, and consolidate trips. Use carbon-offset programs "
            "for unavoidable travel. Consider a quarterly travel budget per department."
        ),
        "reduction_pct": 0.20,
    },

    # Commuting
    {
        "category": "commuting",
        "trigger_pct": 0.10,
        "priority": "high",
        "title": "Implement hybrid/remote work policy",
        "description": (
            "Employee commuting makes up {pct:.0%} of emissions. "
            "Allowing 2-3 days of remote work per week can reduce commuting emissions by 40-60%. "
            "This also improves employee satisfaction and reduces office energy costs."
        ),
        "reduction_pct": 0.50,
    },
    {
        "category": "commuting",
        "trigger_pct": 0.05,
        "priority": "medium",
        "title": "Encourage sustainable commuting",
        "description": (
            "Offer incentives for public transit, cycling, and carpooling. "
            "Provide secure bike parking, showers, and transit subsidies. "
            "Consider an EV charging station for employees who switch to electric vehicles."
        ),
        "reduction_pct": 0.25,
    },

    # Cloud
    {
        "category": "cloud",
        "trigger_pct": 0.05,
        "priority": "high",
        "title": "Optimize cloud infrastructure",
        "description": (
            "Cloud computing accounts for {pct:.0%} of emissions. "
            "Right-size instances, shut down idle resources, use spot/preemptible instances, "
            "and schedule non-production environments to run only during business hours. "
            "Typical savings: 20-40% of cloud spend and associated emissions."
        ),
        "reduction_pct": 0.30,
    },
    {
        "category": "cloud",
        "trigger_pct": 0.03,
        "priority": "medium",
        "title": "Choose low-carbon cloud regions",
        "description": (
            "Migrate workloads to cloud regions powered by renewable energy. "
            "GCP offers carbon-free regions, AWS has renewable-powered regions, "
            "and Azure publishes carbon intensity by region. This can reduce cloud "
            "emissions by 50-90% with zero performance impact."
        ),
        "reduction_pct": 0.50,
    },

    # Equipment
    {
        "category": "equipment",
        "trigger_pct": 0.05,
        "priority": "medium",
        "title": "Extend equipment lifecycle and buy refurbished",
        "description": (
            "Office equipment accounts for {pct:.0%} of emissions. "
            "Extend laptop/desktop refresh cycles from 3 to 5 years, "
            "buy refurbished equipment, and implement proper e-waste recycling. "
            "Each laptop avoided saves ~350 kg CO₂e."
        ),
        "reduction_pct": 0.30,
    },

    # Waste
    {
        "category": "waste",
        "trigger_pct": 0.02,
        "priority": "medium",
        "title": "Implement zero-waste office program",
        "description": (
            "Waste disposal accounts for {pct:.0%} of emissions. "
            "Set up comprehensive recycling stations, compost food waste, "
            "eliminate single-use plastics, and go paperless. "
            "A zero-waste program can divert 90%+ from landfill."
        ),
        "reduction_pct": 0.70,
    },
]


def generate_insights() -> dict:
    """
    Analyze current emissions and generate prioritized reduction recommendations.
    Returns InsightsResponse-compatible dict.
    """
    summary = get_total_emissions()
    total = summary["total_co2e_kg"]

    if total == 0:
        return {
            "insights": [],
            "total_potential_reduction_kg": 0,
            "total_potential_reduction_pct": 0,
        }

    by_category = summary.get("by_category", {})
    insights: list[dict] = []
    total_reduction = 0.0

    for strategy in REDUCTION_STRATEGIES:
        cat = strategy["category"]
        cat_emissions = by_category.get(cat, 0)
        cat_pct = cat_emissions / total if total > 0 else 0

        if cat_pct >= strategy["trigger_pct"]:
            reduction_kg = cat_emissions * strategy["reduction_pct"]
            total_reduction += reduction_kg

            insights.append({
                "category": cat,
                "priority": strategy["priority"],
                "title": strategy["title"],
                "description": strategy["description"].format(pct=cat_pct),
                "estimated_reduction_pct": round(strategy["reduction_pct"] * 100, 1),
                "estimated_reduction_kg": round(reduction_kg, 2),
            })

    # Sort by potential reduction (descending)
    insights.sort(key=lambda x: x["estimated_reduction_kg"], reverse=True)

    return {
        "insights": insights,
        "total_potential_reduction_kg": round(total_reduction, 2),
        "total_potential_reduction_pct": round((total_reduction / total) * 100, 1) if total > 0 else 0,
    }
