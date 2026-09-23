# Demo walkthrough (approximately 7 minutes)

1. **00:00-00:45 - Architecture.** Explain React/Vite, Python FastAPI, SQLAlchemy, PostgreSQL and the shared-schema tenant model. Mention the intentional Python substitution for Node.
2. **00:45-01:30 - Authentication/dashboard.** Log in to `acme` as `admin@acme.test`. Explain active users, campaign totals, open/critical events, seven-day activity and recent events. Refresh to show live API-backed data.
3. **01:30-03:00 - Campaigns.** Create a draft campaign, edit its description, assign a user, start it, and complete it. Show search/status filters/pagination. Open its details and remove an assignment. Demonstrate an invalid transition through Swagger returning 409.
4. **03:00-04:00 - Events.** Report a security event, filter by severity/status, move it to investigating and then resolved. Refresh the dashboard to show changed counts.
5. **04:00-05:00 - Users and RBAC.** Create a user, update role, deactivate. Sign out, log in as manager and then regular user. Explain unavailable actions and assigned-only campaign visibility; show backend 403 for an unauthorized action.
6. **05:00-06:00 - Tenant isolation.** Use a Nexus campaign ID recorded while logged in to Nexus. With an Acme token, GET/PATCH that campaign in Swagger and show 404. Explain why changing IDs or sending tenantId cannot bypass scope. Show the automated database constraint test.
7. **06:00-07:00 - Audit and delivery.** Return as admin to audit history. Show recorded campaign/user/event/login actions. Explain immediate logout revocation, README setup, migrations and test results. Mention production extensions and known limits honestly.

Use only seeded/demo data. Keep `.env`, bearer tokens and production account information out of the recording. In Swagger, copy a demo login token into Authorize, then clear it after the demonstration. Record the resulting browser/API output rather than just code screenshots.
