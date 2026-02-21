"""
image_extractor.py — DocStyle Pro 이미지 추출기

.docx 는 ZIP 아카이브이므로 zipfile 로 word/media/ 내부 이미지를
직접 추출한다. 변환 세션마다 UUID 서브폴더에 격리 저장한다.

반환값
    image_map : dict[str, str]
        {"image1.png": "/abs/path/to/temp/images/{uuid}/image1.png"}
    image_base_dir : str
        "/abs/path/to/temp/images/{uuid}/"
"""

import shutil
import uuid
import zipfile
from pathlib import Path


# 지원 이미지 확장자
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff"}


def extract_images(docx_path: str, temp_root: str = "./temp/images") -> tuple[dict, str]:
    """
    docx 파일에서 이미지를 모두 추출한다.

    Parameters
    ----------
    docx_path : str
        원본 .docx 절대 경로
    temp_root : str
        이미지를 저장할 루트 디렉터리

    Returns
    -------
    image_map : dict[str, str]
        파일명 → 절대 경로 매핑
    image_base_dir : str
        이미지 저장 디렉터리 절대 경로 (trailing slash 포함)

    Raises
    ------
    FileNotFoundError
        docx_path 파일이 없을 때
    ValueError
        파일이 유효한 docx(ZIP) 형식이 아닐 때
    """
    docx_path = Path(docx_path).resolve()
    if not docx_path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {docx_path}")

    # 진짜 ZIP 형식인지 확인 (PK 매직 바이트)
    with open(docx_path, "rb") as f:
        magic = f.read(4)
    if magic[:2] != b"PK":
        raise ValueError(
            f"유효한 .docx 파일이 아닙니다 (ZIP 형식이 아님): {docx_path}\n"
            "플랫폼에서 변환된 마크다운 버전이 아닌 원본 .docx 파일을 사용하세요."
        )

    # 세션별 격리 디렉터리 생성
    session_id     = uuid.uuid4().hex[:8]
    output_dir     = Path(temp_root).resolve() / session_id
    output_dir.mkdir(parents=True, exist_ok=True)

    image_map: dict[str, str] = {}

    with zipfile.ZipFile(docx_path, "r") as zf:
        for entry in zf.namelist():
            entry_path = Path(entry)

            # word/media/ 하위 파일만 대상
            if not entry.startswith("word/media/"):
                continue

            ext = entry_path.suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue

            filename    = entry_path.name
            output_path = output_dir / filename

            with zf.open(entry) as src, open(output_path, "wb") as dst:
                shutil.copyfileobj(src, dst)

            image_map[filename] = str(output_path)

    image_base_dir = str(output_dir) + "/"
    return image_map, image_base_dir


def cleanup_session(image_base_dir: str) -> None:
    """
    변환 완료 후 임시 이미지 디렉터리를 삭제한다.
    bridge/converter.py 에서 변환 성공 후 호출.
    """
    target = Path(image_base_dir)
    if target.exists() and target.is_dir():
        shutil.rmtree(target)


# ─────────────────────────────────────────────
# 단독 실행 테스트
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("사용법: python image_extractor.py <path/to/file.docx>")
        sys.exit(1)

    try:
        img_map, base_dir = extract_images(sys.argv[1])
        print(f"추출된 이미지 수: {len(img_map)}개")
        print(f"저장 디렉터리: {base_dir}")
        for name, path in img_map.items():
            size = Path(path).stat().st_size
            print(f"  {name:30s}  {size:>8,} bytes")
    except (FileNotFoundError, ValueError) as e:
        print(f"오류: {e}")
        sys.exit(1)
