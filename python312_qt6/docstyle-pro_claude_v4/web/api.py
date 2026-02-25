from __future__ import annotations

import json
import re
import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from bridge.ai_organizer import (
    chat_with_vault,
    generate_draft,
    generate_guide_questions,
    generate_toc,
    inline_edit,
    organize_text,
)
from bridge.converter import convert
from gui.structure_doctor import (
    inspect_markdown_structure,
    normalize_markdown_structure,
)


ROOT = Path(__file__).resolve().parent.parent
ENGINE_DIR = ROOT / "engine"
GENERATE_JS = ENGINE_DIR / "generate.js"
AI_CREDENTIALS_FILE = ROOT / "settings" / "ai_credentials.json"


def _category_from_template_id(tid: str) -> str:
    category_map = {
        "01": "Editorial",
        "02": "Life & Culture",
        "03": "Business",
        "04": "Life & Culture",
        "05": "Education",
        "06": "Tech",
        "07": "Life & Culture",
        "08": "Life & Culture",
        "09": "Life & Culture",
        "10": "Editorial",
        "11": "Medical",
        "12": "Legal",
        "13": "Education",
        "14": "Life & Culture",
        "15": "Business",
        "16": "Life & Culture",
        "17": "Life & Culture",
        "18": "Life & Culture",
        "19": "Life & Culture",
        "20": "Business",
        "21": "Tech",
        "22": "Tech",
        "23": "Life & Culture",
        "24": "Life & Culture",
        "25": "Tech",
        "26": "Life & Culture",
        "27": "Life & Culture",
        "28": "Life & Culture",
        "29": "Business",
        "30": "Life & Culture",
        "31": "Medical",
        "32": "Medical",
        "33": "Legal",
        "34": "Legal",
        "35": "Education",
        "36": "Education",
        "37": "Life & Culture",
        "38": "Life & Culture",
        "39": "Business",
        "40": "Business",
        "41": "Tech",
        "42": "Tech",
        "43": "Life & Culture",
        "44": "Life & Culture",
        "45": "Life & Culture",
        "46": "Life & Culture",
        "47": "Life & Culture",
        "48": "Life & Culture",
        "49": "Life & Culture",
        "50": "Business",
    }
    return category_map.get(tid, "Life & Culture")


class DraftRequest(BaseModel):
    title: str = Field(min_length=1)
    subtitle: str = ""
    header: str = ""
    toc: str = ""


class TocRequest(BaseModel):
    title: str = Field(min_length=1)
    subtitle: str = ""
    header: str = ""


class InlineEditRequest(BaseModel):
    text: str = Field(min_length=1)
    mode: str = Field(pattern=r"^(polish|expand|summarize)$")


class OrganizeRequest(BaseModel):
    text: str = Field(min_length=1)


class StructureRequest(BaseModel):
    text: str = Field(min_length=1)


class InsightGuideRequest(BaseModel):
    filter_files: list[str] = []


class InsightChatRequest(BaseModel):
    query: str = Field(min_length=1)
    filter_files: list[str] = []


class AiSettingsUpdateRequest(BaseModel):
    provider: str = "OpenAI (ChatGPT)"
    openai_key: str = ""
    claude_key: str = ""
    gemini_key: str = ""
    groq_key: str = ""


