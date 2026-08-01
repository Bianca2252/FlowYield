"""Smoke tests for the FlowYield application foundation."""

from app import create_app


def test_create_app_uses_testing_configuration():
    """The factory should create an isolated testing application."""
    app = create_app("testing")

    assert app.config["TESTING"] is True
    assert app.config["WTF_CSRF_ENABLED"] is False


def test_index_returns_application_status():
    """The main route should confirm that FlowYield is running."""
    app = create_app("testing")

    with app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.get_json() == {
        "application": "FlowYield",
        "status": "running",
    }


def test_unknown_configuration_is_rejected():
    """The factory should reject unsupported configuration names."""
    try:
        create_app("invalid")
    except ValueError as error:
        assert str(error) == "Unknown configuration: invalid"
    else:
        raise AssertionError("Expected ValueError for invalid configuration.")