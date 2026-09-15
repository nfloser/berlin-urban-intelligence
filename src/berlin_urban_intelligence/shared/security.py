"""Security defaults shared by direct API and deployment boundaries."""

from __future__ import annotations

from collections.abc import Mapping

from starlette.responses import Response

BASELINE_SECURITY_HEADERS: Mapping[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


def apply_baseline_security_headers(response: Response) -> None:
    """Apply headers that are safe for both local HTTP and TLS-terminated deployments.

    HSTS and CSP are intentionally deployment-specific. HSTS is only valid once HTTPS is
    guaranteed, while the dashboard's MapLibre style/tile origins must be allow-listed before a
    useful CSP can be enforced.
    """

    for name, value in BASELINE_SECURITY_HEADERS.items():
        response.headers[name] = value
