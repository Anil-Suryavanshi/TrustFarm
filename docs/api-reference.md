# API reference

All responses use `{ success, data, message }`; errors use `{ success: false, error: { code, message, details } }`.

| Route | Purpose |
|---|---|
| `GET /api/v1/health` | Health status |
| `GET /api/v1/dashboard/summary` | Overview metrics and current decision |
| `GET /api/v1/sensors` | Latest reading and quality by sensor |
| `GET /api/v1/sensors/<id>/history` | Selected sensor history |
| `GET /api/v1/readings?page=&page_size=` | Paginated readings |
| `POST /api/v1/simulation/{start,pause,resume,reset,step}` | Simulation controls; `step` accepts `{scenario}` |
| `GET /api/v1/analysis/quality` | Quality outcomes |
| `GET /api/v1/analysis/decisions` | Baseline and trust-aware decisions |
| `POST /api/v1/experiments/run` | Controlled experiment `{scenario, steps}` |
| `GET /api/v1/data/export` | Generated readings as CSV |
| `GET/PUT /api/v1/settings` | Validated configuration |
