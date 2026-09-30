# Cloud Computing Concepts — Where Each One Appears in This Project

Every concept is named against an actual file/function in this repo, not
described in the abstract.

| Concept | Where it appears |
|---|---|
| **Cloud Computing** (general) | The whole app is designed to run against hosted services rather than a single fixed machine: `cloud/database_service.py` and `cloud/storage_service.py` both support a real managed cloud backend, selected purely by `.env`. |
| **SaaS** | The deployed portal itself — students and teachers use it as a hosted service through a browser, with no install. |
| **PaaS** | The deployment targets in `docs/DEPLOYMENT.md` (e.g. Render/Railway for the backend, Vercel/Netlify for the frontend) are Platform-as-a-Service: you deploy code, the platform manages the OS/runtime. |
| **IaaS** (where applicable) | The AWS-mapped deployment option (`docs/DEPLOYMENT.md`, Approach B) touches IaaS-adjacent services like EC2 if chosen over serverless, where you manage more of the stack yourself. |
| **Cloud Database** | `cloud/database_service.py` — same code runs against local SQLite or cloud PostgreSQL (Supabase), switched by `DATABASE_URL`/`CLOUD_PROVIDER`. |
| **Object Storage** | `cloud/storage_service.py` — `LocalStorageBackend` (disk) and `SupabaseStorageBackend` (S3-compatible cloud storage) implement the same `upload/download/get_access_url` interface. |
| **Authentication** | `cloud/auth_service.py` (`create_access_token`, `decode_access_token`, password hashing) plus `POST /api/register` and `POST /api/login`. |
| **Authorization** | `backend/middleware/auth_middleware.py` — `require_role(...)` reads the role claim signed into the JWT and blocks any route the caller's role isn't listed for. |
| **Role-Based Access Control** | Every route is decorated with `@require_role("teacher")`, `@require_role("student")`, or left open to any authenticated user (e.g. viewing an assignment). See `docs/API_REFERENCE.md` for the full table. |
| **REST API** | `backend/routes/*.py` — resource-oriented endpoints (`/api/assignments`, `/api/submissions/{id}`) using GET/POST/PUT/DELETE and standard status codes. |
| **Client-Server Architecture** | React frontend (`frontend/`) never accesses the database or storage directly — it only calls the Flask REST API (`backend/`). |
| **Serverless Computing** | Not used in the local/Flask build, but the AWS deployment option maps the backend to AWS Lambda behind API Gateway — see `docs/DEPLOYMENT.md`. |
| **Scalability** | Stateless Flask app (all state in the DB/storage, not in server memory except the in-process rate limiter) means you can run many instances behind a load balancer. See `docs/SCALABILITY.md`. |
| **Elasticity** | Object storage and a managed cloud database both grow with usage automatically — no manual disk resizing, unlike the local-disk fallback. |
| **Availability** | A managed Postgres/Supabase instance and object store both offer replication/uptime guarantees that a single local SQLite file does not — discussed in `docs/SCALABILITY.md` and `docs/DEPLOYMENT.md`. |
| **Load Balancing** | Discussed as part of the 100,000-student scaling scenario in `docs/SCALABILITY.md` — multiple stateless backend instances behind a load balancer. |
| **CDN** | Frontend static assets (the built React app) are served through a CDN-backed static host (Vercel/Netlify/CloudFront) — see `docs/DEPLOYMENT.md`. |
| **API Gateway** | The AWS deployment option routes all API calls through Amazon API Gateway in front of the backend compute — see `docs/DEPLOYMENT.md`. |
| **Environment Variables** | `backend/config.py` reads every configurable value (`DATABASE_URL`, `SECRET_KEY`, `SUPABASE_*`, etc.) from the environment via `python-dotenv`; nothing sensitive is hardcoded. |
| **Secrets Management** | `.env` is git-ignored (`.gitignore`); `.env.example` documents every variable without real values; `backend/config.py` refuses to start in production with a placeholder `SECRET_KEY`. |
| **Logging** | `backend/middleware/error_handler.py` logs every unhandled exception server-side (`logger.exception(...)`) while returning a generic message to the client. |
| **Monitoring** | `GET /api/health` gives a liveness/readiness endpoint suitable for uptime monitors or a load balancer health check. |
| **Backup** | Discussed in `docs/SCALABILITY.md` and `docs/DEPLOYMENT.md` — a managed Postgres/Supabase instance provides automated backups that a local SQLite file does not. |
| **CI/CD** | The repo structure (`tests/`, `requirements.txt`) is ready to plug into a GitHub Actions workflow that runs `pytest` on every push — see `docs/GITHUB_STRATEGY.md` for the suggested commit history that sets this up next. |
| **Cloud Deployment** | Two full deployment paths (free-tier and AWS-mapped) are documented in `docs/DEPLOYMENT.md`. |
