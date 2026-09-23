# Deep Trace Cybernetics

A multi-tenant security operations platform with **Python FastAPI**, **React / Vite / TypeScript**, and **PostgreSQL**. Includes JWT login, backend-enforced roles, campaign assignments, security events, tenant metrics, and audit history.

**Assessment stack deviation:** the supplied assessment asks for Node.js/Express. This implementation intentionally uses Python FastAPI, as requested by the project owner. Frontend and SQL requirements are retained. The UI uses custom responsive CSS rather than a CSS framework.

## Start with Docker (PostgreSQL)

Requires Docker Engine and Docker Compose v2.

```powershell
Copy-Item .env.example .env
# Edit .env: set POSTGRES_PASSWORD and JWT_SECRET before starting.
docker compose up --build
```

Generate a JWT secret with `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Use a URL-safe database password (letters, digits, hyphens, underscores); percent-encode reserved characters if constructing DATABASE_URL manually. Do not commit `.env`.

- UI: http://localhost:5173
- API documentation: http://localhost:8000/docs
- API health: http://localhost:8000/api/health

Compose waits for PostgreSQL, applies migrations, seeds the demo tenants, and starts the API and nginx frontend. Seed is idempotent and skips existing tenant slugs. Database data persists in the `postgres_data` volume. `docker compose down` stops the application without deleting that data. This Compose configuration is for local assessment/demo use; it intentionally creates demo accounts.

## Start locally without Docker

Requires Python 3.10+, Node.js 22, and an accessible PostgreSQL database. Create an empty database and a role that owns it using your PostgreSQL administration account:

```sql
CREATE USER deeptrace WITH PASSWORD 'choose-a-local-password';
CREATE DATABASE deeptrace OWNER deeptrace;
```

Backend, from the repository root:

```powershell
cd Backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Update DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD and JWT_SECRET in Backend/.env.
python -m alembic upgrade head
python -m app.seed
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

On macOS/Linux, use `source .venv/bin/activate` and `cp .env.example .env` instead. Run backend commands from `Backend/` so `.env` and `alembic.ini` resolve correctly.

Local database settings use separate `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` fields. Spaces around `=` are supported. Passwords are safely URL-encoded when constructing the connection string. An explicitly set `DATABASE_URL` takes precedence for Docker, CI, or SQLite previews; remove it to use the separate fields. Restart the backend after changing `.env`.

Frontend, in another terminal:

```powershell
cd Frontend
npm ci
npm run dev
```

Open **http://localhost:5173**. Vite proxies `/api` to `127.0.0.1:8000`, so no frontend environment changes are required. For a separate API origin, copy `Frontend/.env.example` to `.env`, set `VITE_API_URL`, and add your frontend origin to backend `CORS_ORIGINS`. A Vite environment value is public; never put secrets in it.

### Optional SQLite preview

PostgreSQL is the assessment database. If it is temporarily unavailable, SQLite supports a local functional preview and the default test suite. Its locking and concurrency semantics differ from PostgreSQL; use PostgreSQL for final validation and deployment.

