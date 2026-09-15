# Security baseline

Berlin Urban Intelligence is currently a research-oriented single-host application. This document records the implemented security controls, the deployment trust boundary and the controls that remain the responsibility of a real public deployment. It is not a penetration-test report or security certification.

## Threat boundary

The repository-managed topology consists of:

1. a React/MapLibre dashboard served by nginx;
2. a FastAPI backend;
3. a background refresh process using the same backend image; and
4. host-mounted persisted data under `./data`.

The default Compose file binds the dashboard and direct backend host ports to loopback only (`127.0.0.1:8080` and `127.0.0.1:8000`). This prevents an ordinary `docker compose up` from unintentionally exposing either service on every host interface.

The application does not implement user accounts, sessions, RBAC or API authentication. Therefore a shared, remote or internet-facing deployment is **not** secure merely because the containers start successfully. Such a deployment requires an external trusted gateway/reverse proxy that terminates HTTPS and enforces authentication/authorization, rate/request-size controls and the intended network policy.

## Container and filesystem review

### Backend and refresh

The Python image creates UID `10001` (`appuser`) and switches to that user before the application starts. Application source, scripts, configuration and knowledge files stay root-owned in the image. Only `/app/data` and the application user's home directory are explicitly made writable for `appuser`.

Both backend and refresh services use Docker's `no-new-privileges:true` security option. Neither service uses privileged mode, host networking or explicit Linux capability additions.

The `./data:/app/data` bind mount is intentionally writable because the refresh process publishes validated persisted state and generated RDF there. This means host filesystem permissions and backups for `./data` are part of the operator's security responsibility. The application does not treat that directory as a secret store.

### Frontend

The frontend uses the official nginx image and serves compiled static assets plus reverse-proxy routes to the backend. The repository does not currently replace the image's normal nginx master/worker privilege model with a custom unprivileged image. No privileged container flags or host filesystem mounts are added.

For the current local research topology this is an explicit accepted boundary, not a statement that the frontend container has been hardened against every container-escape class. A more restrictive production platform may run an unprivileged nginx variant and/or a read-only root filesystem after validating required runtime paths.

## HTTP boundary and browser headers

The browser-facing nginx response boundary emits:

| Header | Value | Purpose |
|---|---|---|
| `X-Content-Type-Options` | `nosniff` | Prevent browser MIME-type sniffing. |
| `X-Frame-Options` | `DENY` | Prevent framing/clickjacking for the current standalone dashboard. |
| `Referrer-Policy` | `no-referrer` | Avoid sending navigation referrer information. |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | Disable browser capabilities the dashboard does not require. |

These values are tested through the composed Playwright path rather than by inspecting nginx configuration text alone.

### Why HSTS is not set here

The repository's local topology intentionally uses HTTP. `Strict-Transport-Security` is only safe when the actual public host is guaranteed to remain HTTPS-only. A production TLS terminator should set HSTS according to its domain/subdomain policy.

### Why a strict CSP is not guessed

MapLibre styles, glyphs, sprites and tiles can originate from deployment-selected external origins. A useful Content Security Policy must explicitly model those origins. Shipping a permissive wildcard CSP would provide little protection; shipping an incorrect restrictive CSP would break the analytical map. Public deployments should define a tested CSP at the deployment boundary after fixing the intended style/tile providers.

## Logging and sensitive context

`JsonFormatter` serializes a fixed context allow-list (`operation_id`, agent/source identifiers, error state, duration and selected HTTP metadata). Unknown `LogRecord` attributes such as query strings or request bodies are ignored.

Raw exception messages and tracebacks are not emitted by the platform JSON formatter. When exception information is present, only the exception class name is retained. This avoids accidental disclosure if a provider library places a URL, token-like query parameter or remote payload detail into an exception message.

This guarantee applies to the platform structured formatter. Future third-party logging integrations must be reviewed separately and must not reintroduce request/provider payload logging.

## Dependency vulnerability auditing

`.github/workflows/security.yml` is deliberately separate from deterministic correctness CI and runs:

- on relevant dependency/workflow pull-request changes;
- weekly; and
- on manual dispatch.

The Python audit creates an isolated environment containing the same `live` and `osm` extras installed by the runtime Dockerfile, then uses pinned `pip-audit` tooling from outside that environment to scan the installed runtime dependency path.

The frontend audit runs `npm audit --audit-level=high` against the committed lockfile, including development/build dependencies. The isolated browser-acceptance runner is audited separately because its pinned Playwright/Axe packages are intentionally not part of the dashboard lockfile.

The acceptance runner was updated from `@playwright/test@1.55.0` to `1.63.0`; the latter was the current stable npm release during the 2026-09-15 security review. `@axe-core/playwright` remains pinned to the current stable `4.13.0`. Version freshness alone is not treated as proof of safety: the security workflow's actual audit result is the gate.

Audit policy is fail-by-default for findings at the configured threshold. Any advisory exception must be explicit, advisory-specific and documented with exploitability reasoning, fix availability and a review/removal condition. Blanket ignore lists are not part of the baseline.

## Secret handling

The current configured public sources do not require committed credentials. Future credentials must be supplied through deployment environment/secret mechanisms and must not be placed in source files, fixtures, generated state, browser bundles or documentation.

`scripts/check_secrets.py` remains part of protected backend CI as a repository-specific guard. It complements dependency auditing; neither mechanism replaces proper secret management.

## Security verification

The current baseline is considered verified only when all of the following pass on the candidate head:

- Python/backend format, lint, strict types and tests;
- explicit security regression tests for loopback exposure and structured-log redaction;
- frontend tests/build;
- Docker Compose validation and image builds;
- composed browser acceptance of the nginx security headers;
- Python runtime vulnerability audit;
- frontend lockfile vulnerability audit; and
- isolated Playwright/Axe dependency audit.

A successful result demonstrates only the controls above. It does not establish formal production hardening, authenticated multi-user isolation, DDoS resilience or absence of unknown vulnerabilities.

## Reporting

Repository-level reporting instructions and supported-version policy are maintained in [`../SECURITY.md`](../SECURITY.md).
