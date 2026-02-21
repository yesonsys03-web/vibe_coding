"""
image_extractor.py — 원본 .docx(ZIP) 에서 이미지 추출

word/media/ 에 있는 모든 이미지를 output_dir 로 복사하고
각 이미지의 EMU 크기(원본 치수) 정보를 함께 반환한다.
"""

from __future__ import annotations
import os
import zipfile
from pathlib import Path
from lxml import etree


# EMU 네임스페이스
WP_NS  = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS   = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS   = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PIC_NS = "http://schemas.openxmlformats.org/drawingml/2006/picture"


def extract_images(docx_path: str, output_dir: str) -> list[dict]:
    """
    Returns:
    [
      {
        "id":         "image1",
        "filename":   "image1.png",
        "path":       "temp/images/image1.png",
        "width_emu":  5400000,
        "height_emu": 3200000,
        "rel_id":     "rId5",        # document.xml.rels 관계 ID
        "ext":        "png",
      },
      ...
    ]
    """
    os.makedirs(output_dir, exist_ok=True)
    images: list[dict] = []

    with zipfile.ZipFile(docx_path, "r") as z:
        # ── 미디어 파일 복사 ─────────────────────────────────
        media_files = sorted(
            f for f in z.namelist()
            if f.startswith("word/media/")
            and not f.endswith("/")
        )

        for media_file in media_files:
            filename = Path(media_file).name
            ext      = Path(filename).suffix.lstrip(".")
            out_path = os.path.join(output_dir, filename)

            with z.open(media_file) as src, open(out_path, "wb") as dst:
                dst.write(src.read())

            images.append({
                "id":         "",          # document.xml 파싱 후 채움
                "filename":   filename,
                "path":       out_path,
                "width_emu":  0,
                "height_emu": 0,
                "rel_id":     "",
                "ext":        ext,
            })

        # ── EMU 크기 및 관계 ID 추출 ─────────────────────────
        if "word/document.xml" in z.namelist():
            with z.open("word/document.xml") as f:
                tree = etree.parse(f)
            _fill_sizes_and_ids(tree, images)

        # ── 관계 파일에서 rel_id ↔ filename 매핑 ──────────────
        rels_path = "word/_rels/document.xml.rels"
        if rels_path in z.namelist():
            with z.open(rels_path) as f:
                rels_tree = etree.parse(f)
            _fill_rel_ids(rels_tree, images)

    # image_id 부여
    for i, img in enumerate(images):
        img["id"] = f"image{i + 1}"

    return images


def _fill_sizes_and_ids(tree, images: list[dict]) -> None:
    """document.xml 에서 각 이미지 EMU 크기 추출"""
    ns  = {"wp": WP_NS}
    extents = tree.findall(".//wp:extent", ns)
    for i, img in enumerate(images):
        if i < len(extents):
            img["width_emu"]  = int(extents[i].get("cx", 0))
            img["height_emu"] = int(extents[i].get("cy", 0))


def _fill_rel_ids(rels_tree, images: list[dict]) -> None:
    """_rels/document.xml.rels 에서 rel_id 매핑"""
    root = rels_tree.getroot()
    # {filename: rel_id}
    filename_to_rel: dict[str, str] = {}
    for rel in root:
        target = rel.get("Target", "")
        rel_id = rel.get("Id", "")
        if "media/" in target:
            filename_to_rel[Path(target).name] = rel_id

    for img in images:
        img["rel_id"] = filename_to_rel.get(img["filename"], "")


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 3:
        print("Usage: python image_extractor.py <input.docx> <output_dir>")
        sys.exit(1)
    result = extract_images(sys.argv[1], sys.argv[2])
    print(json.dumps(result, ensure_ascii=False, indent=2))
