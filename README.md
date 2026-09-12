# Meta Lead CRM Foundation

This project contains a minimal CRM foundation with an independent Next.js frontend and FastAPI backend. The existing Meta Lead Ads read and webhook functionality remains available, and the backend connects to the existing `meta_lead_test_db` PostgreSQL database.

No CRM tables, users, user types, or admin modules are created yet. The existing `meta_leads` table is not modified.

## Project structure

```text
backend/                 FastAPI app, SQLAlchemy engine, Alembic setup
frontend/                Next.js + React + TypeScript app
test_meta_lead.py        Existing Meta API and webhook implementation
test_webhook.py          Existing webhook test
test_auth.py             Authentication tests
requirements.txt         Python dependencies
.env.example             Environment variable template
```

## 1. Create a virtual environment

Open PowerShell in this folder and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use the Python executable directly instead:

```powershell
.\.venv\Scripts\python.exe --version
```

## 2. Install backend requirements

With the virtual environment active, run:

```powershell
python -m pip install -r requirements.txt
```

Install the frontend dependencies separately:

```powershell
Set-Location frontend
npm install
```

## 3. Create your environment file

Copy the example file:

```powershell
Copy-Item .env.example .env
```

Open `.env` and set:

- `META_PAGE_ACCESS_TOKEN`: put your Meta Page Access Token after the equals sign.
- `META_LEAD_FORM_ID`: put the ID of the Facebook or Instagram Lead Form after the equals sign.

Keep `.env` private. The script sends the token to Meta but never prints it.

## 4. Run the test

```powershell
python test_meta_lead.py
```

## Successful output

A successful run looks similar to this:

```text
Lead ID: 123456789012345
Created time: 2026-09-03T12:34:56+0000
Form ID: 987654321098765
Field data: full_name = Example Person
Field data: email = person@example.com
Field data: phone_number = +15551234567
```

The exact fields depend on the questions configured in the form. If the request succeeds but the form has no leads, the script reports that no leads were returned.

## Run the backend

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

The API health check is available at `GET http://localhost:8000/health`.

## Run the frontend

In a second terminal:

```powershell
Set-Location frontend
npm run dev
```

The placeholder page is available at `http://localhost:3000`.

## Admin authentication

Set a private signing key in `.env` before using authentication. Generate one
without putting it in source control:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the generated value into `JWT_SECRET_KEY` in `.env`. The key is used only
by FastAPI and is never included in frontend code.

Create the first active ADMIN interactively. The password is prompted twice
and stored as an Argon2 hash; it is never written to source code or printed:

```powershell
.\.venv\Scripts\python.exe -m backend.seed_admin `
	--first-name Ada `
	--last-name Admin `
	--email admin@example.com
```

The command refuses to create another ADMIN if one already exists. It writes
to the existing `users` table only and does not create tables or modify
`priority`, `leads`, or `meta_leads`.

The login endpoint is `POST /auth/login` with `email` and `password`. It
returns a short-lived JWT and safe user fields including `user_type_id`.
`GET /admin/me` requires `Authorization: Bearer <token>` and allows only
active ADMIN users. The frontend stores the access token for the browser
session, verifies it through `/admin/me`, and redirects administrators to
`/admin/dashboard`.

## Alembic

Alembic is configured for future migrations. No models are registered yet, so it currently produces no table operations:

```powershell
.\.venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head
```

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Webhook mode

The project also provides a local FastAPI webhook at `GET /webhook` and `POST /webhook`. Meta must be configured separately with a public HTTPS callback URL; this local server is not automatically registered with Meta.

Set these values in `.env` before starting the server:

- `META_WEBHOOK_VERIFY_TOKEN`: a private verification string you choose and enter in both Meta and `.env`.
- `META_TEST_DB_PASSWORD`: your PostgreSQL password. Leave it out of source code and never commit `.env`.
- `META_TEST_DB_NAME`: keep this as `meta_lead_test_db`.

Start the local webhook server with:

```powershell
python test_meta_lead.py --webhook
```

Meta webhook verification uses `GET /webhook` with `hub.mode`, `hub.verify_token`, and `hub.challenge`. Lead events are received at `POST /webhook`; the server retrieves each lead from Meta using `leadgen_id`, maps it, and saves it to `public.leads`. The existing `meta_leads` table is retained for the standalone test commands and is not used as the destination for webhook leads. Duplicate webhook deliveries are ignored using `public.leads.meta_leadgen_id`.
