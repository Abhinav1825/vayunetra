"""Auth guard + input-validation tests.

These exercise paths the fixture-only test_api.py never touched: the admin-key
guard, the broadcast rate-limit, and the request-validation bounds added to the
POST bodies. Auth guards are tested at the function level so they don't require a
live token through the get_db dependency.
"""
import os

os.environ["DEMO_MODE"] = "true"

from fastapi.testclient import TestClient  # noqa: E402

import api.main as m  # noqa: E402

client = TestClient(m.app)


# --- input validation (H4): bad input must 422, not 500 or hang ---------------

def test_simulate_rejects_out_of_range_horizon():
    assert client.post("/simulate", json={"city": "delhi", "horizon_h": 999}).status_code == 422


def test_simulate_rejects_injection_like_city():
    assert client.post("/simulate", json={"city": "DROP TABLE x"}).status_code == 422


def test_optimize_rejects_nonpositive_budget():
    assert client.post("/optimize", json={"city": "delhi", "budget_inspector_hours": -5}).status_code == 422
    assert client.post("/optimize", json={"city": "delhi", "budget_inspector_hours": 0}).status_code == 422


def test_status_rejects_unknown_enum():
    assert client.post("/enforcement/1/status", json={"status": "garbage"}).status_code == 422


def test_valid_inputs_still_accepted():
    assert client.post("/simulate", json={"city": "delhi", "horizon_h": 48}).status_code == 200
    assert client.post("/enforcement/1/status", json={"status": "approved"}).status_code == 200


# --- admin-key guard (function-level, bypasses the get_db token dependency) ----

def test_admin_guard_rejects_wrong_key(monkeypatch):
    monkeypatch.setattr(m, "DEMO_MODE", False)
    monkeypatch.setenv("ADMIN_KEY", "s3cret-key")
    res = m.admin_onboard_city(m.CityBody(city_id="testcity", name="Test"), x_admin_key="wrong", db=None)
    assert res["success"] is False
    assert res["error"]["code"] == "forbidden"


def test_admin_guard_rejects_missing_key(monkeypatch):
    monkeypatch.setattr(m, "DEMO_MODE", False)
    monkeypatch.setenv("ADMIN_KEY", "s3cret-key")
    res = m.admin_onboard_city(m.CityBody(city_id="testcity", name="Test"), x_admin_key=None, db=None)
    assert res["error"]["code"] == "forbidden"


def test_admin_guard_not_configured(monkeypatch):
    monkeypatch.setattr(m, "DEMO_MODE", False)
    monkeypatch.delenv("ADMIN_KEY", raising=False)
    res = m.admin_onboard_city(m.CityBody(city_id="x", name="X"), x_admin_key="whatever", db=None)
    assert res["error"]["code"] == "not_configured"


# --- broadcast rate-limit (money-spending path) -------------------------------

def test_broadcast_is_rate_limited(monkeypatch):
    # No real channels: keep the test from touching Telegram/Twilio.
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)
    m._last_broadcast.clear()
    first = client.post("/advisory/broadcast", json={"city": "delhi"})
    second = client.post("/advisory/broadcast", json={"city": "delhi"})
    assert first.json()["success"] is True
    assert second.json()["error"]["code"] == "rate_limited"
