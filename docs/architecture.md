# Architecture

`VirtualSensorSimulator → ReadingRepository → analysis.py → decisions.py → Flask /api/v1 → React dashboard`.

The simulator produces UTC ISO-8601 readings and controlled ground-truth labels. `analysis.py` does not consume those labels, preventing leakage into the reliability calculation. `decisions.py` receives readings and analysis results and applies the configured trust gate before the demonstration moisture threshold. The repository uses a bounded deque to prevent unbounded in-memory growth.
