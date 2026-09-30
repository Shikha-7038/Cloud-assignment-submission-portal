# Technology Stack Options

Three implementation tiers, as requested by the brief. **This repository
implements Option B** (with Option A's local/free-tier fallback built in as
a configuration switch, not a separate codebase).

## Option A — Beginner

| Layer | Choice |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python Flask |
| Database | SQLite |
| Storage | Local uploads folder |

- **Architecture:** a single Flask process serving both API and static pages.
- **Difficulty:** low — no accounts, no network dependency, runs anywhere Python runs.
- **Cost:** free.
- **Cloud concepts demonstrated:** minimal — mostly client-server basics and a REST-ish API, without real cloud services.
- **Advantages:** fastest to get running, nothing to configure.
- **Limitations:** doesn't actually demonstrate cloud database/object storage/managed auth — a grader looking for cloud concepts will find this thin.

## Option B — Recommended Cloud Version *(implemented here)*

| Layer | Choice |
|---|---|
| Frontend | React (Vite) |
| Backend | Python Flask, REST API |
| Authentication | JWT-based, with a clean swap point for Supabase Auth |
| Database | SQLite locally / PostgreSQL via Supabase in the cloud |
| Cloud Storage | Local disk locally / Supabase Storage in the cloud |
| Deployment | Free-tier frontend host (Vercel/Netlify) + free-tier backend host (Render/Railway) |

- **Architecture:** `frontend/` (React) → REST API (`backend/`) → `cloud/database_service.py` + `cloud/storage_service.py`, both written as an interface with two interchangeable backends.
- **Difficulty:** moderate — real cloud concepts, but every free-tier service has a generous no-cost plan.
- **Cost:** $0 for a student project at this scale (Supabase free tier covers the database, storage, and even auth if you choose to swap to it).
- **Cloud concepts demonstrated:** cloud database, cloud object storage, authentication, RBAC, REST APIs, signed URLs, environment-based secrets, cloud deployment.
- **Advantages:** genuinely demonstrates the cloud concepts a Cloud Computing course wants to see, without needing a credit card or a paid account.
- **Limitations:** not auto-scaling in the way a serverless/managed-everything AWS build would be; a single backend process still needs to be running (though the free-tier hosts handle that for you).

**Why this is the recommended option:** it's the sweet spot between "actually cloud" and "actually free/beginner-friendly." Option A doesn't touch real cloud services; Option C is heavier to configure and often requires a credit card even on a free tier. Option B is the one a student can fully build, deploy, and demo without spending money or getting stuck in cloud-console setup for days.

## Option C — Advanced Cloud Version

| Layer | Choice |
|---|---|
| Frontend | React / Next.js |
| Backend | FastAPI |
| Cloud | AWS / Azure / Google Cloud |

Example architecture: Frontend Hosting + API Gateway + Backend/Serverless
Functions + Managed Database + Object Storage + Authentication + Monitoring.

- **Architecture:** fully serverless-capable — API Gateway in front of Lambda (or Azure Functions / Cloud Functions), a managed database (RDS/DynamoDB), S3/Blob Storage, Cognito/Azure AD B2C for auth, CloudWatch/Azure Monitor for observability.
- **Difficulty:** high — real IAM policies, VPC/networking considerations, and provider-specific tooling.
- **Cost:** technically has a free tier, but usage caps are easy to exceed by accident, and many AWS/Azure signups require a credit card even to stay within the free tier.
- **Cloud concepts demonstrated:** the full list — including true serverless compute, managed IAM, and enterprise-grade monitoring.
- **Advantages:** closest to what a large-scale production system looks like; strongest resume signal if you can show it deployed and working.
- **Limitations:** steep setup curve, easiest option to accidentally incur cost on, and the extra complexity doesn't teach fundamentally different concepts than Option B — it teaches provider-specific tooling.

## Recommendation

Build Option B first, get every feature working end-to-end, and only move to
Option C (or add AWS deployment on top of the same codebase, see
`docs/DEPLOYMENT.md` Approach B) once B is solid. That is the safest path to
a finished, demonstrable, resume-ready project without burning your course
timeline on cloud-console setup instead of features.
