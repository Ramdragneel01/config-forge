from __future__ import annotations

import importlib

from fastapi.testclient import TestClient
import pytest


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "config_forge_test.sqlite3"
    monkeypatch.setenv("CONFIG_FORGE_DB_PATH", str(db_path))

    import app.main as main_module

    importlib.reload(main_module)

    with TestClient(main_module.app) as test_client:
        yield test_client


def test_create_and_validate_success(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/configs",
        json={
            "service_name": "risk-router",
            "environment": "staging",
            "provider": "openai",
            "parameters": {
                "model": "gpt-4o-mini",
                "temperature": 0.3,
                "timeout_ms": 1200,
                "max_tokens": 1024,
            },
            "policy": {
                "required_keys": ["model", "temperature", "timeout_ms"],
                "forbidden_keys": ["debug_mode"],
                "max_temperature": 0.8,
                "min_timeout_ms": 300,
                "max_timeout_ms": 5000,
            },
        },
    )
    assert create_response.status_code == 200
    config_id = create_response.json()["id"]

    validate_response = client.post(f"/api/v1/configs/{config_id}/validate")
    assert validate_response.status_code == 200
    payload = validate_response.json()
    assert payload["passed"] is True
    assert payload["issues"] == []


def test_validation_failure_for_missing_keys(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/configs",
        json={
            "service_name": "summarizer",
            "environment": "prod",
            "provider": "azure-openai",
            "parameters": {
                "model": "gpt-4.1",
                "timeout_ms": 200,
                "mock_mode": True,
            },
            "policy": {
                "required_keys": ["model", "temperature", "timeout_ms"],
                "forbidden_keys": ["debug_mode"],
                "max_temperature": 1.0,
                "min_timeout_ms": 300,
                "max_timeout_ms": 5000,
            },
        },
    )
    assert create_response.status_code == 200
    config_id = create_response.json()["id"]

    validate_response = client.post(f"/api/v1/configs/{config_id}/validate")
    assert validate_response.status_code == 200
    payload = validate_response.json()
    assert payload["passed"] is False
    assert "Missing required key: temperature" in payload["issues"]
    assert "azure-openai provider requires api_version" in payload["issues"]


def test_promote_requires_passed_validation(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/configs",
        json={
            "service_name": "classifier",
            "environment": "staging",
            "provider": "openai",
            "parameters": {
                "model": "gpt-4o-mini",
                "temperature": 0.4,
                "timeout_ms": 1500,
            },
        },
    )
    config_id = create_response.json()["id"]

    blocked = client.post(
        f"/api/v1/configs/{config_id}/promote",
        json={
            "target_environment": "staging",
            "rollout_percent": 20,
            "change_ticket": "CHG-1001",
            "approved_by": "oncall-sre",
        },
    )
    assert blocked.status_code == 409

    client.post(f"/api/v1/configs/{config_id}/validate")

    allowed = client.post(
        f"/api/v1/configs/{config_id}/promote",
        json={
            "target_environment": "production",
            "rollout_percent": 25,
            "change_ticket": "CHG-1002",
            "approved_by": "platform-lead",
        },
    )
    assert allowed.status_code == 200
    body = allowed.json()
    assert body["target_environment"] == "production"
    assert body["rollout_percent"] == 25
