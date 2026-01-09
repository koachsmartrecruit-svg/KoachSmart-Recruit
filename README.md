# KoachSmart-Recruit

KoachSmart-Recruit is an AI-assisted hiring platform that connects sports academies with verified coaches, combining job posting, intelligent matching, real-time chat, and subscription billing.

## What this app does (non-technical)

- Academies/employers can:
  - Create accounts, post coaching jobs with location and detailed requirements.
  - See ranked applicants with an automatic “match score” and explanation.
  - Update application status (Applied, Interview, Hired, Rejected) and send email notifications.

- Coaches can:
  - Sign up (email or Google), build a rich coaching profile, and upload proofs and resumes.
  - Browse and filter active jobs by sport, city, salary text, job type, and distance.
  - Apply with optional custom resumes and answer screening questions.

- Platform features:
  - In-app 1:1 chat with file sharing, online presence, typing indicators, and read receipts.
  - Subscription plans (Basic, Pro) using Stripe; access is updated via webhooks.
  - Super-admin view with coach verification and platform-wide stats.

## Tech stack

- Backend: Flask, Flask-Login, Flask-SocketIO, Flask-Mail
- ORM & DB: SQLAlchemy with a relational database (Postgres/MySQL/SQLite via `DATABASE_URL`)
- Auth: Email/password + Google OAuth (Authlib)
- Payments: Stripe subscriptions + webhooks
- Integrations: Google Sheets API for mirroring users and applications
- Documents: PyPDF2, python-docx for parsing PDFs/DOCs; custom text parsers

## Data model (simplified)

- `User`: core auth, role (`coach`, `employer`, `admin`), Stripe IDs, subscription status.
- `Profile`: coach-specific info – sport, experience, city, certifications, proofs, resume, verification flag.
- `Job`: posted by employers; includes sport, location (venue/city/state/country), description, requirements, salary range.
- `Application`: links a coach to a job, stores match score, reasons, custom resume path, and screening answers.
- `Review`: rating + comment from employers about coaches.
- `Message`: chat messages between users, including file message links.

## AI and automation

- Match scoring:
  - Uses sport match, years of experience, verification badge, and requirement–certification keyword overlap.
  - Stores both a numeric score and a human-readable “why this score” text.

- Salary suggestions:
  - Suggests a salary range based on sport (e.g., higher for cricket), metro cities, senior roles, and job type (full-time, part-time, internship, contract).

- Profile completeness:
  - Calculates a 0–100% profile completion score from profile fields and uploaded documents.

## Main user flows

- **Coach**
  - Register/login → complete profile → browse/filter jobs → apply → chat with employers → track applications and ratings.

- **Employer**
  - Register/login → choose plan → create jobs → view candidates with match scores → change statuses → schedule interviews and chat.

- **Admin**
  - Access `/super-admin` → verify coach documents, see platform stats, and manage users and jobs.

## Environment configuration

Environment variables (examples):

- `DATABASE_URL` – SQLAlchemy database URL.
- `SECRET_KEY` – Flask session key.
- `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_PRICE_BASIC`, `STRIPE_PRICE_PRO`, `STRIPE_WEBHOOK_SECRET`
- `MAIL_USERNAME`, `MAIL_PASSWORD` – SMTP credentials (Gmail by default).
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_SHEETS_CREDENTIALS`, `GOOGLE_SHEETS_SPREADSHEET_ID`

## Running locally

1. Create and activate a virtualenv.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
