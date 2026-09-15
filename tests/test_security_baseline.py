import json
import logging

from fastapi.testclient import TestClient

from berlin_urban_intelligence.api.app import create_app
from berlin_urban_intelligence.shared.observability import JsonFormatter


def test_backend_responses_include_safe_baseline_security_headers() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"


def test_structured_formatter_drops_query_and_body_context() -> None:
    record = logging.LogRecord(
        name="berlin_urban_intelligence.security-test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="api_request",
        args=(),
        exc_info=None,
    )
    record.operation_id = "test-operation"
    record.http_method = "POST"
    record.http_path = "/api/v1/resilience/routes"
    record.query_string = "token=do-not-log-this"
    record.request_body = {"secret": "do-not-log-this-either"}

    payload = json.loads(JsonFormatter().format(record))

    assert payload["operation_id"] == "test-operation"
    assert payload["http_path"] == "/api/v1/resilience/routes"
    assert "query_string" not in payload
    assert "request_body" not in payload
    assert "do-not-log-this" not in json.dumps(payload)
