# analyser-cld

AI-powered game analysis platform — Claude Vision API + FastAPI + Railway.

## Quick Start (local)

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
uvicorn app.main:app --reload
```

## Deploy

Push to `main` → GitHub Actions → Railway auto-deploy.

## API

`POST /analyze/sync` — synchronous, returns JSON + optional PDF  
`POST /analyze` — async, returns job_id  
`GET /analyze/{job_id}/result` — fetch async result  
`GET /health` — health check
