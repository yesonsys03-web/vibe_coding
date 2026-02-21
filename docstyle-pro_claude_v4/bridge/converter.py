"""
converter.py — DocStyle Pro Python → Node.js 변환 브릿지

입력 파일 종류에 따라 파서를 자동 분기한다.
    .md   → parser/md_parser.py   (방향 A — 구조화 마크다운, 권장)
    .docx → parser/docx_parser.py (방향 B — Word 파일, 서식 추론)
"""

from __future__ import annotations

import subprocess
import sys
import uuid
from pathlib import Path

from parser.md_parser   import parse_md
from parser.docx_parser import parse as parse_docx
from parser.image_extractor import cleanup_session
from .json_builder import build_json


# ─────────────────────────────────────────────
# 경로 상수
# ─────────────────────────────────────────────

_THIS_DIR    = Path(__file__).resolve().parent
_ENGINE_PATH = _THIS_DIR.parent / "engine" / "generate.js"
_TEMP_ROOT   = _THIS_DIR.parent / "temp"


# ─────────────────────────────────────────────
# node_modules 자동 설치
# ─────────────────────────────────────────────

def _ensure_node_modules() -> None:
    """
    engine/node_modules/docx 가 없으면 npm install 을 자동 실행한다.
    ZIP 압축 해제 직후 발생하는 MODULE_NOT_FOUND 오류를 방지한다.
    """
    engine_dir   = _ENGINE_PATH.parent
    node_modules = engine_dir / "node_modules" / "docx"

    if node_modules.exists():
        return

    import shutil
    npm_cmd = shutil.which("npm")
    if not npm_cmd:
        raise RuntimeError(
            "npm 을 찾을 수 없습니다.\n"
            "Node.js 18 이상을 설치한 후 다시 시도하세요.\n"
            "https://nodejs.org"
        )

    print("[DocStyle Pro] engine/node_modules 가 없습니다. npm install 실행 중...")
    result = subprocess.run(
        [npm_cmd, "install"],
        cwd=str(engine_dir),
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"npm install 실패:\n{result.stderr.strip()}\n\n"
            f"터미널에서 직접 실행해 주세요:\n"
            f"  cd {engine_dir}\n  npm install"
        )
    print("[DocStyle Pro] npm install 완료")


# ─────────────────────────────────────────────
# 변환 결과 모델
# ─────────────────────────────────────────────

class ConvertResult:
    def __init__(
        self,
        success: bool,
        output_path: str = "",
        error: str = "",
        element_count: int = 0,
        image_count: int = 0,
        template_id: str = "01",
        input_type: str = "",     # "md" | "docx"
    ):
        self.success       = success
        self.output_path   = output_path
        self.error         = error
        self.element_count = element_count
        self.image_count   = image_count
        self.template_id   = template_id
        self.input_type    = input_type

    def __repr__(self) -> str:
        if self.success:
            return (
                f"ConvertResult(success=True, output='{self.output_path}', "
                f"elements={self.element_count}, images={self.image_count}, "
                f"type={self.input_type})"
            )
        return f"ConvertResult(success=False, error='{self.error}')"


# ─────────────────────────────────────────────
# 메인 변환 함수
# ─────────────────────────────────────────────

