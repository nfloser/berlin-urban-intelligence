# Security Policy

Berlin Urban Intelligence is a research-oriented urban intelligence platform. Security reports are welcome, but the repository must not be presented as a hardened multi-tenant or internet-facing municipal service without additional deployment controls.

## Supported versions

Security fixes are maintained on the default `main` branch and, when releases exist, on the latest supported release line. Older development snapshots and superseded releases may not receive backports.

The current package version is `0.1.x`; it is pre-1.0 research software and does not carry a production-security certification.

## Reporting a vulnerability

Please avoid publishing exploit details, credentials, tokens, private data or a working proof of concept in a public issue.

1. If GitHub shows **Report a vulnerability** for this repository, use GitHub private vulnerability reporting.
2. If private reporting is not available, open a minimal public issue that requests a private security contact and contains only the affected component and high-level impact category. Do not include secrets, exploit payloads or sensitive reproduction data there.
3. Include affected versions/commit, impact, prerequisites, a minimal safe reproduction and any suggested mitigation once a private channel is available.

Routine dependency-update requests without a demonstrated vulnerability can use normal issues or pull requests.

## Deployment threat boundary

The repository's default Docker Compose topology is intended for local/single-host research use:

- backend and dashboard host ports bind to `127.0.0.1` by default;
- the backend and refresh services run as an unprivileged application user and have `no-new-privileges` enabled;
- application code/configuration in the backend image remain root-owned while `/app/data` is the intended writable application path;
- the browser-facing nginx boundary emits a conservative baseline of `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` and `Permissions-Policy` headers; and
- the application API has **no built-in user authentication or authorization**.

A shared, remote or public deployment must therefore place the application behind a deployment-controlled HTTPS reverse proxy or gateway that provides authentication/authorization, TLS termination, request-size/rate controls and appropriate network access policy. Do not publish the Compose backend port directly to an untrusted network.

HSTS is not enabled by the repository because the local development topology uses plain HTTP; it belongs at a reverse proxy that guarantees HTTPS. A strict Content Security Policy is also deployment-specific because required MapLibre style/tile origins must be explicitly allow-listed rather than guessed.

## Secrets and logging

Do not commit provider tokens, credentials or private keys. Use deployment environment/secret-management facilities when a future source requires credentials.

Structured application logging uses an explicit context allow-list. Request bodies and query strings are not logged by the platform formatter, and raw exception messages/tracebacks are excluded because external exceptions can contain URLs or sensitive provider context.

## Dependency vulnerability policy

`.github/workflows/security.yml` performs scheduled/manual and relevant pull-request dependency audits for:

- the installed Python runtime dependency set, including `live` and `osm` extras;
- the frontend lockfile, including build dependencies; and
- the isolated Playwright/Axe browser-acceptance runner.

Known findings that reach the configured audit threshold fail the audit. A vulnerability may be ignored only through a narrowly scoped repository change that names the advisory, explains exploitability in this project's threat model, records the available fix or blocking dependency, and states an explicit review/removal condition. Silent or blanket vulnerability suppression is not acceptable.

## Security scope

A green dependency audit, passing tests or these baseline controls do not prove absence of vulnerabilities. Provider integrity, scientific validity, municipal-authority status, denial-of-service resistance, multi-tenant isolation, formal penetration testing and regulatory certification remain outside the current project guarantee unless separately implemented and evidenced.
