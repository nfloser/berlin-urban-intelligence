import json
import logging
from pathlib import Path

import yaml

from berlin_urban_intelligence.shared.observability import JsonFormatter

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_default_compose_only_publishes_http_ports_on_loopback() -> None:
    compose = yaml.safe_load((PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8"))

    assert compose["services"]["backend"]["ports"] == ["127.0.0.1:8000:8000"]
    assert compose["services"]["frontend"]["ports"] == ["127.0.0.1:8080:80"]
    assert "ports" not in compose["services"]["refresh"]


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
