# Cloud Deployment

Two deployment paths. Approach A is the recommended one for a student
project — genuinely free, no credit card. Approach B maps the same
architecture onto AWS for anyone who wants the extra resume line.

## Approach A — Free-tier deployment (recommended)

**Database + Storage: Supabase (free tier)**
1. Create a project at supabase.com.
2. In the SQL editor or via `psycopg2`, the app auto-creates its schema on
   first connection (`DatabaseService._init_schema`) — no manual migration
   needed.
3. In Storage, create a private bucket matching `SUPABASE_BUCKET`
   (default `assignment-submissions`).
4. Copy `Project URL`, `anon public key`, and `service_role key` into your
   backend's `.env`.

**Backend: Render or Railway (free tier)**
1. Push this repo to GitHub.
2. Create a new Web Service pointing at the repo, root directory the repo
   root, start command `gunicorn backend.app:app` (add `gunicorn` to
   `requirements.txt` for production — Flask's dev server is not meant for
   production traffic).
3. Set environment variables from `.env.example`, with:
   ```
   APP_ENV=production
   CLOUD_PROVIDER=supabase
   DATABASE_URL=<your Supabase Postgres connection string>
   SECRET_KEY=<a long random value — generate with python -c "import secrets; print(secrets.token_urlsafe(48))">
   SUPABASE_URL=...
   SUPABASE_ANON_KEY=...
   SUPABASE_SERVICE_ROLE_KEY=...
   CORS_ORIGINS=https://<your-frontend-domain>
   ```
4. Deploy. Confirm `GET /api/health` responds `{"status":"ok","cloud_provider":"supabase"}`.

**Frontend: Vercel or Netlify (free tier)**
1. Import the repo, set the project root to `frontend/`.
2. Build command `npm run build`, output directory `dist`.
3. Set an environment variable or edit `vite.config.js`'s proxy target for
   production so API calls go to your deployed backend URL instead of
   `localhost:8000` (or serve the frontend from the same domain behind a
   reverse proxy, if your host supports it, to avoid CORS entirely).
4. Deploy. The static frontend is automatically served through the host's
   CDN.

## Approach B — AWS-mapped deployment

Maps every piece of this architecture onto an AWS-native equivalent:

| This project's component | AWS equivalent |
|---|---|
| `cloud/database_service.py` (Postgres mode) | Amazon RDS for PostgreSQL |
| `cloud/storage_service.py` (Supabase Storage mode) | Amazon S3 (swap the `SupabaseStorageBackend` for a boto3-based `S3StorageBackend` implementing the same `upload/download/get_access_url` interface — signed URLs become S3 pre-signed URLs) |
| Flask backend | AWS Lambda behind API Gateway (serverless), or App Runner / an EC2 Auto Scaling Group (always-on) |
| `cloud/auth_service.py` (JWT mode) | Amazon Cognito, if you want managed auth instead of hand-rolled JWT |
| Frontend static build | S3 + CloudFront (CDN) |
| `backend/middleware/error_handler.py` logging | CloudWatch Logs |
| `GET /api/health` | CloudWatch/ALB health checks |

This is intentionally **not** the default build target for this project —
it requires more setup (IAM roles, VPC/security groups if using RDS) and
most AWS free-tier signups require a credit card, whereas Approach A is
genuinely free and gets you deployed faster. Approach B is worth doing
*after* Approach A works, as a "here's how I'd take this to a larger
provider" exercise for interviews.

## Post-deployment checklist

- [ ] `GET /api/health` returns `200` from the deployed backend URL
- [ ] Registering a teacher without the invite code is rejected
- [ ] A file uploaded through the deployed frontend appears in Supabase
      Storage (or S3) under the expected `assignments/.../` path
- [ ] `.env` values are set through the platform's secrets UI, never
      committed to the repo
- [ ] `CORS_ORIGINS` on the backend matches the deployed frontend's real
      domain (not `localhost`)
