"""
structure_analyzer.py — DocStyle Pro 구조 분석기 v2

분류 우선순위
──────────────────────────────────────────────────────
1. DS-* 커스텀 스타일 이름  (100% 정확)
2. 표준 Word 헤딩 스타일    (Heading 1 / 2 / 3)
3. 폰트 크기 기반 추론      (커스텀 스타일 없는 문서 대비)
4. 전체 Bold + 짧은 문장    (h3 추정)
5. 들여쓰기                 (quote 추정)
6. 나머지                   (body)

DS-* 스타일 매핑
──────────────────────────────────────────────────────
DS-ChapterTitle   → chapter_title
DS-Insight        → insight
DS-Tip            → tip
DS-Warning        → warning
DS-Quote          → quote
DS-QA-Question    → qa (question)
DS-QA-Answer      → qa (answer, 직전 qa 에 병합)
DS-Prompt         → prompt
DS-Conclusion     → conclusion
DS-Caption        → caption
"""

from __future__ import annotations

import re
from typing import Optional

from docx.oxml.ns import qn
from docx.shared import Pt

from .models import (
    BulletsElement,
    ConclusionElement,
    DocumentElement,
    ElementType,
    HRElement,
    ImageElement,
    PromptElement,
    QAElement,
    TableElement,
    TextElement,
)


# ─────────────────────────────────────────────
# DS-* 스타일 → ElementType 매핑
# ─────────────────────────────────────────────

_DS_STYLE_MAP: dict[str, ElementType] = {
    "ds-chaptertitle" : ElementType.CHAPTER_TITLE,
    "ds-insight"      : ElementType.INSIGHT,
    "ds-tip"          : ElementType.TIP,
    "ds-warning"      : ElementType.WARNING,
    "ds-quote"        : ElementType.QUOTE,
    "ds-qa-question"  : ElementType.QA,
    "ds-qa-answer"    : ElementType.QA,       # 후처리로 직전 QAElement 에 병합
    "ds-prompt"       : ElementType.PROMPT,
    "ds-conclusion"   : ElementType.CONCLUSION,
    "ds-caption"      : ElementType.CAPTION,
}


# ─────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────

def _style_name(para) -> str:
    """단락 스타일 이름을 소문자로 반환"""
    try:
        return (para.style.name or "").lower().strip()
    except Exception:
        return ""


def _font_size_pt(para) -> float:
    """단락 내 최대 폰트 크기(pt)"""
    sizes = []
    for run in para.runs:
        if run.font.size:
            sizes.append(run.font.size.pt)
    pPr = para._p.find(qn("w:pPr"))
    if pPr is not None:
        rPr = pPr.find(qn("w:rPr"))
        if rPr is not None:
            sz = rPr.find(qn("w:sz"))
            if sz is not None:
                val = sz.get(qn("w:val"))
                if val:
                    sizes.append(int(val) / 2)
    return max(sizes) if sizes else 0.0


def _indent_twips(para) -> int:
    try:
        ind = para.paragraph_format.left_indent
        return int(ind) if ind is not None else 0
    except Exception:
        return 0


def _all_bold(para) -> bool:
    runs = para.runs
    return bool(runs) and all(r.bold for r in runs)


def _clean_text(para) -> str:
    return re.sub(r"\s+", " ", para.text).strip()


def _has_image(para) -> bool:
    return bool(para._p.findall(".//" + qn("w:drawing")))


def _is_list_para(para) -> bool:
    if "list" in _style_name(para):
        return True
    return para._p.find(".//" + qn("w:numPr")) is not None


def _extract_image_rel_id(para) -> tuple[str, int, int]:
    """(rId, width_emu, height_emu)"""
    drawing = para._p.find(".//" + qn("w:drawing"))
    if drawing is None:
        return "", 0, 0
    extent = drawing.find(".//" + qn("wp:extent"))
    w = int(extent.get("cx", 0)) if extent is not None else 0
    h = int(extent.get("cy", 0)) if extent is not None else 0
    blip = drawing.find(".//" + qn("a:blip"))
    r_id = ""
    if blip is not None:
        r_id = blip.get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed", ""
        )
    return r_id, w, h


# ─────────────────────────────────────────────
# Prompt 라벨 파싱
# ─────────────────────────────────────────────

def _parse_prompt_label(text: str) -> tuple[str, str]:
    """
    'PrompT 라벨: 본문 텍스트' 또는 '라벨:' + 다음 줄 텍스트
    단일 단락인 경우 ':' 앞을 라벨로 처리.
    """
    m = re.match(r"^(.{1,30})[:：]\s*(.+)$", text)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return "", text


