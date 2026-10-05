from src.web.app import app

def test_ready_endpoint():
    """Readiness endpoint should respond without an MCP check."""

    client = app.test_client()

    response = client.get("/ready")

    assert response.status_code == 200

    data = response.get_json()

    assert data == {
        "status": "ok",
        "app": "northstar-hr-agent",
    }

def test_health_endpoint():
    """Health endpoint should report app and MCP status."""

    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "ok"
    assert data["app"] == "northstar-hr-agent"
    assert "mcp" in data
    assert data["mcp"]["status"] in {"ok", "unavailable"}
