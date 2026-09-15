"""
Tests for restocking API endpoints (budget recommendations and restock orders).
"""
import math
from datetime import date, timedelta

import pytest

import mock_data
from main import recommend_restock


@pytest.fixture(autouse=True)
def reset_restock_orders():
    """Clear in-memory restock orders so POSTs in one test don't leak into another."""
    # Clear in place: main.py holds a reference to this same list object
    mock_data.restock_orders.clear()
    yield
    mock_data.restock_orders.clear()


def build_order_payload(warehouse="London", budget=5000, items=None):
    """Build a valid restock order request body, overridable per test."""
    return {
        "warehouse": warehouse,
        "budget": budget,
        "items": items if items is not None else [{"item_sku": "WDG-001", "quantity": 10}],
    }


class TestRestockRecommendationEndpoints:
    """Test suite for the restock recommendations endpoint."""

    def test_get_restock_recommendations(self, client):
        """Test getting recommendations returns the expected structure."""
        response = client.get("/api/restock/recommendations?budget=5000")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        for field in ["budget", "total_cost", "remaining_budget", "total_needed_cost", "items"]:
            assert field in data, f"Missing field: {field}"
        assert isinstance(data["items"], list)
        assert len(data["items"]) > 0

        item = data["items"][0]
        for field in ["item_sku", "item_name", "trend", "unit_cost", "quantity_needed",
                      "recommended_quantity", "line_total", "fully_covered"]:
            assert field in item, f"Missing item field: {field}"
        assert isinstance(item["recommended_quantity"], int)
        assert isinstance(item["fully_covered"], bool)

    def test_zero_budget_recommends_nothing(self, client):
        """Test that a zero budget produces no recommended items."""
        response = client.get("/api/restock/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data["items"] == []
        assert data["total_cost"] == 0
        assert data["remaining_budget"] == 0

    @pytest.mark.parametrize("budget", [250, 1000, 5000, 12345.67])
    def test_total_cost_within_budget(self, client, budget):
        """Test that recommendations never exceed the budget and totals add up."""
        response = client.get(f"/api/restock/recommendations?budget={budget}")
        data = response.json()

        line_sum = sum(item["line_total"] for item in data["items"])
        assert data["total_cost"] <= budget, f"Total {data['total_cost']} exceeds budget {budget}"
        assert abs(line_sum - data["total_cost"]) < 0.01
        assert abs((budget - data["total_cost"]) - data["remaining_budget"]) < 0.01

        for item in data["items"]:
            assert 0 < item["recommended_quantity"] <= item["quantity_needed"]
            assert abs(item["recommended_quantity"] * item["unit_cost"] - item["line_total"]) < 0.01
            assert item["fully_covered"] == (item["recommended_quantity"] == item["quantity_needed"])

    def test_increasing_trend_items_prioritized(self, client):
        """Test that items are ordered by trend priority: increasing, stable, decreasing."""
        response = client.get("/api/restock/recommendations?budget=1000000")
        data = response.json()

        trend_rank = {"increasing": 0, "stable": 1, "decreasing": 2}
        ranks = [trend_rank[item["trend"].lower()] for item in data["items"]]
        assert ranks == sorted(ranks), f"Items not in trend priority order: {ranks}"
        assert data["items"][0]["trend"].lower() == "increasing"

    def test_limited_budget_funds_increasing_items_first(self, client):
        """Test that a tight budget is spent on increasing-trend items before others."""
        response = client.get("/api/restock/recommendations?budget=1000")
        data = response.json()

        assert len(data["items"]) > 0
        assert all(item["trend"].lower() == "increasing" for item in data["items"])

    def test_large_budget_covers_all_items(self, client):
        """Test that a budget above total need fully covers every forecast item."""
        demand = client.get("/api/demand").json()

        response = client.get("/api/restock/recommendations?budget=1000000")
        data = response.json()

        assert len(data["items"]) == len(demand)
        assert all(item["fully_covered"] for item in data["items"])
        assert abs(data["total_cost"] - data["total_needed_cost"]) < 0.01

    def test_quantity_needed_calculation(self, client):
        """Test needed quantity is demand growth with a 10% safety-stock floor."""
        demand = {f["item_sku"]: f for f in client.get("/api/demand").json()}

        response = client.get("/api/restock/recommendations?budget=1000000")
        for item in response.json()["items"]:
            forecast = demand[item["item_sku"]]
            growth = forecast["forecasted_demand"] - forecast["current_demand"]
            safety_stock = math.ceil(0.10 * forecast["forecasted_demand"])
            assert item["quantity_needed"] == max(growth, safety_stock)

    def test_decreasing_items_get_safety_stock(self, client):
        """Test that decreasing-demand items still receive a positive safety-stock quantity."""
        response = client.get("/api/restock/recommendations?budget=1000000")
        decreasing = [i for i in response.json()["items"] if i["trend"].lower() == "decreasing"]

        assert len(decreasing) > 0
        for item in decreasing:
            assert item["quantity_needed"] > 0

    def test_negative_budget_rejected(self, client):
        """Test that a negative budget fails validation."""
        response = client.get("/api/restock/recommendations?budget=-1")
        assert response.status_code == 422

    def test_missing_budget_rejected(self, client):
        """Test that the budget query parameter is required."""
        response = client.get("/api/restock/recommendations")
        assert response.status_code == 422

    def test_new_item_with_zero_current_demand_prioritized(self):
        """Test that a new SKU (zero current demand) ranks first within its trend."""
        # Unit-level check on the helper: the shipped data has no zero-demand rows to hit via the API
        forecasts = [
            {"item_sku": "OLD-1", "item_name": "Existing Item", "current_demand": 100,
             "forecasted_demand": 150, "trend": "increasing", "unit_cost": 1.0},
            {"item_sku": "NEW-1", "item_name": "New Item", "current_demand": 0,
             "forecasted_demand": 50, "trend": "increasing", "unit_cost": 1.0},
        ]

        result = recommend_restock(forecasts, budget=1000)
        assert [item["item_sku"] for item in result["items"]] == ["NEW-1", "OLD-1"]

    def test_zero_cost_item_skipped(self):
        """Test that an item with no unit cost is never recommended (guards divide-by-zero)."""
        forecasts = [
            {"item_sku": "FREE-1", "item_name": "Unpriced Item", "current_demand": 10,
             "forecasted_demand": 20, "trend": "increasing", "unit_cost": 0.0},
            {"item_sku": "PAID-1", "item_name": "Priced Item", "current_demand": 10,
             "forecasted_demand": 20, "trend": "stable", "unit_cost": 2.0},
        ]

        result = recommend_restock(forecasts, budget=100)
        assert [item["item_sku"] for item in result["items"]] == ["PAID-1"]
        assert result["total_cost"] == 20.0


class TestRestockOrderEndpoints:
    """Test suite for creating and listing restock orders."""

    def test_create_restock_order(self, client):
        """Test submitting a valid restock order."""
        response = client.post("/api/restock-orders", json=build_order_payload())
        assert response.status_code == 201

        order = response.json()
        assert order["order_number"] == "RST-0001"
        assert order["warehouse"] == "London"
        assert order["status"] == "Submitted"
        assert order["lead_time_days"] == 7
        assert order["order_date"] == date.today().isoformat()
        assert order["expected_delivery"] == (date.today() + timedelta(days=7)).isoformat()

        assert len(order["items"]) == 1
        item = order["items"][0]
        assert item["item_sku"] == "WDG-001"
        assert item["item_name"] == "Industrial Widget Type A"
        assert item["quantity"] == 10

    @pytest.mark.parametrize("warehouse,lead_time_days", [
        ("San Francisco", 3),
        ("London", 7),
        ("Tokyo", 10),
    ])
    def test_lead_time_by_warehouse(self, client, warehouse, lead_time_days):
        """Test that lead time and expected delivery depend on the destination warehouse."""
        response = client.post("/api/restock-orders", json=build_order_payload(warehouse=warehouse))
        assert response.status_code == 201

        order = response.json()
        assert order["lead_time_days"] == lead_time_days
        expected = date.fromisoformat(order["order_date"]) + timedelta(days=lead_time_days)
        assert order["expected_delivery"] == expected.isoformat()

    def test_order_totals_computed_by_server(self, client):
        """Test that prices come from forecast data, ignoring client-supplied costs."""
        demand = {f["item_sku"]: f for f in client.get("/api/demand").json()}
        items = [
            # Extra client-supplied price fields must be ignored by the server
            {"item_sku": "WDG-001", "quantity": 10, "unit_cost": 0.01, "line_total": 0.1},
            {"item_sku": "FLT-405", "quantity": 4},
        ]

        response = client.post("/api/restock-orders", json=build_order_payload(items=items))
        assert response.status_code == 201

        order = response.json()
        expected_total = 10 * demand["WDG-001"]["unit_cost"] + 4 * demand["FLT-405"]["unit_cost"]
        assert abs(order["total_value"] - expected_total) < 0.01
        for item in order["items"]:
            assert item["unit_cost"] == demand[item["item_sku"]]["unit_cost"]
            assert abs(item["line_total"] - item["quantity"] * item["unit_cost"]) < 0.01

    def test_order_from_recommendations_accepted(self, client):
        """Test that ordering exactly what was recommended stays within budget."""
        recommendations = client.get("/api/restock/recommendations?budget=5000").json()
        items = [
            {"item_sku": i["item_sku"], "quantity": i["recommended_quantity"]}
            for i in recommendations["items"]
        ]

        response = client.post("/api/restock-orders", json=build_order_payload(budget=5000, items=items))
        assert response.status_code == 201
        assert abs(response.json()["total_value"] - recommendations["total_cost"]) < 0.01

    @pytest.mark.parametrize("overrides,detail_fragment", [
        ({"warehouse": "Paris"}, "unknown warehouse"),
        ({"items": []}, "at least one item"),
        ({"items": [{"item_sku": "NOPE-999", "quantity": 5}]}, "unknown item sku"),
        ({"items": [{"item_sku": "WDG-001", "quantity": 5}, {"item_sku": "WDG-001", "quantity": 5}]},
         "duplicate item sku"),
        ({"items": [{"item_sku": "WDG-001", "quantity": 0}]}, "greater than 0"),
        ({"items": [{"item_sku": "WDG-001", "quantity": -3}]}, "greater than 0"),
        ({"budget": -10}, "negative"),
        ({"budget": 100, "items": [{"item_sku": "WDG-001", "quantity": 1000}]}, "exceeds budget"),
    ])
    def test_invalid_restock_order_rejected(self, client, overrides, detail_fragment):
        """Test that invalid orders return 400 with a descriptive message and are not saved."""
        payload = {**build_order_payload(), **overrides}

        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert detail_fragment in data["detail"].lower(), f"Unexpected detail: {data['detail']}"

        assert client.get("/api/restock-orders").json() == []

    def test_malformed_restock_order_rejected(self, client):
        """Test that a request missing required fields fails validation."""
        response = client.post("/api/restock-orders", json={"warehouse": "London"})
        assert response.status_code == 422

    def test_get_restock_orders_empty(self, client):
        """Test listing restock orders when none have been submitted."""
        response = client.get("/api/restock-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_restock_orders_newest_first(self, client):
        """Test that submitted orders are listed newest first with sequential numbers."""
        client.post("/api/restock-orders", json=build_order_payload(warehouse="Tokyo"))
        client.post("/api/restock-orders", json=build_order_payload(warehouse="San Francisco"))

        response = client.get("/api/restock-orders")
        assert response.status_code == 200

        data = response.json()
        assert [o["order_number"] for o in data] == ["RST-0002", "RST-0001"]
        assert [o["warehouse"] for o in data] == ["San Francisco", "Tokyo"]
