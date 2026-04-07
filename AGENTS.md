# AGENTS.md

Project agent instructions for `cs2-datalab`.

## Goal
Build and maintain a CS2 data pipeline that:
1. Parses `.dem` files into structured outputs.
2. Produces tactical summaries and prompts.
3. Generates visuals and videos.
4. Orchestrates end-to-end jobs through n8n.

## Architecture
- `parser/`: demo parsing service.
- `analyzer/`: tactical analysis and prompt generation APIs.
- `generator/`: visualization/video generation service.
- `scripts/`: CLIs for extract, parse, visualize, prompt creation, and pipeline glue.
- `n8n/`: workflow JSON and n8n runtime config.
- `nginx/`: reverse proxy config.
- `features/`: generated tactical summaries and AI prompt artifacts.
- `docker-compose.yml`: local multi-service orchestration.

## Primary Runtime
Use Docker Compose for local integration work.

Core services from `docker-compose.yml`:
- `n8n` on port `5678` (internal), proxied by nginx.
- `postgres` on port `5432` (internal network).
- `analyzer` on `8002`.
- `generator` on `8001`.
- `parser` as worker-style service.

## Common Commands
From repository root:

```bash
# Bring up full stack
docker compose up -d --build

# Watch logs for key services
docker compose logs -f parser analyzer generator n8n

# Tear down
docker compose down
```

Pipeline helper flow:

```bash
# Example: run parser pipeline helper with a URL
bash scripts/run_pipeline.sh "<demo-or-zip-url>"
```

Extraction helper flow:

```bash
# Extract/parse local zip or dem
bash scripts/auto_extract_and_parse.sh /data/raw/example.zip
```

## Agent Rules
- Keep changes focused and minimal.
- Preserve existing service contracts and output file formats unless asked.
- Prefer updating scripts and service code over changing workflow JSON blindly.
- When touching `n8n/*.json`, keep node names and connection structure stable.
- Avoid destructive operations on `postgres_data/`.
- Do not commit generated artifacts unless requested (`videos/`, generated visuals, large parsed outputs).

## Coding Standards
- Python: PEP 8, type hints when practical, explicit error handling.
- Bash: `set -euo pipefail` for new scripts, quote variables.
- Paths: keep repo-relative behavior predictable for scripts invoked from root.

## Validation Checklist
After code changes:
1. Run targeted script/service command for touched area.
2. Confirm outputs exist where expected (`parsed/`, `features/`, `visuals/`, `videos/`).
3. Check container logs for runtime errors.
4. If API behavior changed, validate endpoint response shape.

## Safe Change Areas
Usually safe to edit:
- `scripts/*.py`, `scripts/*.sh`
- `parser/main.py`, `analyzer/main.py`, `generator/main.py`
- `n8n/cs2_pipeline*_workflow.json` (carefully)
- `nginx/conf.d/*.conf`

Use extra caution with:
- `postgres_data/`
- Production deploy files under `deploy/`

## Definition of Done
A task is complete when:
- Implementation is in place.
- Relevant command(s) run successfully.
- No obvious regression in pipeline path.
- User-facing behavior/output is documented in the PR or change note.
