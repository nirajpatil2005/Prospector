**Project Overview**

- **What:** Orchestrator that runs a lightweight crawler and the Insighter analysis service, scrapes given sites, and returns LLM-based company insights.
- **Structure:** Top-level orchestrator `main.py` starts and coordinates services. The crawler lives in `crawler/` and Insighter backend in `Insighter/backend/`.

# crawling_scrap

A lightweight Python project for web scraping and basic content analysis. It includes a small crawler that saves JSON outputs and an "Insighter" component for post-processing and analysis.

## Quick summary

- Scraper: implemented in the `crawler/` folder — collects pages and writes timestamped JSON files to `crawler/output/`.
- Insighter: analysis and API code lives in `Insighter/` (includes backend, core analyzers, and utilities).

## Requirements

- Python 3.8+ recommended.
- Install dependencies:

```bash
python -m venv .venv
.venv\\Scripts\\activate      # Windows
pip install -r requirements.txt
```

If you plan to run the Insighter service separately, also check any `Insighter/requirements.txt` if present.

## How to run

1. Activate your virtual environment (see above).
2. Run the orchestrator (this will usually start or coordinate the services):

```bash
python main.py
```

3. Alternatively run components individually:

```bash
# Run crawler (if implemented as a service):
python crawler/scrap.py

# Run Insighter backend (example using uvicorn from Insighter/backend/app):
cd Insighter/backend/app
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Check the top of each `main.py` file for any command-line options or environment expectations.

## Configuration / Environment

- Place API keys and service URLs in environment variables or an `.env` file inside `Insighter/` (example: `OPENAI_API_KEY`, `GROQ_API_KEY`).
- The orchestrator can use environment variables like `CRAWLER_API_URL` and `INSIGHTER_ANALYZE_SCRAPED` to target services.

## Output

Scraped data is saved to `crawler/output/` as files named similar to `scrape_<timestamp>.json`. Example files are already included for reference.

## Project layout

- [main.py](main.py)
- [requirements.txt](requirements.txt)
- [crawler/](crawler/)
  - [crawler/scrap.py](crawler/scrap.py)
  - [crawler/filter_system.py](crawler/filter_system.py)
  - [crawler/output/](crawler/output/)
- [Insighter/](Insighter/)
  - [Insighter/main.py](Insighter/main.py)
  - [Insighter/backend/app/](Insighter/backend/app/)
  - [Insighter/core/](Insighter/core/)

## Troubleshooting

- If you get missing-package errors: re-run `pip install -r requirements.txt` and check for an `Insighter/requirements.txt`.
- If LLM calls fail with authentication errors, ensure the appropriate API key is set (e.g., `OPENAI_API_KEY`).
- If services report unhealthy, verify ports (commonly 8000/8001) and start components individually to inspect logs.

## Contributing notes

- When editing or uploading files, avoid changing the top-level repository structure — this README assumes the current layout.
- Preview the README in your editor before pushing to avoid formatting oddities on remote viewers.

---
If you'd like, I can:

- open a preview of this README.md in the editor, or
- run a quick smoke test (install deps and run `python main.py`) and report any obvious runtime errors.


