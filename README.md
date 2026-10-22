# TrustFarm

A software-only smart-agriculture prototype built from the supplied case study. It simulates soil-moisture, temperature and humidity readings, checks reliability, flags missing/stale/inconsistent data, and supplies a cautious irrigation recommendation.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000`.

## Simulations

The dashboard buttons add one virtual reading in each condition:

- Normal
- Dry soil
- Missing value
- Stale timestamp
- Sudden anomalous moisture change

The reliability score uses the case-study weights: freshness 30%, completeness 25%, validity 20%, and consistency 25%. Readings below 85/100 produce **Verify data first** rather than an automatic irrigation recommendation.
