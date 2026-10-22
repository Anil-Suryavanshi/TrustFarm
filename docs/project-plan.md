# TrustFarm project plan

## Scope

TrustFarm is a local, software-only MCA project. It generates **simulated** sensor data, evaluates data quality before issuing an irrigation decision, and compares that trust-aware decision with a threshold-only baseline. It does not control a pump, claim field validation, or represent generated readings as real farm measurements.

## Functional requirements

- Simulate five configurable virtual sensors with reproducible seeds and bounded history.
- Support normal, missing, stale, out-of-range, spike, stuck, outage, and mixed-fault scenarios.
- Validate readings; identify missing, stale, invalid, repeated and suspicious readings.
- Calculate a transparent reliability score and return an explainable decision.
- Provide versioned APIs, a React dashboard, import/export, experiment results and documentation.

## Non-functional requirements

- Python 3.11+ / Flask backend; React, Vite, Tailwind frontend.
- UTC timestamps, safe validation, bounded input and history, consistent JSON errors.
- Responsive and keyboard-accessible UI. Local development CORS is restricted to the Vite origin.

## Reliability and decision rules

`score = 100 × (0.30 freshness + 0.25 completeness + 0.20 validity + 0.25 consistency)`.

Missing required values return `INSUFFICIENT_DATA`. Stale, invalid or below-minimum-trust readings return `VERIFY_DATA`. Only reliable data is compared with the configurable demonstration moisture threshold, yielding `IRRIGATION_RECOMMENDED` or `NO_IRRIGATION_RECOMMENDED`.

## Architecture

`Simulator → repository → quality engine → decision engine → Flask /api/v1 → React dashboard`.

The simulator attaches ground-truth fault labels only for controlled evaluation. The live decision engine never uses those labels.

## Acceptance and limitations

The app is accepted after API, simulation, analysis, experiment and export tests run locally. CSV import is validated and limited. Results are appropriate for a controlled demonstration only; reliability is an algorithmic quality score, not a calibrated probability or farming guarantee.
