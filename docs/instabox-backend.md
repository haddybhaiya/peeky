# BYO InstaBox backend foundation

This post-MVP increment introduces a shared sandbox backend contract and an
explicit, read-only account check for a user-supplied InstaBox account. Docker
remains the only audit executor. It does not create or delete machines, execute
cloud commands, upload repositories, open SSH connections or alter account state.

## Commands and configuration

```bash
peeky doctor                              # existing Docker check
peeky doctor --backend docker --json
peeky doctor --backend instabox --json    # opt-in account metadata reads
peeky audit https://github.com/OWNER/REPO --backend docker --approve
```

Supply the key through the invoking process's environment or a secret manager.
There is no API-key CLI argument, automatic `.env` loading or credential file
persistence. The existing `.env.example` and `--env-file` belong to the separate
Gemma model workflow; do not put InstaBox fields in that model configuration.

| Environment variable | Meaning |
|---|---|
| `INSTABOX_API_KEY` | Required for the selected InstaBox doctor only; a 52-character `ibk_` API key |
| `INSTABOX_API_URL` | Optional; only the exact official `https://api.instabox.sh` origin is accepted |
| `PEEKY_INSTABOX_TEMPLATE` | Optional catalog template ID, default `ci`; the check requires an offered x86_64 template |

Use a key authorized to read templates and usage (`machines:read` or
`images:read`, per the provider documentation). This increment needs no write or
delete permission. Docker commands and source inspection do not load this key or
contact InstaBox. There is no backend auto-detection or implicit fallback.

## Meaning of the result

The selected doctor performs at most three authenticated GETs, in order:

1. `/v1/me`: validate identity and any reported invitation/activation gate.
2. `/v1/templates`: check the selected template's catalog availability and architecture.
3. `/v1/usage`: check machine-count headroom against the reported account limit.

It stops on the first failure and never retries automatically. A zero machine
limit is considered unlimited only when the provider explicitly identifies it in
`limits.unlimited`. Missing disambiguation produces `LIMIT_UNKNOWN`.

InstaBox's identity response does not expose the key's scopes. Read success does
not establish create/delete permission, subscription access to a template or
provider physical capacity. Those checks remain `not_verified` in JSON. This is
account metadata, not a provisioning guarantee or a target audit result.

`preflight_ok: true` and exit 0 mean these read-only checks passed. In this
foundation, `execution_supported` and `ready` always remain **false** for InstaBox,
with reason `PREFLIGHT_OK` and an explicit cloud-execution limitation. Configuration,
authentication, quota and service failures return exit 3 with a stable reason and
safe message. The default Docker doctor's existing text/JSON and exit behavior
remain unchanged.

`peeky audit … --backend instabox --approve` returns exit 3 before credentials,
source fetching/capture, Docker checks or evidence writes. Without `--approve`,
the existing approval gate returns exit 2 first. It cannot silently run locally.
No cloud execution or evidence schema is advertised by this increment.

## Transport and credential boundary

The standard-library client allows only the three exact GET paths above and the
fixed official HTTPS origin. Redirects are refused, TLS verification remains on,
and the trusted operator's configured proxy and CA setup is preserved. Use that
proxy setup only when trusted to handle the provider connection. Keys are sent in
`X-API-Key`, never in a URL. No provider body, login, email or CSRF token is printed;
output includes only controller-selected status, template, numeric account ID and
machine counts. Configuration repr hides the key, and valid InstaBox key patterns
are redacted even when no matching environment variable remains.

Each request has a five-second socket timeout and an elapsed deadline checked
between response reads, with a 256 KiB response-body budget. The deadline is not
an OS wall-clock limit: blocking I/O can overshoot it before control returns.
Duplicate JSON fields, non-finite values, malformed UTF-8/JSON and incomplete
required metadata fail closed. Error bodies and raw exception text never become
user-facing diagnostics. Non-200 responses close without reading their unused
bodies, preserving the known HTTP status even if an error body is oversized or
would stall. Responses close on success and failure.

These are controller account requests. No target code, README, model output or
repository input chooses provider URLs, permissions or lifecycle operations. The
Docker runner's pinned image, offline networking, isolation, budgets, cleanup and
schema 1.2 evidence policy remain in force.

## Foundation acceptance gates

