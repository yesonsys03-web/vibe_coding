"""
json_builder.py — ParsedDocument → JSON 직렬화

generate.js 가 기대하는 JSON 형식으로 변환한다.
각 dataclass 타입별로 직렬화 규칙을 명확히 분리한다.
"""

from __future__ import annotations

import json
from pathlib import Path

from parser.models import (
    BulletsElement,
    ConclusionElement,
    DocumentElement,
    ElementType,
    HRElement,
    ImageElement,
    ParsedDocument,
    PromptElement,
    QAElement,
    TableElement,
    TextElement,
    EmptyElement,
)


# ─────────────────────────────────────────────
# 요소별 직렬화
# ─────────────────────────────────────────────

def _serialize_element(el: DocumentElement) -> dict | None:
    """
    dataclass 하나를 JSON-직렬화 가능한 dict 로 변환.
    None 을 반환하면 해당 요소는 건너뜀.
    """

    if isinstance(el, TextElement):
        t = el.type.value

        if t == ElementType.CHAPTER_TITLE.value:
            return {
                "type":  "chapter_title",
                "phase": el.phase,
                "text":  el.text,
                "sub":   el.sub,
            }

        if t == ElementType.H1.value:
            return {"type": "h1", "num": el.num or "•", "text": el.text}

        if t == ElementType.H2.value:
            return {"type": "h2", "text": el.text}

        if t == ElementType.H3.value:
            return {"type": "h3", "text": el.text}

        if t == ElementType.BODY.value:
            d: dict = {"type": "body", "text": el.text}
            if el.indent:
                d["indent"] = el.indent
            return d

        if t == ElementType.QUOTE.value:
            return {"type": "quote", "text": el.text}

        if t == ElementType.INSIGHT.value:
            return {"type": "insight", "text": el.text}

        if t == ElementType.TIP.value:
            return {"type": "tip", "text": el.text}

        if t == ElementType.WARNING.value:
            return {"type": "warning", "text": el.text}

        if t == ElementType.CAPTION.value:
            # 캡션은 _absorb_captions 에서 이미지에 흡수됐어야 함
            # 혹시 남아있으면 body 로 처리
            return {"type": "body", "text": el.text}

        if t == ElementType.IMAGE_PLACEHOLDER.value:
            return {"type": "image_placeholder", "caption": el.text}

        # 기타 (BULLETS 단일 항목이 남아있는 경우)
        return {"type": "body", "text": el.text}

    if isinstance(el, QAElement):
        return {
            "type":     "qa",
            "question": el.question,
            "answers":  el.answers,
        }

    if isinstance(el, PromptElement):
        return {
            "type":  "prompt",
            "label": el.label,
            "text":  el.text,
        }

    if isinstance(el, ConclusionElement):
        return {"type": "conclusion", "lines": el.lines}

    if isinstance(el, BulletsElement):
        return {"type": "bullets", "items": el.items}

    if isinstance(el, ImageElement):
        return {
            "type":       "image",
            "filename":   el.filename,
            "width_emu":  el.width_emu,
            "height_emu": el.height_emu,
            "caption":    el.caption,
        }

    if isinstance(el, TableElement):
        if el.type == ElementType.TABLE2:
            return {
                "type": "table2",
                "col1": el.col1,
                "col2": el.col2,
                "rows": el.rows,
            }
        return {
            "type":    "table3",
            "headers": el.headers,
            "rows":    el.rows,
        }

    if isinstance(el, HRElement):
        return {"type": "hr", "size": el.size}

    if isinstance(el, EmptyElement):
        return {"type": "empty", "height": el.height}

    return None


# ─────────────────────────────────────────────
# 메인 직렬화 함수
# ─────────────────────────────────────────────

def build_json(
    parsed: ParsedDocument,
    template_id: str = "01",
    custom_settings: dict = None,
    output_path: str | None = None,
) -> str:
    """
    ParsedDocument 를 generate.js 입력 JSON 문자열로 변환.

    Parameters
    ----------
    parsed       : parse() 가 반환한 ParsedDocument
    template_id  : "01" ~ "10"
    custom_settings : 사용자 설정 (폰트, 여백 등) dict
    output_path  : 지정하면 파일로 저장

    Returns
    -------
    JSON 문자열
    """
    serialized_elements = []
    for el in parsed.elements:
        d = _serialize_element(el)
        if d is not None:
            serialized_elements.append(d)

    payload = {
        "template":      template_id,
        "custom_settings": custom_settings or {},
        "meta": {
            "title":   parsed.meta.title,
            "author":  parsed.meta.author,
            "chapter": parsed.meta.chapter,
        },
        "image_base_dir": parsed.image_base_dir,
        "elements":       serialized_elements,
    }

    json_str = json.dumps(payload, ensure_ascii=False, indent=2)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(json_str, encoding="utf-8")

    return json_str
