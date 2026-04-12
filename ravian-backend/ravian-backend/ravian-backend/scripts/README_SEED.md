# ClaritAI / Ravian EdTech — MEGA Data Seeding

Comprehensive seeding for the ClaritAI EdTech platform with realistic B2B Indian data.

## Prerequisites

- PostgreSQL running with database `ravian_db` (or your configured DB)
- Python environment with project dependencies installed
- For PDF generation: `pip install reportlab`

## Run Order

**From the project root** (the folder containing `scripts/`, `app/`, `main.py`):

### 1. Seed Database (Required)

```powershell
python -m scripts.seed_data
```

### 2. Generate PDFs (Optional)

```powershell
pip install reportlab
python -m scripts.seed_pdfs
```

### Run Both (one line each)

```powershell
python -m scripts.seed_data
python -m scripts.seed_pdfs
```

**Note:** If you're not in the project folder, change to it first:
```powershell
cd "C:\Users\praty\OneDrive\Desktop\Edtech admission Final\ravian-backend\ravian-backend\ravian-backend"
```

## What Gets Seeded

| Module | Count | Description |
|--------|-------|-------------|
| Courses | 15 | UPSC, SSC, Data Science, Full Stack, CAT, GATE, etc. |
| Leads | 45 | B2B leads from Infosys, TCS, Amazon, Paytm, etc. |
| Students | 30 | Enrolled learners with progress/risk data |
| Demos | 24 | 12 upcoming + 12 past demo meetings |
| Calls | 30 | Call logs with outcomes and notes |
| Enrollments | 30 | Course enrollments with payment status |
| Chatbot Sessions | 24 | Conversation sessions, some with leads captured |

## Default Login

After seeding:

- **Email:** admin@claritai.com  
- **Password:** Admin@123  
- **Role:** Administrator  

## Tenant

All seeded data belongs to tenant **ClaritAI EdTech** (`claritai.ravian.com`).

## Idempotency

- **Courses:** Upsert by name (skips if exists)
- **Leads:** Upsert by email (skips if exists)
- **Demos, Calls, Enrollments, Students, Chatbot Sessions:** New records each run (may create duplicates on re-run; consider clearing if needed)

## Verify

Visit http://localhost:3000/dashboard after starting frontend and backend.
