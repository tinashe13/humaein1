Backend (FastAPI)

Local development:

```
# From app/backend
pip install poetry==1.8.3
poetry install

# Development server (recommended - fixes Windows reload issues)
poetry run python -m app.devserver

# Or traditional uvicorn (may hang on Windows reload)
poetry run uvicorn app.main:app --reload
```

API docs: /docs

Environment:

- DATABASE_URL (default sqlite:///./claims.db)
- ELIGIBILITY_REFERENCE_DATE (default 2025-07-30)
- CLASSIFIER_MODE (rules|heuristic|mock-llm|rules+heuristic)
- MAX_UPLOAD_MB (default 50)




