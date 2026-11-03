# GuardianX Civic Records AI — Prototype

A runnable Streamlit prototype for demonstrating transparent, human-led public records search and review.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL shown by Streamlit. To deploy, push these files to a GitHub repository and use Streamlit Community Cloud (entrypoint `app.py`). The local SQLite database is **ephemeral on many free cloud hosts** and is not appropriate for durable production records. This is a synthetic-data demonstration, not a government deployment.

## Two-minute walkthrough
1. Overview: load fictional demo record.
2. Records: open the sample.
3. Search Workspace: search `traffic safety road closures transportation planning` and send a result to review.
4. Human Review: choose Include and save a reviewer note.
5. Audit & Exports: show persisted decision and download JSON/CSV.

## Limitations
Keyword retrieval only; no generative AI, exemptions classifier, government integration, authentication, or production security controls. Use fictional data only.
