# SmartOrder AI — Frontend

React + Vite dashboard, upload flow, and chat assistant for the OrdEasy backend.

## Theme

- Background: burnt industrial orange (`#E1590A` → `#C24C08` gradient)
- Buttons & panels: black (`#0A0A0A`) with white text
- Accent: amber (`#FFB100`) for the live/active pipeline state and charts
- Type: Archivo Black (headings) / IBM Plex Sans (body) / IBM Plex Mono (order numbers, SKUs, stats)
- Signature element: the **pipeline tracker** — every order's journey through
  Intake → Extraction → Validation → Inventory → Billing → Saved is shown as
  an animated conveyor-style tracker on the upload page, and as a compact dot
  row in the dashboard table.

## Setup

```
npm install
cp .env.example .env      # point VITE_API_BASE at your backend if not localhost
npm run dev
```

Open **http://localhost:5173**. Make sure the backend is running first:
```
# in the backend/ folder
uvicorn app.main:app --reload
```

## Pages

- `/` — Dashboard: live stats, revenue chart, status breakdown, recent orders table
- `/upload` — Drag-and-drop order upload with a live pipeline tracker and full result breakdown (validation, shortages, invoice)
- `/chat` — Chat assistant grounded in the actual order database
- `/orders/:id` — Full detail view for a single order

## Build for production

```
npm run build
```
Outputs static files to `dist/`, which you can serve with any static host or behind the FastAPI app itself.