# ─────────────────────────────────────────────
# 단락 분류 (핵심 함수)
# ─────────────────────────────────────────────

def classify_paragraph(
    para,
    image_map: dict[str, str],
    rel_map: dict[str, str],
    prev_element: Optional[DocumentElement] = None,
) -> Optional[DocumentElement]:
    """
    단락 하나를 분류하여 적절한 dataclass 반환.
    None 반환 시 해당 단락 건너뜀.

    Parameters
    ----------
    para          : docx Paragraph
    image_map     : {"image1.png": "/abs/path/..."}
    rel_map       : {"rId5": "image1.png"}
    prev_element  : 직전 요소 (QA 답변 병합, 캡션 흡수에 사용)
    """
    style  = _style_name(para)
    text   = _clean_text(para)
    size   = _font_size_pt(para)
    indent = _indent_twips(para)

    # ── 1순위: 이미지 단락 ────────────────────
    if _has_image(para):
        r_id, w_emu, h_emu = _extract_image_rel_id(para)
        filename   = rel_map.get(r_id, "")
        local_path = image_map.get(filename, "")
        caption    = text   # 같은 단락에 텍스트가 있으면 캡션으로
        if local_path:
            return ImageElement(
                type=ElementType.IMAGE,
                filename=filename,
                local_path=local_path,
                width_emu=w_emu,
                height_emu=h_emu,
                caption=caption,
            )
        return TextElement(
            type=ElementType.IMAGE_PLACEHOLDER,
            text=caption or "이미지",
        )

    # ── 빈 단락 제거 ──────────────────────────
    if not text:
        return None

    # ── 2순위: DS-* 커스텀 스타일 ────────────
    if style in _DS_STYLE_MAP:
        elem_type = _DS_STYLE_MAP[style]

        if style == "ds-chaptertitle":
            return TextElement(type=ElementType.CHAPTER_TITLE, text=text)

        if style in ("ds-insight", "ds-tip", "ds-warning", "ds-quote"):
            return TextElement(type=elem_type, text=text)

        if style == "ds-qa-question":
            return QAElement(
                type=ElementType.QA,
                question=text,
                answers=[],
            )

        if style == "ds-qa-answer":
            # 직전 요소가 QAElement 이면 answers 에 추가
            if isinstance(prev_element, QAElement):
                prev_element.answers.append(text)
                return None   # 새 요소 생성 없이 병합
            # 직전이 QA 가 아닌 경우 새 QA 로 생성
            return QAElement(
                type=ElementType.QA,
                question="",
                answers=[text],
            )

        if style == "ds-prompt":
            label, body = _parse_prompt_label(text)
            return PromptElement(
                type=ElementType.PROMPT,
                label=label,
                text=body,
            )

        if style == "ds-conclusion":
            # DS-Conclusion 연속 단락은 후처리에서 병합
            return TextElement(type=ElementType.CONCLUSION, text=text)

        if style == "ds-caption":
            return TextElement(type=ElementType.CAPTION, text=text)

    # ── 3순위: 표준 Word 헤딩 스타일 ────────
    if "heading 1" in style or style in ("제목 1", "heading1"):
        return TextElement(type=ElementType.H1, text=text)
    if "heading 2" in style or style in ("제목 2", "heading2"):
        return TextElement(type=ElementType.H2, text=text)
    if "heading 3" in style or style in ("제목 3", "heading3"):
        return TextElement(type=ElementType.H3, text=text)

    # ── 4순위: 목록 ──────────────────────────
    if _is_list_para(para):
        return TextElement(type=ElementType.BULLETS, text=text)

    # ── 5순위: 폰트 크기 추론 ────────────────
    if size >= 28:
        return TextElement(type=ElementType.H1, text=text)
    if size >= 24:
        return TextElement(type=ElementType.H2, text=text)
    if size >= 20:
        return TextElement(type=ElementType.H3, text=text)

    # ── 6순위: Bold + 짧은 문장 → h3 추정 ───
    if _all_bold(para) and len(text) <= 60:
        return TextElement(type=ElementType.H3, text=text)

    # ── 7순위: 들여쓰기 → quote 추정 ─────────
    if indent >= 720:
        return TextElement(type=ElementType.QUOTE, text=text)

    # ── 기본: body ────────────────────────────
    return TextElement(type=ElementType.BODY, text=text)


