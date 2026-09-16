# SmartOrder AI (OrdEasy) — Backend

Multi-agent, self-healing AI order-entry backend for the Eaton Pratibha Excellence prototype.
Now includes: free LLM (Groq), automatic email ingestion, a continuous background scheduler,
and a notification layer.

## Architecture

```
                        ┌─────────────────────┐
                        │   Email inbox (IMAP) │  ← polled every N minutes
                        └──────────┬──────────┘
                                   │ new attachments
     Manual Upload (API)          ▼
              │            Scheduler Service
              └──────┬───────────┘
                      ▼
              Intake Agent  ──────► Classifier Service
                      │
                      ▼
    PDF Service / Excel Service / OCR Service   (raw text out)
                      │
                      ▼
    Extraction Agent  ──────► LLM Service (Groq free tier by default)
                      │
                      ▼
    Validation Agent  ──────► business_rules.json
                      │
                      ▼ (only if invalid)
    Recovery Agent  ──────► cheap fixes, then LLM re-read  (self-healing)
                      │
                      ▼
    Inventory Agent  ──────► sku_mapping.json (swap for a real DB/ERP later)
                      │
                      ▼
    Billing Agent  ──────► subtotal, GST, grand total
                      │
                      ▼
    Saved to SQLite  ──────► Notification Agent creates alerts
                      │
                      ▼
    Dashboard Agent / Conversation Agent read from here
```

## Folder structure

```
backend/
├── app/
│   ├── main.py                      FastAPI entrypoint, starts the scheduler
│   ├── config.py                    Reads .env into a Settings object
│   ├── api/
│   │   ├── upload.py                POST /api/orders/upload
│   │   ├── orders.py                GET /api/orders, /api/dashboard, POST /api/chat
│   │   └── system.py                Notifications, manual email check, health check
│   ├── agents/
│   │   ├── intake_agent.py
│   │   ├── extraction_agent.py
│   │   ├── validation_agent.py
│   │   ├── recovery_agent.py        Self-healing: fixes what it can, escalates the rest
│   │   ├── inventory_agent.py
│   │   ├── billing_agent.py
│   │   ├── dashboard_agent.py
│   │   ├── notification_agent.py    Alerts for anything needing human attention
│   │   ├── learning_agent.py
│   │   └── conversation_agent.py
│   ├── services/
│   │   ├── logger_service.py
│   │   ├── openai_service.py        OpenAI-SDK wrapper, points at Groq by default
│   │   ├── classifier_service.py
│   │   ├── pdf_service.py
│   │   ├── excel_service.py
│   │   ├── ocr_service.py
│   │   ├── email_service.py         IMAP inbox polling + attachment download
│   │   ├── scheduler_service.py     Background timer -> continuous operation
│   │   ├── pipeline_service.py      Shared logic used by upload AND email paths
│   │   ├── inventory_service.py
│   │   └── database_service.py
│   ├── models/database_models.py    Order, OrderItem, Inventory, Notification
│   ├── schemas/order_schema.py
│   ├── prompts/extraction_prompt.txt
│   └── knowledge/
│       ├── sku_mapping.json         Seed product catalog (the "knowledge layer")
│       └── business_rules.json      Validation thresholds/rules
├── sample_data/sample_po.txt
├── test_extraction.py
├── requirements.txt
└── .env.example
```

## Setup

1. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # Mac/Linux
   pip install -r requirements.txt
   ```

2. Get a **free** LLM key (no card, no billing) at
   **https://console.groq.com/keys**, then copy `.env.example` to `.env` and paste it in:
   ```
   OPENAI_API_KEY=your_groq_key_here
   ```
   (The variable is still called `OPENAI_API_KEY` because Groq uses the same SDK/format as OpenAI —
   only the `OPENAI_BASE_URL` differs, and that's already set correctly in `.env.example`.)

3. *(Optional)* Enable email ingestion — see "Continuous email ingestion" below.

4. *(Optional, for scanned images)* install OCR support:
   ```
   pip install paddlepaddle paddleocr opencv-python-headless
   ```

## Run

```
uvicorn app.main:app --reload
```
Open **http://127.0.0.1:8000/docs** for interactive Swagger docs.

Test the LLM step alone first:
```
python test_extraction.py
```

## Continuous email ingestion (orders arriving by email)

This uses IMAP + an app password — free, and works with Gmail/Outlook/Yahoo etc.
No Gmail API / OAuth consent screen needed.

1. On the Google account receiving orders: turn on **2-Step Verification**
   (Google account settings), then generate an **App Password** at
   https://myaccount.google.com/apppasswords
2. In `.env`:
   ```
   EMAIL_USER=your_inbox@gmail.com
   EMAIL_PASS=the_16_character_app_password
   ENABLE_EMAIL_POLLING=true
   EMAIL_POLL_MINUTES=5
   ```
3. Restart the backend. It will now check the inbox every 5 minutes, download any
   PDF/Excel/image attachments from **unread** emails, run them through the full
   pipeline automatically, and mark those emails as read.
4. To trigger a check immediately instead of waiting: `POST /api/system/check-email-now`
   (there's also a "Check inbox now" button on the dashboard).

## Key endpoints

| Method | Path                            | Purpose                                       |
|--------|----------------------------------|------------------------------------------------|
| POST   | `/api/orders/upload`            | Upload a PDF/Excel/image, runs full pipeline   |
| GET    | `/api/orders`                   | List all processed orders                      |
| GET    | `/api/orders/{id}`              | Full detail for one order                      |
| GET    | `/api/dashboard`                | Aggregated stats for the dashboard UI          |
| POST   | `/api/chat`                     | Ask questions about orders in plain English     |
| GET    | `/api/notifications`            | Recent alerts (validation failures, shortages) |
| POST   | `/api/system/check-email-now`   | Trigger an inbox check immediately             |
| GET    | `/api/healthz`                  | Health check (used to keep free hosting awake) |

## Deploying this for free

**Frontend → Vercel**
1. Push this repo to GitHub.
2. Go to vercel.com → New Project → import the repo → set root directory to `frontend`.
3. Add environment variable `VITE_API_BASE` = your deployed backend URL (step below).
4. Deploy. Free, no card required.

**Backend → Render.com (free web service)**
1. New Web Service → connect your GitHub repo → root directory `backend`.
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add your `.env` values as environment variables in Render's dashboard.
5. **Important limitation**: Render's free tier sleeps after 15 minutes of no traffic,
   which also pauses the background email-polling scheduler. Fix with a free external
   cron ping (next section).

**Keeping a free host awake + polling on schedule → cron-job.org (free)**
1. Sign up at cron-job.org (free, no card).
2. Create a job that hits `https://your-backend.onrender.com/api/system/check-email-now`
   every 5–10 minutes.
3. This does two things at once: keeps Render from sleeping, AND triggers the
   email-ingestion check on schedule — effectively free "continuous" operation.

**Database → Supabase (free Postgres)**
SQLite works locally, but free hosts like Render wipe the filesystem on redeploy/restart,
so orders would disappear. For anything you need to persist:
1. Create a free project at supabase.com.
2. Copy its Postgres connection string.
3. Set `DATABASE_URL=postgresql://...` in your backend's environment variables.
4. Add `psycopg2-binary` to `requirements.txt`.

**Alternative to a sleeping web service → GitHub Actions (free, for public repos)**
If you'd rather not fight a free host's sleep behavior at all, you can skip the
scheduler entirely and instead add a scheduled GitHub Actions workflow (cron syntax,
runs on GitHub's own servers) that calls `POST /api/system/check-email-now` on your
deployed backend every 10 minutes. This is fully free and doesn't depend on your
backend host staying awake on its own.

## Notes on the prototype vs. production

- **LLM**: Groq free tier by default (fast, no billing). Swap `OPENAI_BASE_URL` and
  `OPENAI_MODEL` in `.env` to use real OpenAI or another OpenAI-compatible provider instead.
- **Self-healing**: the Recovery Agent fixes what it safely can (e.g. computing a missing
  total_price) before re-validating; anything it can't fix escalates to a Notification
  instead of silently failing or blocking the order.
- **Knowledge layer**: `sku_mapping.json` (product catalog) and `business_rules.json`
  (validation thresholds) — swap these for real DB-backed lookups when ready.
- **Database**: SQLite by default. Swap `DATABASE_URL` for Postgres (e.g. Supabase) once
  you deploy somewhere with an ephemeral filesystem.
- **OCR**: PaddleOCR is optional/lazy-imported so the rest of the app runs even without it.
