# TrustFarm

TrustFarm is a **software-only**, trust-aware smart-agriculture monitoring project. It generates clearly labelled simulated sensor readings, checks their freshness, completeness, physical validity and consistency, then provides a cautious irrigation decision. It does not use physical sensors or control equipment.

## Features

- Five configurable virtual sensors; bounded local history and seeded, repeatable simulation.
- Normal, missing, stale, out-of-range, spike, stuck, outage and mixed-fault conditions.
- Transparent reliability score: `100 × (0.30F + 0.25C + 0.20V + 0.25K)`.
- `IRRIGATION_RECOMMENDED`, `NO_IRRIGATION_RECOMMENDED`, `VERIFY_DATA`, and `INSUFFICIENT_DATA` outcomes.
- Versioned Flask API, React/Vite responsive dashboard, CSV export, and reproducible evaluation metrics.

## Requirements

- Python 3.11+ (tested with Python 3.13)
- Node.js 20+ and npm (tested with Node 22)

## Run locally (Windows PowerShell)

Open **two** terminals in the project root.

**Terminal 1 – API**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python app.py
```

API health check: `http://127.0.0.1:5000/api/v1/health`

**Terminal 2 – dashboard**

```powershell
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite (normally `http://localhost:5173`). The dashboard reads from `http://127.0.0.1:5000/api/v1` by default. Copy `.env.example` to `frontend/.env` only when a different API URL is required.

## Test and build

```powershell
python -m unittest discover -s backend\tests -v
cd frontend
npm run build
```

## Safety and limitations

The moisture threshold is a demonstrative configuration, not universal agricultural advice. Reliability is an algorithmic data-quality assessment, not a probability that a sensor is correct. Experimental metrics are calculated only from controlled, labelled simulation faults and do not establish real-farm performance.

See [docs](docs/) for architecture, API, data dictionary, methodology, project plan, testing report, and user guide.
