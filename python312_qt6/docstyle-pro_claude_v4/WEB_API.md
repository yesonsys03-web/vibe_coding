# DocStyle Pro Web API

## Run

```bash
uv sync
uv run python -m web.run_api
```

Environment variables (optional):

- `DOCSTYLE_API_HOST` (default: `127.0.0.1`)
- `DOCSTYLE_API_PORT` (default: `8000`)
- `DOCSTYLE_API_RELOAD` (`1` or `0`, default: `1`)

Example:

```bash
DOCSTYLE_API_HOST=0.0.0.0 DOCSTYLE_API_PORT=8001 uv run python -m web.run_api
```

Swagger UI:

`http://localhost:8000/docs`

If startup seems to do nothing, usually port 8000 is already in use. Check with:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

## Endpoints

- `GET /health`
- `GET /templates`
- `GET /settings/ai`
- `POST /settings/ai`
- `POST /convert` (multipart)
  - `file`: `.md` or `.docx`
  - `template_id`: `01`..`50`
  - `custom_settings`: JSON string
- `POST /ai/organize`
- `POST /ai/draft`
- `POST /ai/toc`
- `POST /ai/inline-edit`
- `POST /structure/check`
- `POST /structure/normalize`
- `POST /insight/guide`
- `POST /insight/chat`

## Example `curl` convert

```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@sample_docs/1_essay.md" \
  -F "template_id=01" \
  -F 'custom_settings={"style_preset":"magazine","auto_polish":true}' \
  --output result.docx
```
