"""
docx_parser.py — DocStyle Pro 파싱 오케스트레이터 v2

변경 사항
    - classify_paragraph 에 prev_element 전달 (QA 답변 실시간 병합)
    - 후처리 파이프라인에 merge_conclusion_runs / absorb_prompt_labels 추가
    - DocMeta.sub 속성 동적 추가 제거 → models.py 에서 직접 선언
"""

from __future__ import annotations

import re
from pathlib import Path

import docx
import docx.table
import docx.text.paragraph
from docx.oxml.ns import qn

from .image_extractor import extract_images
from .models import (
    DocMeta,
    DocumentElement,
    ElementType,
    ImageElement,
    ParsedDocument,
    TextElement,
)
from .structure_analyzer import (
    absorb_captions,
    absorb_prompt_labels,
    classify_paragraph,
    classify_table,
    merge_bullet_runs,
    merge_conclusion_runs,
)


# ─────────────────────────────────────────────
# 관계 ID 매핑
# ─────────────────────────────────────────────

def _build_rel_map(doc_obj) -> dict[str, str]:
    rel_map: dict[str, str] = {}
    try:
        for rel in doc_obj.part.rels.values():
            if "image" in rel.reltype:
                rel_map[rel.rId] = Path(rel.target_ref).name
    except Exception:
        pass
    return rel_map


# ─────────────────────────────────────────────
# 메타 추출
# ─────────────────────────────────────────────

def _extract_meta(doc_obj) -> DocMeta:
    props = doc_obj.core_properties
    return DocMeta(
        title=props.title or "",
        author=props.author or "",
        chapter="",
    )


# ─────────────────────────────────────────────
# DS-ChapterTitle 에서 메타 보완
# ─────────────────────────────────────────────

def _enrich_meta_from_elements(meta: DocMeta, elements: list) -> None:
    """
    DS-ChapterTitle 단락의 텍스트를 메타에 반영.
    템플릿에서 '제목 | 챕터 | 부제' 형식으로 작성한 경우 파싱한다.
    """
    for el in elements:
        if isinstance(el, TextElement) and el.type == ElementType.CHAPTER_TITLE:
            # "제목 | [Phase N] | 부제" 형식 파싱
            parts = [p.strip() for p in el.text.split("|")]
            if len(parts) >= 1 and not meta.title:
                meta.title = parts[0]
            if len(parts) >= 2 and not meta.chapter:
                meta.chapter = parts[1]
            if len(parts) >= 3:
                el.sub = parts[2]   # type: ignore[attr-defined]
            elif not hasattr(el, "sub"):
                el.sub = ""         # type: ignore[attr-defined]
            break
    if not meta.chapter:
        for el in elements:
            if isinstance(el, TextElement) and el.type == ElementType.H1:
                meta.chapter = el.text
                break


# ─────────────────────────────────────────────
# 블록 순회
# ─────────────────────────────────────────────

def _iter_block_items(doc_obj):
    """Paragraph 와 Table 을 문서 순서대로 yield"""
    body = doc_obj.element.body
    for child in body:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == "p":
            yield docx.text.paragraph.Paragraph(child, doc_obj)
        elif tag == "tbl":
            yield docx.table.Table(child, doc_obj)


# ─────────────────────────────────────────────
# 메인 파서
# ─────────────────────────────────────────────

def parse(
    docx_path: str,
    temp_root: str = "./temp/images",
    chapter_override: str = "",
) -> ParsedDocument:
    """
    .docx 파일을 파싱하여 ParsedDocument 반환.

    DS-* 커스텀 스타일이 있으면 100% 정확하게 분류한다.
    DS-* 스타일이 없는 일반 Word 파일도 폰트 크기·들여쓰기로 최선 분류한다.
    """
    docx_path = str(Path(docx_path).resolve())

    # 1. 이미지 추출
    image_map, image_base_dir = extract_images(docx_path, temp_root)

    # 2. 문서 열기
    doc_obj = docx.Document(docx_path)

    # 3. 관계 ID 매핑
    rel_map = _build_rel_map(doc_obj)

    # 4. 메타 추출
    meta = _extract_meta(doc_obj)

    # 5. 블록 순회 — QA 답변은 실시간 병합
    raw_elements: list = []
    prev_element = None

    for block in _iter_block_items(doc_obj):
        if isinstance(block, docx.text.paragraph.Paragraph):
            el = classify_paragraph(block, image_map, rel_map, prev_element)
            if el is None:
                # QA 답변이 병합된 경우 — prev_element 는 유지
                continue
            raw_elements.append(el)
            prev_element = el

        elif isinstance(block, docx.table.Table):
            tbl_el = classify_table(block)
            raw_elements.append(tbl_el)
            prev_element = tbl_el

    # 6. 후처리 파이프라인
    result = raw_elements
    result = merge_bullet_runs(result)
    result = merge_conclusion_runs(result)
    result = absorb_captions(result)
    result = absorb_prompt_labels(result)

    # 7. 챕터명 보완
    if chapter_override:
        meta.chapter = chapter_override
    _enrich_meta_from_elements(meta, result)

    return ParsedDocument(
        meta=meta,
        elements=result,
        image_map=image_map,
        image_base_dir=image_base_dir,
    )


# ─────────────────────────────────────────────
# 단독 실행
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    from collections import Counter

    if len(sys.argv) < 2:
        print("사용법: python docx_parser.py <file.docx>")
        sys.exit(1)

    result = parse(sys.argv[1])
    print(f"\n제목:   {result.meta.title}")
    print(f"챕터:   {result.meta.chapter}")
    print(f"요소수: {len(result.elements)}개\n")

    counter = Counter(e.type.value for e in result.elements)
    print("요소 타입 분포:")
    for t, cnt in sorted(counter.items()):
        print(f"  {t:25s}  {cnt}개")
