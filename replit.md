# GuardianX Civic Records AI

Imported Streamlit prototype. Preserve the existing Python/Streamlit structure
and local SQLite storage unless a storage change is explicitly requested.

## Run on Replit

- Runtime: Python 3.11.
- Dependencies: `requirements.txt` (Streamlit and pandas).
- Click **Run** to start the **Start application** workflow.
- The workflow runs:
  `python -m streamlit run app.py --browser.serverAddress="$REPLIT_DEV_DOMAIN"`
- `.streamlit/config.toml` binds the server to `0.0.0.0:5000` for preview.
- No API keys or external services are required.

## Demo walkthrough

1. Overview: click **Load fictional demo record**.
2. Records: expand the sample record.
3. Search Workspace: use the default traffic-safety search and send a result to review.
4. Human Review: choose a decision, enter a rationale, and save.
5. Audit & Exports: inspect the saved decision and download JSON/CSV.

## Data and scope

`guardianx.db` is created beside `app.py` on first use and excluded from Git.
It contains records, review decisions, and audit events. Local SQLite is for
this demonstration, not durable production records. Use fictional data only.
The app has no authentication or government integration and uses deterministic
keyword search, not generative AI.