| ID | Required behavior | Coverage |
|---|---|---|
| BF-001 | Shared backend interface; Docker delegates to the existing runner without changing source/image/time inputs | `test_backends.py`, existing real Docker integration |
| BF-002 | Explicit environment configuration; official origin only; no key in repr or config errors | `test_instabox_api.py` |
| BF-003 | Only bounded read-only account, template and usage GETs; no redirects, retries or mutations | `test_instabox_api.py`, `test_instabox_transport.py` |
| BF-004 | Account/template/quota failures are explicit; unknown permissions and unsupported execution never become ready | `test_instabox_backend.py` |
| BF-005 | Cloud audits fail before credentials, acquisition, execution and evidence; approval still comes first | `test_backend_cli.py` |
| BF-006 | Output omits provider secrets/PII; key patterns redact without the originating environment | backend/CLI/API tests, existing redaction/report tests |
| BF-007 | HTTP failures, malformed metadata, response limits, timeouts and unknown zero limits fail safely | API/transport/backend tests |
| BF-008 | Docker and URL audit/report behavior, default doctor output and installed artifact remain compatible | existing core/Docker suite, `test_backend_cli.py`, `scripts/smoke_wheel.py` |

Tests inject documented metadata and transport failures; the existing Docker
integration gate executes real containers.

## Cloud microVM execution lifecycle

With `--backend instabox --approve`, Peeky executes an approved audit step inside
an ephemeral InstaBox Firecracker microVM instead of local Docker. Docker remains
the default offline runner.

### Lifecycle stages

1. **Machine Provisioning (`POST /v1/machines`)**:
   - Machine is created using the selected template (default `ci`) and tagged with metadata (`managed_by: peeky-controller`).
   - Server-side auto-destroy TTL (300 seconds) is requested at creation time so orphaned VMs terminate automatically if network connection drops.
2. **Source Transfer (`PUT /v1/machines/{id}/files/{path}`)**:
   - Captured Git snapshot files are uploaded directly to `/workspace/{relpath}`.
   - Strict path traversal validation rejects paths escaping `/workspace` (e.g., `..`, leading slashes).
3. **Execution (`POST /v1/machines/{id}/exec`)**:
   - Command is executed with exact `argv` (no shell wrapping), working directory `/workspace`, and execution timeout budget (60s).
   - Execution stdout and stderr are captured with 64 KiB truncation limits.
4. **Guaranteed Disposal (`DELETE /v1/machines/{id}`)**:
   - Deletion is executed in a guaranteed `finally:` block regardless of command pass, fail, or exception.
   - Deletion checks confirm the machine is terminated (`204 No Content` or `404 Not Found`), ensuring no persistent machines remain.
5. **HMAC Provenance & Evidence (`evidence.json`)**:
   - Schema 1.2 evidence records `execution: "instabox-cloud-single-command"`, `backend: "instabox"`, `machine_id`, `template_id`, `cleanup_verified: true`, and controller HMAC signature.
   - All credentials (`INSTABOX_API_KEY`) and sensitive patterns are redacted before provenance recording.

## Cloud execution acceptance gates

| ID | Required behavior | Coverage |
|---|---|---|
| CL-001 | Ephemeral VM provisioning with template and auto-destroy TTL (300s) | `test_instabox_lifecycle.py`, `test_instabox_api.py` |
| CL-002 | Direct source snapshot upload to `/workspace` with path traversal rejection | `test_instabox_lifecycle.py`, `test_instabox_api.py` |
| CL-003 | Constrained shell-free argv execution with working dir `/workspace` and timeout | `test_instabox_lifecycle.py`, `test_instabox_api.py` |
| CL-004 | Guaranteed deletion in `finally:` block; cleanup verified or 404 handled | `test_instabox_lifecycle.py`, `test_instabox_backend.py` |
| CL-005 | Output streams bounded to 64 KiB; API key and secrets redacted from evidence | `test_instabox_lifecycle.py` |
| CL-006 | Schema 1.2 cloud provenance with `machine_id`, `template_id`, `cleanup_verified` | `test_instabox_lifecycle.py`, `test_evidence.py` |
| CL-007 | Strict machine ID validation (`r"^m_[A-Za-z0-9_-]{8,64}$"`) and error mapping | `test_instabox_api.py`, `test_instabox_lifecycle.py` |
| CL-008 | CLI audit executes cloud when approved; Docker remains default | `test_backend_cli.py` |

## Provider contract references

Checked against official documentation on 2026-11-05:

- [API overview](https://instabox.sh/docs/api.md)
- [Account API](https://instabox.sh/docs/api/account.md)
- [API key formats and scopes](https://instabox.sh/docs/api-keys.md)
- [OpenAPI specification](https://api.instabox.sh/v1/openapi.json)

These documents establish the implemented request contract; they do not establish
live account access, provider availability or future provisioning success.
