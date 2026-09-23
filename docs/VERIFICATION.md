# Local verification

- Backend integration/security/configuration suite: 20 tests passed on SQLite with foreign keys enabled, including organization signup, duplicate ID handling, new-tenant isolation and existing-session separation.
- Alembic migration upgrade and idempotent demo seed: passed on SQLite.
- Alembic model/schema comparison: no pending changes.
- TypeScript type checking: passed.
- Home page redesign and organization onboarding: TypeScript passed after integration. Browser automation reported no available browser; visual verification remains pending. The supplied logo is represented by a recreated SVG mark rather than an original local image file.
- Frontend dependencies: installed successfully; npm reported zero vulnerabilities at installation time.
- Frontend production build: blocked at Vite/esbuild launch by sandbox `EPERM`. TypeScript finished successfully before that step. The requested elevated build was declined; production bundling is not verified.
- Browser workflows: not verified because the Vite server hit the same process-launch restriction. The running backend was verified using real HTTP requests.
- Live HTTP smoke checks: health, login, current user, dashboard, campaigns, events, users, audit, OpenAPI and logout/token revocation passed.
- PostgreSQL migration SQL: Alembic compiled the complete schema for the PostgreSQL dialect successfully (offline; no connection or runtime claim).
- PostgreSQL runtime verification: connected to the user-created `DeepTrace` database using separate `DB_*` settings. Applied initial migrations to the empty database, seeded demo tenants, confirmed model/schema parity, and verified login and dashboard requests returned 200 against PostgreSQL.
- Database configuration: two tests passed for separate-field construction, special-character password encoding, and explicit URL precedence.
- Docker Compose runtime and GitHub Actions: not run locally. Docker is not installed in the current environment; CI runs after repository publication.

SQLite tests and PostgreSQL smoke checks do not establish concurrent locking behavior. The included CI uses a dedicated PostgreSQL test database for the full integration suite.
