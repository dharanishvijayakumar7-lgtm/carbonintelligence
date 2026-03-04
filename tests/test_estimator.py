#!/usr/bin/env python3
"""
Unit Tests for the Carbon Estimation Engine
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from datetime import date

from database import reset_database, get_connection
from models.emission_factors import seed_emission_factors, lookup_factor, EMISSION_FACTORS
from engine.carbon_estimator import (
    estimate_single,
    process_activity,
    process_all_unprocessed,
    get_total_emissions,
    get_monthly_trends,
    get_emissions_by_category,
    get_emissions_by_department,
)
from engine.insights_engine import generate_insights
from engine.prediction import predict_emissions
from chatbot.chat_engine import chat, _detect_intent


class TestEmissionFactors(unittest.TestCase):
    """Test emission factor lookups."""

    @classmethod
    def setUpClass(cls):
        reset_database()
        seed_emission_factors()

    def test_electricity_us_factor(self):
        factor = lookup_factor("electricity", "grid_us", "US")
        self.assertAlmostEqual(factor, 0.417, places=3)

    def test_electricity_global_fallback(self):
        factor = lookup_factor("electricity", "grid_global", "GLOBAL")
        self.assertAlmostEqual(factor, 0.494, places=3)

    def test_travel_flight_short(self):
        factor = lookup_factor("travel", "flight_short")
        self.assertAlmostEqual(factor, 0.255, places=3)

    def test_commuting_car_petrol(self):
        factor = lookup_factor("commuting", "car_petrol")
        self.assertAlmostEqual(factor, 0.171, places=3)

    def test_cloud_aws(self):
        factor = lookup_factor("cloud", "aws")
        self.assertAlmostEqual(factor, 0.0006, places=4)

    def test_waste_landfill(self):
        factor = lookup_factor("waste", "general_landfill")
        self.assertAlmostEqual(factor, 0.587, places=3)

    def test_unknown_category_returns_zero(self):
        factor = lookup_factor("nonexistent_category", "nonexistent_sub")
        self.assertEqual(factor, 0.0)

    def test_renewable_is_zero(self):
        factor = lookup_factor("electricity", "renewable")
        self.assertEqual(factor, 0.0)


class TestCarbonEstimator(unittest.TestCase):
    """Test emission calculation engine."""

    @classmethod
    def setUpClass(cls):
        reset_database()
        seed_emission_factors()

    def test_estimate_electricity(self):
        """1000 kWh × 0.417 = 417.0 kg CO₂e"""
        result = estimate_single("electricity", 1000, "kWh", "grid_us", "US")
        self.assertAlmostEqual(result, 417.0, places=1)

    def test_estimate_travel_flight(self):
        """500 km × 0.255 = 127.5 kg CO₂e"""
        result = estimate_single("travel", 500, "km", "flight_short")
        self.assertAlmostEqual(result, 127.5, places=1)

    def test_estimate_commuting(self):
        """1000 km × 0.171 = 171.0 kg CO₂e"""
        result = estimate_single("commuting", 1000, "km", "car_petrol")
        self.assertAlmostEqual(result, 171.0, places=1)

    def test_estimate_cloud(self):
        """1000 USD × 0.0006 = 0.6 kg CO₂e"""
        result = estimate_single("cloud", 1000, "USD", "aws")
        self.assertAlmostEqual(result, 0.6, places=1)

    def test_estimate_equipment(self):
        """1 laptop × 350 = 350.0 kg CO₂e"""
        result = estimate_single("equipment", 1, "item", "laptop")
        self.assertAlmostEqual(result, 350.0, places=0)

    def test_estimate_waste(self):
        """100 kg × 0.587 = 58.7 kg CO₂e"""
        result = estimate_single("waste", 100, "kg", "general_landfill")
        self.assertAlmostEqual(result, 58.7, places=1)

    def test_process_activity(self):
        """Insert an activity and process it."""
        conn = get_connection()
        conn.execute("""
            INSERT INTO raw_activity (id, source_file, category, subcategory, department, quantity, unit, date)
            VALUES (9999, 'test', 'electricity', 'grid_us', 'Test', 500, 'kWh', '2025-06-01')
        """)
        co2e = process_activity(9999)
        # 500 kWh × grid_us factor (0.417 for US or 0.494 for GLOBAL)
        self.assertGreater(co2e, 100)
        self.assertLess(co2e, 300)

        # Verify emission was stored
        row = conn.execute("SELECT co2e_kg FROM emissions WHERE activity_id = 9999").fetchone()
        self.assertIsNotNone(row)
        self.assertAlmostEqual(row[0], co2e, places=1)


class TestDatabaseOperations(unittest.TestCase):
    """Test database query operations."""

    @classmethod
    def setUpClass(cls):
        reset_database()
        seed_emission_factors()
        conn = get_connection()

        # Insert test data across months and departments
        test_data = [
            (1, "electricity", "grid_us", "Engineering", 3000, "kWh", "2025-01-15"),
            (2, "electricity", "grid_us", "Marketing", 1500, "kWh", "2025-01-15"),
            (3, "travel", "flight_short", "Sales", 600, "km", "2025-01-20"),
            (4, "commuting", "car_petrol", "Engineering", 5000, "km", "2025-01-31"),
            (5, "electricity", "grid_us", "Engineering", 2800, "kWh", "2025-02-15"),
            (6, "travel", "car_petrol", "Sales", 400, "km", "2025-02-10"),
            (7, "waste", "general_landfill", "Operations", 100, "kg", "2025-02-28"),
            (8, "cloud", "aws", "Engineering", 3000, "USD", "2025-01-31"),
            (9, "cloud", "aws", "Engineering", 3200, "USD", "2025-02-28"),
            (10, "equipment", "laptop", "Engineering", 3, "item", "2025-01-10"),
        ]

        for tid, cat, sub, dept, qty, unit, dt in test_data:
            conn.execute(
                "INSERT INTO raw_activity (id, source_file, category, subcategory, department, quantity, unit, date) "
                "VALUES (?, 'test', ?, ?, ?, ?, ?, ?)",
                [tid, cat, sub, dept, qty, unit, dt],
            )

        process_all_unprocessed()

    def test_get_total_emissions(self):
        summary = get_total_emissions()
        self.assertGreater(summary["total_co2e_kg"], 0)
        self.assertGreater(summary["record_count"], 0)
        self.assertIn("by_category", summary)
        self.assertIn("by_department", summary)

    def test_get_monthly_trends(self):
        trends = get_monthly_trends()
        self.assertGreater(len(trends), 0)
        self.assertIn("month", trends[0])
        self.assertIn("co2e_kg", trends[0])

    def test_get_emissions_by_category(self):
        cats = get_emissions_by_category()
        self.assertGreater(len(cats), 0)
        categories = [c["category"] for c in cats]
        self.assertIn("electricity", categories)

    def test_get_emissions_by_department(self):
        depts = get_emissions_by_department()
        self.assertGreater(len(depts), 0)
        dept_names = [d["department"] for d in depts]
        self.assertIn("Engineering", dept_names)

    def test_date_filtering(self):
        jan = get_total_emissions(start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        feb = get_total_emissions(start_date=date(2025, 2, 1), end_date=date(2025, 2, 28))
        self.assertGreater(jan["total_co2e_kg"], 0)
        self.assertGreater(feb["total_co2e_kg"], 0)


class TestInsightsEngine(unittest.TestCase):
    """Test AI insights generation."""

    @classmethod
    def setUpClass(cls):
        # Reuse data from TestDatabaseOperations
        pass

    def test_generate_insights(self):
        insights = generate_insights()
        self.assertIn("insights", insights)
        self.assertIn("total_potential_reduction_kg", insights)
        self.assertIn("total_potential_reduction_pct", insights)

    def test_insights_have_required_fields(self):
        insights = generate_insights()
        for insight in insights.get("insights", []):
            self.assertIn("category", insight)
            self.assertIn("priority", insight)
            self.assertIn("title", insight)
            self.assertIn("description", insight)
            self.assertIn("estimated_reduction_kg", insight)


class TestChatEngine(unittest.TestCase):
    """Test natural language chat interface."""

    def test_detect_total_intent(self):
        self.assertEqual(_detect_intent("What is our total carbon footprint?"), "total_emissions")

    def test_detect_category_intent(self):
        self.assertEqual(_detect_intent("Show emissions by category"), "by_category")

    def test_detect_department_intent(self):
        self.assertEqual(_detect_intent("Which department has the most emissions?"), "by_department")

    def test_detect_reduction_intent(self):
        self.assertEqual(_detect_intent("How can we reduce emissions by 20%?"), "reduction")

    def test_detect_trend_intent(self):
        self.assertEqual(_detect_intent("Show monthly trends"), "monthly_trend")

    def test_detect_compare_intent(self):
        self.assertEqual(_detect_intent("Compare January and February"), "compare_months")

    def test_detect_prediction_intent(self):
        self.assertEqual(_detect_intent("Show me the forecast for next quarter"), "prediction")

    def test_detect_help_intent(self):
        self.assertEqual(_detect_intent("help"), "help")

    def test_chat_returns_answer(self):
        result = chat("What is our carbon footprint?")
        self.assertIn("answer", result)
        self.assertIsInstance(result["answer"], str)
        self.assertGreater(len(result["answer"]), 0)

    def test_chat_help(self):
        result = chat("help")
        self.assertIn("answer", result)
        self.assertIn("Carbon Intelligence", result["answer"])


class TestPredictionEngine(unittest.TestCase):
    """Test emission forecasting."""

    def test_predict_emissions(self):
        pred = predict_emissions(months_ahead=6)
        self.assertIn("trend", pred)
        self.assertIn("historical", pred)

    def test_predict_returns_predictions(self):
        pred = predict_emissions(months_ahead=3)
        if pred.get("trend") != "insufficient_data":
            self.assertIn("predicted", pred)
            self.assertGreater(len(pred["predicted"]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
