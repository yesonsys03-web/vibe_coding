"""
converter.py — Python ↔ Node.js 변환 브릿지

전체 변환 파이프라인:
  1. docx_parser   → parsed.json
  2. image_extractor → temp/images/
  3. subprocess(node generator.js) → output_raw.docx
  4. image_injector → final output.docx
"""

from __future__ import annotations
import os
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

from .docx_parser      import parse_and_save
from .image_extractor  import extract_images
from .image_injector   import inject_images


# Node.js 엔진 경로 (converter.py 기준 상대 경로)
_HERE       = Path(__file__).parent.parent          # docstyle-pro/
ENGINE_JS   = str(_HERE / "engine" / "generator.js")
TEMP_DIR    = str(_HERE / "temp")


class ConversionError(Exception):
    pass


def convert(
    docx_path:   str,
    template_id: int,
    output_path: str,
    on_progress: callable | None = None,
) -> str:
    """
    Args:
        docx_path:   원본 .docx 경로
        template_id: 1~10
        output_path: 최종 출력 경로
        on_progress: (step: int, total: int, message: str) → None

    Returns:
        output_path
    """
    def _progress(step, total, msg):
        if on_progress:
            on_progress(step, total, msg)

    total_steps = 4

    # ── 임시 디렉터리 준비 ──────────────────────────────────
    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp_dir = Path(TEMP_DIR) / ts
    tmp_dir.mkdir(parents=True, exist_ok=True)

    json_path   = str(tmp_dir / "parsed.json")
    images_dir  = str(tmp_dir / "images")
    raw_docx    = str(tmp_dir / "output_raw.docx")
    images_json = str(tmp_dir / "images.json")

    try:
        # ── Step 1. 파싱 ──────────────────────────────────────
        _progress(1, total_steps, "문서 구조 분석 중…")
        parsed = parse_and_save(docx_path, json_path)

        # ── Step 2. 이미지 추출 ──────────────────────────────
        _progress(2, total_steps, "이미지 추출 중…")
        images = extract_images(docx_path, images_dir)
        with open(images_json, "w", encoding="utf-8") as f:
            json.dump(images, f, ensure_ascii=False, indent=2)

        # ── Step 3. Node.js 엔진 호출 ────────────────────────
        _progress(3, total_steps, f"템플릿 {template_id} 적용 중…")
        _run_node(json_path, template_id, raw_docx)

        # ── Step 4. 이미지 재삽입 ────────────────────────────
        _progress(4, total_steps, "이미지 삽입 중…")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        inject_images(raw_docx, images, output_path)

        _progress(4, total_steps, "완료!")
        return output_path

    except Exception as e:
        raise ConversionError(str(e)) from e

    finally:
        # 임시 파일 정리
        shutil.rmtree(str(tmp_dir), ignore_errors=True)


def _run_node(json_path: str, template_id: int, output_path: str) -> None:
    """Node.js generator.js 실행"""
    result = subprocess.run(
        ["node", ENGINE_JS, json_path, str(template_id), output_path],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise ConversionError(
            f"Node.js 엔진 오류:\n{result.stderr or result.stdout}"
        )


def get_template_info(template_id: int) -> dict:
    """템플릿 메타 정보 반환 (이름·색상)"""
    TEMPLATE_META = {
        1:  {"name": "Classic Editorial",  "accent": "#DC2626", "tag": "출판사 원고"},
        2:  {"name": "Minimal Zen",        "accent": "#18181B", "tag": "에세이·철학"},
        3:  {"name": "Nordic Blue",        "accent": "#0EA5E9", "tag": "비즈니스"},
        4:  {"name": "Luxury Gold",        "accent": "#D97706", "tag": "프리미엄"},
        5:  {"name": "Academic",           "accent": "#2563EB", "tag": "학술·논문"},
        6:  {"name": "Tech Modern",        "accent": "#8B5CF6", "tag": "IT·기술"},
        7:  {"name": "Warm Editorial",     "accent": "#EA580C", "tag": "라이프스타일"},
        8:  {"name": "Bold Magazine",      "accent": "#F43F5E", "tag": "매거진"},
        9:  {"name": "Forest Green",       "accent": "#10B981", "tag": "건강·자연"},
        10: {"name": "Royal Purple",       "accent": "#7C3AED", "tag": "인문·예술"},
    }
    return TEMPLATE_META.get(template_id, {})
