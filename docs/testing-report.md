# Testing report

Executed locally on 2026-10-22:

- `python -m unittest discover -s backend\tests -v`: **7 tests passed**.
- Coverage includes health response, normal simulation, missing-data withholding, invalid scenario validation, experiment metric creation, configuration validation, and CSV export.
- `npm run build`: **passed**; Vite generated a production bundle.

Frontend browser interaction testing and real hardware validation are not represented by these automated results.