```powershell
cd Backend
# Keep a valid JWT_SECRET in Backend/.env.
$env:DATABASE_URL = 'sqlite:///./preview.db'
python -m alembic upgrade head
python -m app.seed
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

This environment override applies to the current terminal. Remove it with `Remove-Item Env:DATABASE_URL` to return to PostgreSQL configuration.

## Demo credentials

Default password for seeded accounts: **`DemoPassword123!`**. Override using `SEED_PASSWORD` before the first seed. Changing that variable later does not reset existing passwords.

| Organization | Role | Email |
|---|---|---|
| `acme` | ADMIN | `admin@acme.test` |
| `acme` | MANAGER | `manager@acme.test` |
| `acme` | USER | `user@acme.test` |
| `nexus` | ADMIN | `admin@nexus.test` |
| `nexus` | MANAGER | `manager@nexus.test` |
| `nexus` | USER | `user@nexus.test` |

Each tenant has separate users, campaigns, assignments, events, and audit logs. New tenants can be created through the home page or the console's **Create organization** button. There is no cross-tenant super-admin API.

## Create an organization from the frontend

1. On the home page, choose **Create organization** or **Build your workspace**. Existing users can also choose **+ Create organization** in the sidebar.
2. Enter an organization display name and a unique organization ID, such as `apex-cybersecurity`. IDs use lowercase letters, digits, and hyphens. The form suggests an ID from the name; it remains editable.
3. Enter the first administrator's name, email, password (12+ characters), and password confirmation.
4. Submit. The backend atomically creates the tenant, hashes the password, creates its ADMIN, and records audit entries. Duplicate IDs return a helpful conflict message. New organizations start with no campaigns or events.
5. On the home page, successful creation opens sign-in with the new ID and email filled in. Enter the new password to open the new workspace.
6. When creating an organization from an existing session, the existing workspace remains active. Sign out and sign in with the new organization ID and admin credentials to enter the new workspace.

Public onboarding shares the login throttle budget. Email ownership verification/invitations are not implemented; this is a self-service assessment flow. The server always creates the first user as ADMIN of the newly created tenant and rejects caller-supplied tenant IDs.

The home page uses a responsive navy and cyan design, code-built secure-laptop illustration, and a vector interpretation of the supplied Deep Trace logo reference in `Frontend/public/deeptrace-mark.svg`. The source logo image was not present as a local project asset.

## Roles and behavior

| Capability | ADMIN | MANAGER | USER |
|---|---|---|---|
| Dashboard and tenant event list | Yes | Yes | Yes |
| View campaigns | All in tenant | All in tenant | Assigned only |
| Create/update campaigns, manage assignments | Yes | Yes | No |
| Delete campaigns | Yes | No | No |
| Create/update events | Yes | Yes | No |
| Basic user list | Yes | Yes | Yes |
| Create users/change roles/deactivate/reset passwords | Yes | No | No |
| Audit history | Yes | No | No |

Regular-user dashboard campaign counts and recent campaigns follow assignment visibility. Event and active-user counts are tenant-wide. Recent dashboard activity contains security events and accessible campaigns, not restricted audit records.

Campaign transitions: `DRAFT -> ACTIVE -> COMPLETED`; `DRAFT` and `ACTIVE` may transition to `CANCELLED`. Completed/cancelled states cannot reopen. Same-state edits are accepted. Security events transition `OPEN -> INVESTIGATING -> RESOLVED`, or `OPEN -> RESOLVED`; resolved events cannot reopen. Descriptions/severity can still be corrected.

Users are deactivated rather than deleted. An administrator cannot demote/deactivate their own account. Tenant-row locks serialize role updates on PostgreSQL; an active administrator must remain. Password, role, and account-status changes revoke existing sessions.

## Architecture

```text
Frontend/src/
  App.tsx          Login, authenticated shell, role-aware navigation
  Dashboard.tsx    Metrics, event activity, campaign spotlight
  Records.tsx      Lists, filters, pagination, forms, assignments
  api.ts           Typed HTTP client and session handling
  components.tsx   Accessible dialogs, badges, paging, state components
Backend/app/
  main.py          Application, request IDs, errors, CORS, health
  config.py        Validated environment configuration
  database.py      SQLAlchemy engine and request-scoped sessions
  models.py        Six entities and relational constraints
  schemas.py       Strict validated request schemas
  security.py      Password hashing, JWT validation, role dependencies
  services.py      Tenant queries, pagination, audit and serialization
  routes/          Authentication, campaigns, events, users, dashboard
  seed.py          Idempotent two-tenant demo fixture
Backend/migrations/ Versioned Alembic schema
Backend/tests/      Integration and security tests
```

The six entities are tenants, users, campaigns, campaign members, security events, and audit logs. Mutations and their audit records commit in the same transaction. ORM queries are parameterized; client-controlled sort fields use an allowlist. Pagination, search, filtering, and sorting happen server-side with a maximum page size of 100. Database uniqueness and check constraints back up application validation. The frontend includes responsive layouts, empty/loading/error states, keyboard-accessible native dialogs, and destructive-action confirmation.

### Tenant isolation and security

- JWT contains user ID, token version, issuer, audience, issued-at, and expiry. It does not accept frontend-provided roles or tenant IDs. Every protected request reloads the active user from the database and uses the stored tenant and role.
- Every resource lookup is scoped by authenticated tenant before selecting an ID. Cross-tenant IDs return 404. All lists, counts, assignments, and audit queries use this scope.
- Composite foreign keys `(tenant_id, campaign_id)` and `(tenant_id, user_id)` stop cross-tenant assignments even if application validation is bypassed. Campaign creators are similarly tenant-constrained. Assignment rows cascade when campaigns are deleted; audit history remains.
- Passwords use scrypt (`N=32768`, `r=8`, `p=1`) with random 16-byte salts and constant-time comparison. No passwords/hashes are returned through APIs or written to audit logs. Unknown accounts use a dummy hash to reduce timing differences.
- Access JWTs expire after 30 minutes by default. Logout increments the user's token version and revokes **all** sessions. No refresh tokens are issued.
- Frontend tokens are kept in sessionStorage and cleared on 401. This allows reloads but remains vulnerable to same-origin XSS. React escapes text; no raw user HTML is rendered. A stricter production design can use HttpOnly cookies with CSRF protection or memory-only access tokens with a secure refresh cookie.
- Login is limited to 10 attempts/minute per direct client IP per process. It does not trust arbitrary forwarding headers. Use a shared Redis limiter and a configured trusted reverse proxy in production; nginx proxy traffic currently shares a limiter bucket.
- `.env` is ignored, secrets are required, CORS uses explicit origins, errors avoid database details, request IDs are returned, and nginx adds a CSP. The app does not provide PostgreSQL RLS; read isolation is enforced in the service layer and covered by tests. Add RLS for defense in depth when hardening deployment.

## API overview

Interactive schemas and examples: `/docs`; machine-readable contract: `/openapi.json`.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/login` | Organization/email/password login |
| POST | `/api/organizations` | Create a tenant and its first administrator |
| GET | `/api/auth/me` | Current user and organization |
| POST | `/api/auth/logout` | Revoke current user's sessions |
| GET | `/api/dashboard` | Scoped metrics and recent events/campaigns |
| GET, POST | `/api/campaigns` | List/create |
| GET, PATCH, DELETE | `/api/campaigns/{id}` | Details/update/delete |
| POST | `/api/campaigns/{id}/members` | Assign `{ "user_id": 3 }` |
| DELETE | `/api/campaigns/{id}/members/{user_id}` | Remove assignment |
| GET, POST | `/api/security-events` | List/create |
| GET, PATCH | `/api/security-events/{id}` | View/update |
| GET, POST | `/api/users` | List/create |
| PATCH | `/api/users/{id}` | Update profile, role, active state or password |
| GET | `/api/audit-logs` | Admin-only scoped history |

