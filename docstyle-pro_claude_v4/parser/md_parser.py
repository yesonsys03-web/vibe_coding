"""
md_parser.py — DocStyle Pro 구조화 마크다운 파서

기존 docx_parser.py 가 서식 정보(들여쓰기·폰트 크기)로 의미를 추론했던 것과 달리
이 파서는 사용자가 직접 명시한 태그를 읽어 100% 정확하게 요소 타입을 복원한다.

────────────────────────────────────────────────────────────────
마크다운 문법 규칙
────────────────────────────────────────────────────────────────

1. 메타데이터 (파일 맨 위, 필수)
   ---
   title:   나의 데이터는 배신하지 않는다
   author:  박인찬
   chapter: "[Phase 9]"
   sub:     법률 문서 분석 · 나홀로 소송
   ---

2. 요소 태그  →  [태그명] 또는 [태그명 | 파라미터]
   태그는 반드시 빈 줄 다음에 단독 행으로 작성

   [chapter_title]        챕터 타이틀 (메타데이터의 chapter/sub 사용)
   [insight]              강조 박스 (빨간 좌측 선)
   [tip]                  Tip 박스 (초록)
   [warning]              주의 박스 (황색)
   [quote]                인용 박스 (파란 좌측 선)
   [conclusion]           결론 박스 (다크 배경 + 빨간 선)
   [qa]                   Q&A 블록
   [prompt | 레이블]      골든 프롬프트 박스
   [image | 캡션]         이미지 (다음 줄에 파일명)
   [table2 | 헤더1 | 헤더2]   2열 표 (각 행은 "값1 | 값2")
   [table3 | 헤더1 | 헤더2 | 헤더3]  3열 표
   [hr]                   구분선
   [empty]                빈 줄 (간격)

3. 표준 마크다운
   # 1. 제목          →  h1 (번호 자동 분리)
   ## 소제목          →  h2
   ### 세부 제목      →  h3
   - 항목             →  bullets (연속 행 자동 병합)
   ---                →  hr

4. Q&A 블록 내부 문법
   [qa]
   Q: 질문 내용
   A: 답변 첫 번째
   A: 답변 두 번째

5. 일반 텍스트 (태그 없는 줄)  →  body

────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from .models import (
    BulletsElement,
    ConclusionElement,
    DocMeta,
    DocumentElement,
    ElementType,
    HRElement,
    EmptyElement,
    ImageElement,
    ParsedDocument,
    PromptElement,
    QAElement,
    TableElement,
    TextElement,
)


# ─────────────────────────────────────────────
# 정규식
# ─────────────────────────────────────────────

_RE_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_RE_TAG_LINE    = re.compile(r"^\[([^\]|]+)(?:\s*\|\s*([^\]]*))?\]\s*$")
_RE_H1          = re.compile(r"^#\s+(.+)$")
_RE_H2          = re.compile(r"^##\s+(.+)$")
_RE_H3          = re.compile(r"^###\s+(.+)$")
_RE_BULLET      = re.compile(r"^[-*]\s+(.+)$")
_RE_HR          = re.compile(r"^---+\s*$")
_RE_H1_NUM      = re.compile(r"^(\d+)\.\s+(.+)$")   # "1. 제목" → ("1", "제목")


# ─────────────────────────────────────────────
# 메타데이터 파싱
# ─────────────────────────────────────────────

def _parse_frontmatter(text: str) -> tuple[DocMeta, str]:
    """
    YAML 프론트매터를 파싱하여 DocMeta 와 나머지 본문을 반환.
    프론트매터가 없으면 빈 DocMeta 반환.
    """
    meta = DocMeta()
    m = _RE_FRONTMATTER.match(text)
    if not m:
        return meta, text

    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip().lower()
        val = val.strip().strip('"').strip("'")
        if key == "title":
            meta.title = val
        elif key == "author":
            meta.author = val
        elif key == "chapter":
            meta.chapter = val
        elif key == "sub":
            meta.sub = val   # type: ignore[attr-defined]  # DocMeta 확장 허용

    body = text[m.end():]
    return meta, body


# ─────────────────────────────────────────────
# 블록 토크나이저
# ─────────────────────────────────────────────

class _Block:
    """파싱 중간 단계 블록"""
    __slots__ = ("tag", "params", "lines")

    def __init__(self, tag: str = "body", params: list[str] | None = None):
        self.tag    = tag
        self.params = params or []
        self.lines: list[str] = []

    def text(self) -> str:
        return "\n".join(self.lines).strip()


def _tokenize(body: str) -> list[_Block]:
    """
    본문을 블록 단위로 분리.
    각 [태그] 행이 새 블록의 시작점이 된다.
    """
    blocks: list[_Block] = []
    current = _Block("body")

    for raw_line in body.splitlines():
        line = raw_line.rstrip()

        # 태그 행 감지
        m = _RE_TAG_LINE.match(line)
        if m:
            if current.lines or current.tag != "body":
                blocks.append(current)
            tag    = m.group(1).strip().lower()
            params = [p.strip() for p in m.group(2).split("|")] if m.group(2) else []
            current = _Block(tag, params)
            continue

        # 표준 마크다운 헤딩 — 현재 블록을 닫고 새 블록으로
        if _RE_H1.match(line):
            if current.lines or current.tag != "body":
                blocks.append(current)
            current = _Block("h1")
            current.lines.append(line[2:].strip())   # "# " 제거
            blocks.append(current)
            current = _Block("body")
            continue

        if _RE_H2.match(line):
            if current.lines or current.tag != "body":
                blocks.append(current)
            current = _Block("h2")
            current.lines.append(line[3:].strip())
            blocks.append(current)
            current = _Block("body")
            continue

        if _RE_H3.match(line):
            if current.lines or current.tag != "body":
                blocks.append(current)
            current = _Block("h3")
            current.lines.append(line[4:].strip())
            blocks.append(current)
            current = _Block("body")
            continue

        # HR (---)
        if _RE_HR.match(line) and current.tag == "body" and not current.lines:
            blocks.append(_Block("hr"))
            continue

        current.lines.append(line)

    if current.lines or current.tag != "body":
        blocks.append(current)

    return blocks


# ─────────────────────────────────────────────
# 블록 → dataclass 변환
# ─────────────────────────────────────────────

def _convert_block(block: _Block, meta: DocMeta, image_dir: str) -> list[DocumentElement]:
    """블록 하나를 dataclass 목록으로 변환"""

    tag   = block.tag
    text  = block.text()
    lines = [l for l in block.lines if l.strip()]

    # ── chapter_title ──────────────────────────
    if tag == "chapter_title":
        sub = getattr(meta, "sub", "")
        return [TextElement(
            type=ElementType.CHAPTER_TITLE,
            text=meta.title,
            phase=meta.chapter,
            sub=sub,
        )]

    # ── h1 ─────────────────────────────────────
    if tag == "h1":
        m = _RE_H1_NUM.match(text)
        if m:
            return [TextElement(type=ElementType.H1, num=m.group(1), text=m.group(2))]
        return [TextElement(type=ElementType.H1, num="•", text=text)]

    # ── h2 ─────────────────────────────────────
    if tag == "h2":
        return [TextElement(type=ElementType.H2, text=text)]

    # ── h3 ─────────────────────────────────────
    if tag == "h3":
        return [TextElement(type=ElementType.H3, text=text)]

    # ── 텍스트 박스 단일 타입들 ─────────────────
    if tag in {"insight", "tip", "warning", "quote"}:
        type_map = {
            "insight": ElementType.INSIGHT,
            "tip":     ElementType.TIP,
            "warning": ElementType.WARNING,
            "quote":   ElementType.QUOTE,
        }
        return [TextElement(type=type_map[tag], text=text)]

    # ── conclusion ────────────────────────────
    if tag == "conclusion":
        return [ConclusionElement(
            type=ElementType.CONCLUSION,
            lines=lines,
        )]

    # ── qa ────────────────────────────────────
    if tag == "qa":
        question = ""
        answers: list[str] = []
        for l in lines:
            if l.startswith("Q:") or l.startswith("Q："):
                question = l[2:].strip()
            elif l.startswith("A:") or l.startswith("A："):
                answers.append(l[2:].strip())
        return [QAElement(
            type=ElementType.QA,
            question=question,
            answers=answers,
        )]

    # ── prompt ────────────────────────────────
    if tag == "prompt":
        label = block.params[0] if block.params else ""
        return [PromptElement(
            type=ElementType.PROMPT,
            label=label,
            text=text,
        )]

    # ── image ─────────────────────────────────
    if tag == "image":
        caption  = block.params[0] if block.params else ""
        filename = lines[0].strip() if lines else ""
        local_path = str(Path(image_dir) / filename) if filename else ""
        if filename and Path(local_path).exists():
            return [ImageElement(
                type=ElementType.IMAGE,
                filename=filename,
                local_path=local_path,
                width_emu=0,
                height_emu=0,
                caption=caption,
            )]
        return [TextElement(
            type=ElementType.IMAGE_PLACEHOLDER,
            text=caption or filename,
        )]

    # ── table2 ────────────────────────────────
    if tag == "table2":
        col1 = block.params[0] if len(block.params) > 0 else ""
        col2 = block.params[1] if len(block.params) > 1 else ""
        rows = []
        for l in lines:
            parts = [p.strip() for p in l.split("|")]
            if len(parts) >= 2:
                rows.append([parts[0], parts[1]])
        return [TableElement(
            type=ElementType.TABLE2,
            col1=col1, col2=col2,
            rows=rows,
        )]

    # ── table3 ────────────────────────────────
    if tag == "table3":
        headers = block.params[:3] if block.params else []
        rows = []
        for l in lines:
            parts = [p.strip() for p in l.split("|")]
            if len(parts) >= 3:
                rows.append(parts[:3])
        return [TableElement(
            type=ElementType.TABLE3,
            headers=headers,
            rows=rows,
        )]

    # ── hr ────────────────────────────────────
    if tag == "hr":
        return [HRElement(type=ElementType.HR)]

    # ── empty ─────────────────────────────────
    if tag == "empty":
        return [EmptyElement(type=ElementType.EMPTY)]

    # ── body (기본) ───────────────────────────
    if tag == "body":
        results: list[DocumentElement] = []
        bullet_buffer: list[str] = []

        for l in block.lines:
            # 불릿 항목
            bm = _RE_BULLET.match(l)
            if bm:
                bullet_buffer.append(bm.group(1).strip())
                continue

            # 불릿 버퍼 flush
            if bullet_buffer:
                results.append(BulletsElement(
                    type=ElementType.BULLETS,
                    items=bullet_buffer[:],
                ))
                bullet_buffer = []

            stripped = l.strip()
            if stripped:
                results.append(TextElement(type=ElementType.BODY, text=stripped))

        if bullet_buffer:
            results.append(BulletsElement(
                type=ElementType.BULLETS,
                items=bullet_buffer,
            ))

        return results

    # ── 알 수 없는 태그 → body 처리 ─────────────
    if text:
        return [TextElement(type=ElementType.BODY, text=text)]
    return []


# ─────────────────────────────────────────────
# 메인 파서
# ─────────────────────────────────────────────

def parse_md(
    md_path: str,
    image_dir: str = "",
) -> ParsedDocument:
    """
    구조화 마크다운 파일을 파싱하여 ParsedDocument 반환.

    Parameters
    ----------
    md_path   : .md 파일 경로
    image_dir : 이미지 파일이 있는 디렉터리 경로
                (비어있으면 .md 파일과 같은 디렉터리 사용)

    Returns
    -------
    ParsedDocument
    """
    md_path = Path(md_path).resolve()
    if not md_path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {md_path}")

    # 이미지 디렉터리 설정
    if not image_dir:
        image_dir = str(md_path.parent)
    image_dir = str(Path(image_dir).resolve()) + "/"

    raw = md_path.read_text(encoding="utf-8")

    # 1. 프론트매터 파싱
    meta, body = _parse_frontmatter(raw)

    # DocMeta 에 sub 속성이 없으면 동적으로 추가
    if not hasattr(meta, "sub"):
        meta.sub = ""  # type: ignore[attr-defined]

    # 2. 블록 토크나이징
    blocks = _tokenize(body)

    # 3. 블록 → dataclass
    elements: list[DocumentElement] = []
    for block in blocks:
        converted = _convert_block(block, meta, image_dir)
        elements.extend(converted)

    # 4. 빈 요소 제거
    elements = [e for e in elements if e is not None]

    return ParsedDocument(
        meta=meta,
        elements=elements,
        image_map={},          # .md 방식에서는 image_dir 직접 참조
        image_base_dir=image_dir,
    )


# ─────────────────────────────────────────────
# 단독 실행 테스트
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    from collections import Counter

    if len(sys.argv) < 2:
        print("사용법: python md_parser.py <path/to/file.md>")
        sys.exit(1)

    result = parse_md(sys.argv[1])

    print(f"\n{'─'*50}")
    print(f"제목:    {result.meta.title}")
    print(f"작성자:  {result.meta.author}")
    print(f"챕터:    {result.meta.chapter}")
    print(f"요소 수: {len(result.elements)}개")
    print(f"{'─'*50}")

    counter = Counter(
        e.type.value if hasattr(e.type, "value") else str(e.type)
        for e in result.elements
    )
    print("\n요소 타입 분포:")
    for t, cnt in sorted(counter.items()):
        print(f"  {t:25s}  {cnt}개")

    print("\n전체 요소 목록:")
    for i, el in enumerate(result.elements):
        t = el.type.value if hasattr(el.type, "value") else str(el.type)
        txt = ""
        if hasattr(el, "text"):
            txt = (el.text or "")[:50]
        elif hasattr(el, "question"):
            txt = el.question[:50]
        elif hasattr(el, "lines"):
            txt = str(el.lines)[:50]
        elif hasattr(el, "items"):
            txt = str(el.items)[:50]
        print(f"  {i+1:3d}  [{t:20s}]  {txt}")