# ─────────────────────────────────────────────
# 표 분류
# ─────────────────────────────────────────────

def classify_table(tbl) -> TableElement:
    raw_rows: list[list[str]] = []
    for row in tbl.rows:
        raw_rows.append([cell.text.strip() for cell in row.cells])

    if not raw_rows:
        return TableElement(type=ElementType.TABLE2, rows=[])

    num_cols = max(len(r) for r in raw_rows)

    if num_cols <= 2:
        header = raw_rows[0]
        data   = raw_rows[1:]
        return TableElement(
            type=ElementType.TABLE2,
            col1=header[0] if len(header) > 0 else "",
            col2=header[1] if len(header) > 1 else "",
            rows=data,
        )
    else:
        return TableElement(
            type=ElementType.TABLE3,
            headers=raw_rows[0],
            rows=raw_rows[1:],
        )


# ─────────────────────────────────────────────
# 후처리 1: 불릿 단락 병합
# ─────────────────────────────────────────────

def merge_bullet_runs(elements: list) -> list:
    """연속된 BULLETS TextElement → BulletsElement 병합"""
    merged: list = []
    i = 0
    while i < len(elements):
        el = elements[i]
        if isinstance(el, TextElement) and el.type == ElementType.BULLETS:
            items = [el.text]
            while i + 1 < len(elements):
                nxt = elements[i + 1]
                if isinstance(nxt, TextElement) and nxt.type == ElementType.BULLETS:
                    items.append(nxt.text)
                    i += 1
                else:
                    break
            merged.append(BulletsElement(type=ElementType.BULLETS, items=items))
        else:
            merged.append(el)
        i += 1
    return merged


# ─────────────────────────────────────────────
# 후처리 2: DS-Conclusion 연속 단락 병합
# ─────────────────────────────────────────────

def merge_conclusion_runs(elements: list) -> list:
    """
    연속된 CONCLUSION TextElement → ConclusionElement 병합.
    DS-Conclusion 스타일 단락 여러 줄을 lines 로 모은다.
    """
    merged: list = []
    i = 0
    while i < len(elements):
        el = elements[i]
        if isinstance(el, TextElement) and el.type == ElementType.CONCLUSION:
            lines = [el.text]
            while i + 1 < len(elements):
                nxt = elements[i + 1]
                if isinstance(nxt, TextElement) and nxt.type == ElementType.CONCLUSION:
                    lines.append(nxt.text)
                    i += 1
                else:
                    break
            merged.append(ConclusionElement(
                type=ElementType.CONCLUSION,
                lines=lines,
            ))
        else:
            merged.append(el)
        i += 1
    return merged


# ─────────────────────────────────────────────
# 후처리 3: 이미지 뒤 캡션 흡수
# ─────────────────────────────────────────────

def absorb_captions(elements: list) -> list:
    """IMAGE / IMAGE_PLACEHOLDER 직후 CAPTION → 이미지 caption 필드에 흡수"""
    result = []
    i = 0
    while i < len(elements):
        el = elements[i]
        result.append(el)
        is_img = isinstance(el, ImageElement) or (
            isinstance(el, TextElement) and el.type == ElementType.IMAGE_PLACEHOLDER
        )
        if is_img and i + 1 < len(elements):
            nxt = elements[i + 1]
            if isinstance(nxt, TextElement) and nxt.type == ElementType.CAPTION:
                if isinstance(el, ImageElement):
                    el.caption = nxt.text
                else:
                    el.text = nxt.text
                i += 1
        i += 1
    return result


# ─────────────────────────────────────────────
# 후처리 4: Prompt 라벨 보완
# (DS-Prompt 앞 단락이 "라벨:" 형식이면 라벨로 흡수)
# ─────────────────────────────────────────────

def absorb_prompt_labels(elements: list) -> list:
    """
    DS-Prompt 바로 앞 body 단락이 '라벨:' 패턴이면
    해당 텍스트를 PromptElement.label 로 이동하고 body 단락을 제거한다.
    """
    result = []
    i = 0
    while i < len(elements):
        el = elements[i]
        if (
            isinstance(el, PromptElement)
            and not el.label
            and result
        ):
            prev = result[-1]
            if isinstance(prev, TextElement) and prev.type == ElementType.BODY:
                m = re.match(r"^(.{1,30})[:：]\s*$", prev.text)
                if m:
                    el.label = m.group(1).strip()
                    result.pop()   # 라벨 body 단락 제거
        result.append(el)
        i += 1
    return result