app = FastAPI(title="DocStyle Pro API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _parse_template_registry() -> list[dict]:
    if not GENERATE_JS.exists():
        return []

    src = GENERATE_JS.read_text(encoding="utf-8")
    rows = re.findall(r'"(\d{2})":\s*"(\./templates/[^"]+)"', src)
    out: list[dict] = []

    for tid, rel in rows:
        js_path = (ENGINE_DIR / rel.replace("./", "")).with_suffix(".js")
        name = f"Template {tid}"
        tag = ""
        desc = ""
        header = "#1E293B"
        accent = "#2563EB"
        box_bg = "#EFF6FF"
        box_border = "#93C5FD"
        header_text = "#FFFFFF"
        if js_path.exists():
            tpl_src = js_path.read_text(encoding="utf-8")
            m_name = re.search(r'NAME:\s*"([^"]+)"', tpl_src)
            m_tag = re.search(r'TAG:\s*"([^"]*)"', tpl_src)
            m_desc = re.search(r'DESC:\s*"([^"]*)"', tpl_src)
            m_header = re.search(r'BG_HEAD:\s*"([0-9A-Fa-f]{6})"', tpl_src)
            m_accent = re.search(r'ACCENT:\s*"([0-9A-Fa-f]{6})"', tpl_src)
            m_box_bg = re.search(r'BG_BOX:\s*"([0-9A-Fa-f]{6})"', tpl_src)
            m_box_border = re.search(r'BOX_BORDER:\s*"([0-9A-Fa-f]{6})"', tpl_src)
            m_white = re.search(r'WHITE:\s*"([0-9A-Fa-f]{6})"', tpl_src)
            if m_name:
                name = m_name.group(1)
            if m_tag:
                tag = m_tag.group(1)
            if m_desc:
                desc = m_desc.group(1)
            if m_header:
                header = f"#{m_header.group(1)}"
            if m_accent:
                accent = f"#{m_accent.group(1)}"
            if m_box_bg:
                box_bg = f"#{m_box_bg.group(1)}"
            if m_box_border:
                box_border = f"#{m_box_border.group(1)}"
            if m_white:
                header_text = f"#{m_white.group(1)}"
        out.append(
            {
                "id": tid,
                "category": _category_from_template_id(tid),
                "name": name,
                "tag": tag,
                "desc": desc,
                "header": header,
                "header_text": header_text,
                "accent": accent,
                "box_bg": box_bg,
                "box_border": box_border,
            }
        )

    return out


def _default_ai_settings() -> dict:
    return {
        "provider": "OpenAI (ChatGPT)",
        "openai_key": "",
        "claude_key": "",
        "gemini_key": "",
        "gemini_token": None,
        "groq_key": "",
    }


def _load_ai_settings() -> dict:
    AI_CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if AI_CREDENTIALS_FILE.exists():
        try:
            raw = json.loads(AI_CREDENTIALS_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                merged = _default_ai_settings()
                merged.update(raw)
                return merged
        except Exception:
            pass
    return _default_ai_settings()


def _save_ai_settings(data: dict) -> None:
    AI_CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    AI_CREDENTIALS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/templates")
def list_templates() -> dict:
    return {"templates": _parse_template_registry()}


@app.get("/settings/ai")
def get_ai_settings() -> dict:
    data = _load_ai_settings()
    return {
        "provider": data.get("provider", "OpenAI (ChatGPT)"),
        "has_openai_key": bool(data.get("openai_key")),
        "has_claude_key": bool(data.get("claude_key")),
        "has_gemini_key": bool(data.get("gemini_key")),
        "has_groq_key": bool(data.get("groq_key")),
        "has_gemini_oauth": bool(data.get("gemini_token")),
    }


@app.post("/settings/ai")
def update_ai_settings(req: AiSettingsUpdateRequest) -> dict:
    data = _load_ai_settings()

    data["provider"] = req.provider
    if req.openai_key.strip():
        data["openai_key"] = req.openai_key.strip()
    if req.claude_key.strip():
        data["claude_key"] = req.claude_key.strip()
    if req.gemini_key.strip():
        data["gemini_key"] = req.gemini_key.strip()
    if req.groq_key.strip():
        data["groq_key"] = req.groq_key.strip()

    _save_ai_settings(data)
    return {"ok": True}


@app.post("/convert")
async def convert_document(
    file: UploadFile = File(...),
    template_id: str = Form("01"),
    custom_settings: str = Form("{}"),
) -> Response:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".md", ".docx"}:
        raise HTTPException(status_code=400, detail="Only .md or .docx is supported")

    try:
        settings = json.loads(custom_settings) if custom_settings else {}
        if not isinstance(settings, dict):
            raise ValueError("custom_settings must be a JSON object")
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Invalid custom_settings JSON: {exc}"
        ) from exc

    temp_dir = Path(tempfile.mkdtemp(prefix="docstyle_web_"))
    input_path = temp_dir / f"input{suffix}"
    output_path = temp_dir / "output.docx"

    try:
        data = await file.read()
        input_path.write_bytes(data)

        result = convert(
            input_path=str(input_path),
            output_path=str(output_path),
            template_id=template_id,
            custom_settings=settings,
            keep_temp=False,
        )

        if not result.success or not output_path.exists():
            raise HTTPException(
                status_code=500, detail=result.error or "convert failed"
            )

        payload = output_path.read_bytes()
        headers = {
            "Content-Disposition": f'attachment; filename="docstyle_{template_id}.docx"',
            "X-DocStyle-Elements": str(result.element_count),
            "X-DocStyle-Images": str(result.image_count),
        }
        return Response(
            content=payload,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers=headers,
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/ai/organize")
def ai_organize(req: OrganizeRequest) -> dict:
    try:
        return {"text": organize_text(req.text)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ai/draft")
def ai_draft(req: DraftRequest) -> dict:
    try:
        return {
            "text": generate_draft(
                title=req.title,
                subtitle=req.subtitle,
                header=req.header,
                toc=req.toc,
            )
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ai/toc")
def ai_toc(req: TocRequest) -> dict:
    try:
        return {
            "text": generate_toc(
                title=req.title,
                subtitle=req.subtitle,
                header=req.header,
            )
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ai/inline-edit")
def ai_inline(req: InlineEditRequest) -> dict:
    try:
        return {"text": inline_edit(text=req.text, mode=req.mode)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/structure/check")
def structure_check(req: StructureRequest) -> dict:
    return inspect_markdown_structure(req.text)


@app.post("/structure/normalize")
def structure_normalize(req: StructureRequest) -> dict:
    normalized, report = normalize_markdown_structure(req.text)
    return {"text": normalized, "report": report}


@app.post("/insight/guide")
def insight_guide(req: InsightGuideRequest) -> dict:
    try:
        questions = generate_guide_questions(filter_files=req.filter_files or [])
        return {"questions": questions}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/insight/chat")
def insight_chat(req: InsightChatRequest) -> dict:
    try:
        answer, contexts = chat_with_vault(
            query_text=req.query,
            filter_files=req.filter_files or [],
        )
        return {"answer": answer, "contexts": contexts}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