Lists accept `page`, `page_size`, `q`, `sort`, and `order=asc|desc`. Campaigns accept `status`; events accept `status` and `severity`; users accept `role` and `active`. Unknown/invalid sort fields fail with 422. Responses use `{items, total, page, page_size}`. Create returns 201, delete/logout 204, validation 422, invalid credentials 401, forbidden roles 403, unavailable resources 404, conflicts 409, and login throttling 429.

## Verification

```powershell
cd Backend
python -m pytest -q
python -m alembic check
cd ../Frontend
npm run build
```

The default tests use isolated SQLite databases and enforce foreign keys. They cover cross-tenant reads/updates/deletes, tenant list/count isolation, database-level assignment constraints, roles, campaign assignment visibility, audit isolation, state transitions, field injection, SQL search injection, input validation, pagination, password hashing, login throttling, user deactivation, and JWT expiry/revocation.

For the same tests on PostgreSQL, create a **dedicated empty database whose name ends in `_test`**, then set `TEST_DATABASE_URL` to its URL. Tests create and drop application tables in that database. Never point it at development or production data. The CI workflow provisions its own PostgreSQL service, verifies migration upgrade/seed/downgrade and model parity, runs the tests, and builds the frontend.

Local verification status is recorded in `docs/VERIFICATION.md`. Docker and hosted CI need to be run in an environment where those services are available; included configuration is not evidence of a successful hosted run.

## Engineering notes

**Scaling to 1,000 tenants / 1M users:** run stateless API replicas behind a load balancer; size PostgreSQL connection pools via PgBouncer; keep tenant-leading indexes and inspect slow queries with EXPLAIN. Replace repeated dashboard aggregates with tenant-keyed cached summaries, use keyset pagination on large event/audit streams, and add an index on `(tenant_id, user_id, campaign_id)` for heavy assignment lookups. Move notifications/export work to a queue. Partition audit/event tables by time and archive old partitions. Cache keys must include tenant and authorization scope. Add read replicas for suitable read paths, tenant quotas, tracing, RLS, and tenant-aware operational metrics. Consider tenant sharding only after measuring capacity and noisy-neighbor behavior.

**JWT revocation:** implemented with database token versions, active-user checks, and short expiry. This provides immediate user-wide revocation without storing every token. For individual sessions, add a session identifier (`jti`), a session table or Redis denylist with TTL, rotating refresh-token families, and reuse detection. Cache permission checks only with reliable invalidation.

**Investigating many production 500s:** correlate returned `X-Request-ID` with structured request logs and exception traces; quantify affected routes, tenants, release versions, latency, and time windows. Inspect deployment changes, DB connectivity/pool saturation, locks, query plans, migration state, CPU/memory, and downstream failures. Reproduce with sanitized input; never log bearer tokens/passwords. Roll back or disable a faulty feature when appropriate, add focused regression coverage, and verify recovery using error-rate/latency dashboards. Alert on elevated 5xx and latency before reports arrive.

## Submission checklist

- Run with PostgreSQL and perform the walkthrough in `docs/DEMO.md`.
- Push the complete repository including migrations, README, environment examples and lockfile; exclude secrets, dependencies, local databases and build outputs.
- Record a 5-10 minute demonstration; upload it to Google Drive and verify reviewer access.
- Submit the GitHub repository URL and video URL. Repository publishing, account uploads, and video recording have not been performed automatically.
