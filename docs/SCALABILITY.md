# Scalability

## Current design choices that already help

- **Stateless backend:** almost all state lives in the database or object
  storage, not in server memory — the one exception is the in-process rate
  limiter (`backend/utils/rate_limit.py`), called out below. A stateless
  app can run as many identical instances as needed behind a load balancer.
- **Files never touch the database:** uploads go straight to object
  storage, so the database only ever holds small rows and stays fast to
  query even as file volume grows.
- **Indexed foreign keys:** `submissions.assignment_id` and
  `submissions.student_id` are indexed, so "submissions for this
  assignment" / "submissions by this student" stay fast as row count grows.
- **Provider-agnostic cloud layer:** swapping `CLOUD_PROVIDER=local` for
  `CLOUD_PROVIDER=supabase` moves from a single SQLite file to a managed,
  horizontally-scalable Postgres instance and S3-compatible storage without
  touching business logic.

## What would need to change to support 100,000 students

| Concern | Change needed |
|---|---|
| Single backend process | Run multiple stateless Flask instances behind a **load balancer**; any instance can serve any request since no session state lives on the process. |
| In-process rate limiter | Move to a shared store (Redis) or push rate limiting to an API gateway, since per-process counters don't coordinate across instances. |
| SQLite | Not viable at this scale (single-writer, single-file) — move to managed Postgres (already the cloud-mode default here) with connection pooling. |
| Dashboard aggregation in Python | `dashboard_service.py` currently loops over rows in Python for simplicity. At scale this becomes SQL `GROUP BY`/`COUNT` queries, or a scheduled job that pre-aggregates into a summary table so the dashboard read is O(1) instead of O(n). |
| Large file uploads | Move from "upload through the Flask app" to **direct-to-storage uploads** using a pre-signed upload URL, so large files never pass through (and load) the application server at all. |
| Peak traffic near deadlines | Deadline day is a predictable spike; **elastic** compute (auto-scaling instance count) absorbs it without over-provisioning year-round. |
| Global student base | A **CDN** in front of the static frontend, and optionally regional read replicas of the database, reduce latency for geographically distant users. |
| Notifications at scale | An async **queue** (e.g. for "email the student their grade") decouples slow operations (sending email) from the fast path (saving the grade), so grading a submission doesn't wait on an email provider. |
| Observability | Structured logging + a real monitoring/alerting stack (the codebase already logs every unhandled exception server-side — see `backend/middleware/error_handler.py` — as the foundation for this). |

## Vertical vs. horizontal scaling, in this project's terms

- **Vertical** (a bigger single database/server) is where this project
  starts — a single managed Postgres instance handles a normal course's
  worth of students comfortably.
- **Horizontal** (more instances) is what the backend is already built to
  support cheaply, because it's stateless: `docker run` (or your platform's
  equivalent) three copies of `backend/app.py` behind any load balancer and
  they all work correctly, since every request carries everything it needs
  (the JWT) and touches only the shared database/storage.

## Caching opportunities (not yet implemented)

- Assignment listings change rarely relative to how often they're read —
  a short-TTL cache (in-memory or Redis) in front of `GET /api/assignments`
  would cut database load significantly at scale.
- Dashboard numbers could be recomputed on a schedule (e.g. every 5
  minutes) instead of on every page load, trading a small staleness window
  for a much cheaper read.
