# Security

## Password storage
Never stored or logged in plain text. `cloud/auth_service.hash_password`
uses Werkzeug's salted **scrypt** hasher (`generate_password_hash`); login
compares with `check_password_hash`, which is constant-time and salt-aware.

## Authentication tokens (JWT)
Issued by `cloud/auth_service.create_access_token` with an expiry
(`ACCESS_TOKEN_EXPIRE_MINUTES`, default 60) baked into the `exp` claim, and
signed with `SECRET_KEY` (HS256). `decode_access_token` verifies the
signature and expiry on every request — a tampered token fails signature
verification, not just a client-side check.

## Logout / token revocation
JWTs are normally stateless (valid until they expire, even after
"logging out"). To make logout actually work, `POST /api/logout` writes a
SHA-256 hash of the token to a `revoked_tokens` table
(`backend/utils/security.hash_token` — the raw token itself is never
stored). `require_auth` checks this table on every request, so a revoked
token is rejected immediately, not just ignored client-side.

## Role-Based Access Control (RBAC)
The role claim is signed inside the JWT at login/registration time —
`backend/middleware/auth_middleware.require_role(*roles)` checks it on the
server for every protected route. A student cannot edit their own token to
claim `role: teacher` without invalidating the signature, and even a valid
teacher token is still checked for *ownership* (their course, their
assignment) before any write, not just their role — see
`backend/services/*.py` for the ownership checks alongside the role checks.

## File upload validation
`backend/utils/validators.py` does three checks, not one:
1. **Extension** must be in the assignment's allowed list.
2. **Size** must be under the assignment's (and a hard 25MB) limit.
3. **Content (magic bytes)** must actually match the claimed extension —
   e.g. a real PDF starts with `%PDF-`. This stops a renamed executable
   (`virus.exe` → `homework.pdf`) from being accepted just because the
   filename looks right.

Filenames are also sanitized (`sanitize_filename`) to strip path separators
and unsafe characters before being used to build a storage path — this is
what defends against **path traversal** (`../../etc/passwd` style attacks).

## Object storage access control
- Local mode: no route serves the upload folder as static files. The only
  read path is the authenticated, ownership-checked download route.
- Cloud mode: the Supabase bucket is private; downloads use short-lived
  **signed URLs** (`SIGNED_URL_EXPIRE_SECONDS`, default 300s) rather than
  permanent public links.

## SQL injection
Every query in `cloud/database_service.py` uses parameterized placeholders
(`?` / `%s`) — values are never interpolated into SQL strings.

## Secrets management
`backend/config.py` reads every credential from environment variables via
`python-dotenv`. `.env` is git-ignored; `.env.example` documents every
variable with no real values. In production mode (`APP_ENV=production`),
the app **refuses to start** if `SECRET_KEY` is left as a placeholder,
rather than silently running insecurely.

## Rate limiting
`backend/utils/rate_limit.py` throttles login attempts per email+IP
(`AUTH_RATE_LIMIT_PER_MIN`, default 10/min) to slow down password-guessing.
Noted in the code as process-local — a real multi-instance deployment
should move this to a shared store (Redis) or an API gateway.

## CORS
`backend/app.py` restricts allowed origins to `CORS_ORIGINS` from the
environment rather than defaulting to `*`, so the API only accepts
browser requests from the configured frontend origin(s).

## Error handling that doesn't leak internals
`backend/middleware/error_handler.py` catches every unhandled exception,
logs the full detail server-side, and returns a generic
`500 INTERNAL_ERROR` to the client — a database connection string, a stack
trace, or an internal file path is never part of an HTTP response.

## Common mistakes this project deliberately avoids

| Mistake | What this project does instead |
|---|---|
| Trusting the file extension alone | Also checks magic bytes (`validators.content_matches_extension`) |
| Checking deadlines with the browser's clock | Always uses `utcnow()` on the server |
| Hiding a button instead of enforcing a role server-side | Every route re-checks role + ownership server-side regardless of what the UI shows |
| Storing raw JWTs to "support logout" | Stores only a SHA-256 hash of a revoked token |
| Hardcoding a database URL or API key in source | Everything comes from `.env`, which is git-ignored |
| Returning stack traces on error | Centralized handler always returns a generic message, logs details separately |
| Letting anyone self-register as a teacher | `TEACHER_INVITE_CODE` gate on teacher registration |
| Public, permanent file links | Signed, expiring URLs in cloud mode; ownership-checked API route in local mode |

## What is intentionally out of scope

- **Malware/antivirus scanning** of uploaded files — magic-byte validation
  catches "wrong file type," not "malicious file of the correct type."
  A production deployment should add a scanning step (e.g. ClamAV, or a
  cloud provider's built-in file-scanning service) before serving uploads
  back to other users.
- **Multi-factor authentication** — straightforward to add on top of the
  existing JWT flow, but out of scope for a first version.
- **CSRF protection** — not required as-is because the API uses a Bearer
  token in an `Authorization` header (not cookies), which isn't
  automatically sent cross-site by the browser the way a cookie would be.
