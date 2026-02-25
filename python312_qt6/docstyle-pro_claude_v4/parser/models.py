"""
models.py — DocStyle Pro 파싱 결과 데이터 모델

모든 파서 모듈은 이 파일의 dataclass만 반환한다.
JSON 직렬화는 bridge/json_builder.py 에서 담당한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ─────────────────────────────────────────────
# 요소 타입
# ─────────────────────────────────────────────

class ElementType(str, Enum):
    """generate.js 의 switch-case 와 1:1 대응"""
    CHAPTER_TITLE     = "chapter_title"
    H1                = "h1"
    H2                = "h2"
    H3                = "h3"
    BODY              = "body"
    QUOTE             = "quote"          # 들여쓰기 단락
    INSIGHT           = "insight"        # 강조 박스
    TIP               = "tip"
    WARNING           = "warning"
    QA                = "qa"
    PROMPT            = "prompt"
    CONCLUSION        = "conclusion"
    BULLETS           = "bullets"
    IMAGE             = "image"          # 실제 이미지 파일 존재
    IMAGE_PLACEHOLDER = "image_placeholder"
    TABLE2            = "table2"
    TABLE3            = "table3"
    HR                = "hr"
    EMPTY             = "empty"
    CAPTION           = "caption"        # 이미지 직후 짧은 설명 (내부 처리용)


# ─────────────────────────────────────────────
# 개별 요소 dataclass
# ─────────────────────────────────────────────

@dataclass
class TextElement:
    """h1 ~ h3, body, quote, insight, tip, warning"""
    type:   ElementType
    text:   str         = ""
    num:    str         = ""     # h1 번호 ("1", "2" …)
    sub:    str         = ""     # chapter_title 부제
    phase:  str         = ""     # chapter_title 페이즈 "[Phase 9]"
    indent: int         = 0      # body 들여쓰기 DXA
    bold:   bool        = False
    italic: bool        = False


@dataclass
class QAElement:
    type:     ElementType = ElementType.QA
    question: str         = ""
    answers:  list[str]   = field(default_factory=list)


@dataclass
class PromptElement:
    type:   ElementType = ElementType.PROMPT
    label:  str         = ""
    text:   str         = ""


@dataclass
class ConclusionElement:
    type:  ElementType = ElementType.CONCLUSION
    lines: list[str]   = field(default_factory=list)


@dataclass
class BulletsElement:
    type:  ElementType = ElementType.BULLETS
    items: list[str]   = field(default_factory=list)


@dataclass
class ImageElement:
    type:       ElementType = ElementType.IMAGE
    filename:   str         = ""    # image1.png
    local_path: str         = ""    # temp/images/{uuid}/image1.png
    width_emu:  int         = 0
    height_emu: int         = 0
    caption:    str         = ""


@dataclass
class TableElement:
    type:    ElementType  = ElementType.TABLE2
    col1:    str          = ""     # table2 헤더
    col2:    str          = ""
    headers: list[str]    = field(default_factory=list)  # table3 헤더
    rows:    list         = field(default_factory=list)
    # table2 rows: [[왼쪽, 오른쪽], ...]
    # table3 rows: [[col1, col2, col3], ...]


@dataclass
class HRElement:
    type: ElementType = ElementType.HR
    size: int         = 4


@dataclass
class EmptyElement:
    type:   ElementType = ElementType.EMPTY
    height: int         = 120


# ─────────────────────────────────────────────
# 문서 최상위 모델
# ─────────────────────────────────────────────

# 요소 유니언 타입 (타입 힌트용)
DocumentElement = (
    TextElement
    | QAElement
    | PromptElement
    | ConclusionElement
    | BulletsElement
    | ImageElement
    | TableElement
    | HRElement
    | EmptyElement
)


@dataclass
class DocMeta:
    """문서 메타 정보"""
    title:   str = ""
    author:  str = ""
    chapter: str = ""
    sub:     str = ""   # 챕터 부제 (DS-ChapterTitle 에서 추출)


@dataclass
class ParsedDocument:
    """
    파서 전체 결과물.
    bridge/json_builder.py 가 이 객체를 JSON으로 직렬화한다.
    """
    meta:          DocMeta        = field(default_factory=DocMeta)
    elements:      list           = field(default_factory=list)
    image_map:     dict[str, str] = field(default_factory=dict)
    # image_map = {"image1.png": "temp/images/abc123/image1.png"}
    image_base_dir: str           = ""
