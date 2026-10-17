# Northstar HR Agent Deployment

## Public Application

- Application: https://northstar-hr-agent-5uub.onrender.com/
- Health endpoint: https://northstar-hr-agent-5uub.onrender.com/health
- Readiness endpoint: https://northstar-hr-agent-5uub.onrender.com/ready

The health endpoint reports application and MCP status. The readiness endpoint is configured as the Render health check.

## Deployment Architecture

The application is deployed as a single Render web service. It runs the Flask interface and API, LangGraph orchestrator, local stdio MCP server process, and Chroma policy index. Synthetic employee and PTO data are committed with the project. The Chroma index is rebuilt from the committed policy corpus during deployment. The LLM provider is configured through private environment variables.

## Render Build and Start Commands

Build command:

```bash
pip install -r requirements.txt && python scripts/build_policy_index.py
```

Start command:

```bash
gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 src.web.app:app
```

Required private configuration includes `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL`. Do not commit provider credentials. Set `PYTHONHASHSEED` in the service environment before Python starts if deterministic Python hashing is required.

## Free-Tier Behavior

The Render free web service may spin down after inactivity. The first request after spin-down can take a minute or more while the service starts. Subsequent requests can still be slow because the free instance has limited CPU and memory and performs local embedding, Chroma retrieval, MCP subprocess calls, and external model requests.

## Deployment Validation

After deployment, verify that the application URL loads, `/ready` returns HTTP 200, `/health` reports app and MCP status, policy questions return grounded citations, and an employee-specific PTO question uses MCP tools. The mock PTO operation does not modify real HR records.