def convert(
    input_path: str,
    output_path: str,
    template_id: str = "01",
    chapter_override: str = "",
    custom_settings: dict = None,
    keep_temp: bool = False,
    progress_callback=None,
) -> ConvertResult:
    """
    .md 또는 .docx → 서식 적용 .docx 전체 파이프라인.

    Parameters
    ----------
    input_path       : .md 또는 .docx 파일 경로
    output_path      : 결과 .docx 저장 경로
    template_id      : "01" ~ "10"
    chapter_override : 챕터명 직접 지정 (비어있으면 자동 추출)
    custom_settings  : 사용자 설정 (폰트, 크기, 간격 등) dict
    keep_temp        : True 면 임시 파일 삭제하지 않음 (디버그용)
    progress_callback: GUI 진행 상황 콜백 fn(pct: int, msg: str)
    """

    def _progress(pct: int, msg: str = ""):
        if progress_callback:
            progress_callback(pct, msg)

    temp_json_path = ""
    image_base_dir = ""
    suffix         = Path(input_path).suffix.lower()
    input_type     = "md" if suffix == ".md" else "docx"

    # ── Step 0: node_modules 자동 설치
    try:
        _progress(5, "Node.js 모듈 확인 중...")
        _ensure_node_modules()
    except RuntimeError as e:
        return ConvertResult(success=False, error=str(e), template_id=template_id)

    try:
        session_id = uuid.uuid4().hex[:8]
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)

        # ── Step 1: 파싱
        if input_type == "md":
            _progress(10, "마크다운 파싱 중...")
            parsed = parse_md(
                md_path=input_path,
                image_dir=str(Path(input_path).parent),
            )
            image_base_dir = parsed.image_base_dir
            _progress(40, f"파싱 완료 — 요소 {len(parsed.elements)}개")

        else:
            _progress(10, "Word 문서 파싱 중...")
            temp_img_dir = str(_TEMP_ROOT / "images")
            parsed = parse_docx(
                docx_path=input_path,
                temp_root=temp_img_dir,
                chapter_override=chapter_override,
            )
            image_base_dir = parsed.image_base_dir
            _progress(40, f"파싱 완료 — 요소 {len(parsed.elements)}개 / 이미지 {len(parsed.image_map)}개")

        # ── Step 2: JSON 직렬화
        _progress(50, "JSON 변환 중...")
        temp_json_path = str(_TEMP_ROOT / f"input_{session_id}.json")
        build_json(parsed, template_id=template_id, custom_settings=custom_settings, output_path=temp_json_path)

        # ── Step 3: Node.js 엔진 호출
        _progress(60, "레이아웃 적용 중...")

        node_cmd = _find_node()
        if not node_cmd:
            raise RuntimeError(
                "Node.js 를 찾을 수 없습니다.\n"
                "Node.js 18 이상을 설치한 후 다시 시도하세요."
            )

        proc = subprocess.run(
            [node_cmd, str(_ENGINE_PATH), temp_json_path,
             str(Path(output_path).resolve()), "--template", template_id],
            capture_output=True,
            text=True,
            cwd=str(_ENGINE_PATH.parent),
            timeout=120,
        )

        if proc.returncode != 0:
            raise RuntimeError(f"Node.js 엔진 오류:\n{proc.stderr.strip() or proc.stdout.strip()}")

        _progress(90, "임시 파일 생성 완료...")

        # ── Step 5: 임시 파일 정리
        if not keep_temp:
            _cleanup_temp(temp_json_path, image_base_dir if input_type == "docx" else "")

        _progress(100, "변환 완료")

        return ConvertResult(
            success=True,
            output_path=str(Path(output_path).resolve()),
            element_count=len(parsed.elements),
            image_count=len(parsed.image_map),
            template_id=template_id,
            input_type=input_type,
        )

    except Exception as e:
        if not keep_temp:
            _cleanup_temp(temp_json_path, image_base_dir if input_type == "docx" else "")
        return ConvertResult(
            success=False,
            error=str(e),
            template_id=template_id,
            input_type=input_type,
        )


# ─────────────────────────────────────────────
# 유틸리티
# ─────────────────────────────────────────────

def _find_node() -> str | None:
    import shutil
    for c in ["node", "node.exe", "nodejs"]:
        p = shutil.which(c)
        if p:
            return p
    return None


def _cleanup_temp(json_path: str, image_dir: str) -> None:
    import os
    if json_path and Path(json_path).exists():
        try:
            os.remove(json_path)
        except Exception:
            pass
    if image_dir:
        try:
            cleanup_session(image_dir)
        except Exception:
            pass


# ─────────────────────────────────────────────
# 단독 실행
# ─────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("사용법: python bridge/converter.py <input.md|.docx> <output.docx> [template_id]")
        sys.exit(1)

    in_path  = sys.argv[1]
    out_path = sys.argv[2]
    tmpl     = sys.argv[3] if len(sys.argv) > 3 else "01"

    result = convert(in_path, out_path, template_id=tmpl, keep_temp=True,
                     progress_callback=lambda p, m="": print(f"  [{p:3d}%] {m}"))

    if result.success:
        print(f"\n✅ 변환 완료: {result.output_path}")
        print(f"   입력 형식: {result.input_type} / 요소: {result.element_count}개")
    else:
        print(f"\n❌ 변환 실패: {result.error}")
        sys.exit(1)
