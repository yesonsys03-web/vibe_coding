"""
image_injector.py — Node.js 가 생성한 raw .docx 에 원본 이미지 재삽입

동작 방식:
1. raw docx(ZIP) 열기
2. word/media/ 에 원본 이미지 파일 삽입
3. word/_rels/document.xml.rels 에 관계(Relationship) 추가
4. [Content_Types].xml 에 이미지 확장자 등록
5. word/document.xml 에서 [IMG:image1] 마커를 실제 <w:drawing> 으로 교체
6. 새 .docx 로 저장
"""

from __future__ import annotations
import os
import re
import zipfile
import shutil
from pathlib import Path
from lxml import etree


# ── XML 네임스페이스 ──────────────────────────────────────
NSMAP = {
    "wpc":  "http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas",
    "cx":   "http://schemas.microsoft.com/office/drawing/2014/chartex",
    "mc":   "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "aink": "http://schemas.microsoft.com/office/drawing/2016/ink",
    "am3d": "http://schemas.microsoft.com/office/drawing/2017/model3d",
    "o":    "urn:schemas-microsoft-com:office:office",
    "oel":  "http://schemas.microsoft.com/office/2019/extlst",
    "r":    "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "m":    "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "v":    "urn:schemas-microsoft-com:vml",
    "wp14": "http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing",
    "wp":   "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "w10":  "urn:schemas-microsoft-com:office:word",
    "w":    "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "w14":  "http://schemas.microsoft.com/office/word/2010/wordml",
    "w15":  "http://schemas.microsoft.com/office/word/2012/wordml",
    "w16cex":"http://schemas.microsoft.com/office/word/2018/wordml/cex",
    "w16cid":"http://schemas.microsoft.com/office/word/2016/wordml/cid",
    "w16":  "http://schemas.microsoft.com/office/word/2018/wordml",
    "w16sdtdh":"http://schemas.microsoft.com/office/word/2020/wordml/sdtdatahash",
    "w16se":"http://schemas.microsoft.com/office/word/2015/wordml/symex",
    "wpg":  "http://schemas.microsoft.com/office/word/2010/wordprocessingGroup",
    "wpi":  "http://schemas.microsoft.com/office/word/2010/wordprocessingInk",
    "wne":  "http://schemas.microsoft.com/office/word/2006/wordml",
    "wps":  "http://schemas.microsoft.com/office/word/2010/wordprocessingShape",
    "a":    "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic":  "http://schemas.openxmlformats.org/drawingml/2006/picture",
}

RELATIONSHIP_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"

CONTENT_TYPES = {
    "png":  "image/png",
    "jpg":  "image/jpeg",
    "jpeg": "image/jpeg",
    "gif":  "image/gif",
    "bmp":  "image/bmp",
    "tiff": "image/tiff",
    "emf":  "image/x-emf",
    "wmf":  "image/x-wmf",
}

# 기본 이미지 크기 (EMU) — 원본 크기 정보 없을 때
DEFAULT_WIDTH_EMU  = 5_400_000   # ≈ 6cm
DEFAULT_HEIGHT_EMU = 3_600_000   # ≈ 4cm


def _drawing_xml(rel_id: str, width_emu: int, height_emu: int, img_id: int) -> str:
    """<w:drawing> XML 문자열 생성"""
    return f"""<w:drawing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
  xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
  xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
  xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <wp:inline distT="0" distB="0" distL="0" distR="0">
    <wp:extent cx="{width_emu}" cy="{height_emu}"/>
    <wp:effectExtent l="0" t="0" r="0" b="0"/>
    <wp:docPr id="{img_id}" name="Image{img_id}"/>
    <wp:cNvGraphicFramePr/>
    <a:graphic>
      <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
        <pic:pic>
          <pic:nvPicPr>
            <pic:cNvPr id="{img_id}" name="Image{img_id}"/>
            <pic:cNvPicPr><a:picLocks noChangeAspect="1"/></pic:cNvPicPr>
          </pic:nvPicPr>
          <pic:blipFill>
            <a:blip r:embed="{rel_id}"/>
            <a:stretch><a:fillRect/></a:stretch>
          </pic:blipFill>
          <pic:spPr>
            <a:xfrm><a:off x="0" y="0"/><a:ext cx="{width_emu}" cy="{height_emu}"/></a:xfrm>
            <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
          </pic:spPr>
        </pic:pic>
      </a:graphicData>
    </a:graphic>
  </wp:inline>
</w:drawing>"""


def inject_images(
    raw_docx:    str,
    images:      list[dict],
    output_path: str,
) -> str:
    """
    Args:
        raw_docx:     Node.js 가 생성한 임시 .docx 경로
        images:       image_extractor.extract_images() 반환값
        output_path:  최종 출력 경로

    Returns:
        output_path
    """
    if not images:
        shutil.copy2(raw_docx, output_path)
        return output_path

    # image_id → image dict 매핑
    id_map: dict[str, dict] = {img["id"]: img for img in images}

    # 임시 작업 경로
    tmp_dir  = Path(raw_docx).parent / "_inject_tmp"
    tmp_dir.mkdir(exist_ok=True)
    tmp_out  = tmp_dir / "output.docx"

    try:
        with zipfile.ZipFile(raw_docx, "r") as zin, \
             zipfile.ZipFile(str(tmp_out), "w", zipfile.ZIP_DEFLATED) as zout:

            existing = set(zin.namelist())
            added_rels:   dict[str, str] = {}   # image_id → rel_id
            added_exts:   set[str]       = set()
            img_counter   = 1000  # 기존 rId 와 충돌 방지

            # ── 1. 기존 파일 복사 ───────────────────────────────
            for item in zin.namelist():
                data = zin.read(item)

                if item == "word/document.xml":
                    # 나중에 교체
                    continue
                if item == "word/_rels/document.xml.rels":
                    # 관계 추가 후 저장
                    rels_xml = _add_relationships(data, images, id_map, added_rels, img_counter)
                    zout.writestr(item, rels_xml)
                    continue
                if item == "[Content_Types].xml":
                    # 확장자 등록 후 저장
                    ct_xml = _add_content_types(data, images, added_exts)
                    zout.writestr(item, ct_xml)
                    continue

                zout.writestr(item, data)

            # ── 2. 이미지 파일 삽입 ─────────────────────────────
            for img in images:
                media_path = f"word/media/{img['filename']}"
                if media_path not in existing and os.path.exists(img["path"]):
                    zout.write(img["path"], media_path)

            # ── 3. document.xml 마커 교체 ───────────────────────
            doc_xml = zin.read("word/document.xml").decode("utf-8")
            doc_xml = _replace_markers(doc_xml, id_map, added_rels)
            zout.writestr("word/document.xml", doc_xml.encode("utf-8"))

            # ── 4. _rels 없으면 생성 ────────────────────────────
            if "word/_rels/document.xml.rels" not in existing:
                rels_xml = _create_rels(images, added_rels)
                zout.writestr("word/_rels/document.xml.rels", rels_xml)

        # 최종 출력 경로로 이동
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(tmp_out), output_path)

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return output_path


# ── 내부 헬퍼 ─────────────────────────────────────────────

def _add_relationships(
    data: bytes,
    images: list[dict],
    id_map: dict,
    added_rels: dict,
    start_id: int,
) -> bytes:
    root = etree.fromstring(data)
    current_ids = {r.get("Id") for r in root}
    counter = start_id

    for img in images:
        rel_id = f"rIdI{counter}"
        while rel_id in current_ids:
            counter += 1
            rel_id = f"rIdI{counter}"

        added_rels[img["id"]] = rel_id
        current_ids.add(rel_id)

        rel_elem = etree.SubElement(root, "Relationship")
        rel_elem.set("Id", rel_id)
        rel_elem.set("Type", RELATIONSHIP_TYPE)
        rel_elem.set("Target", f"media/{img['filename']}")
        counter += 1

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _create_rels(images: list[dict], added_rels: dict) -> bytes:
    root = etree.Element("Relationships",
        xmlns="http://schemas.openxmlformats.org/package/2006/relationships")
    for img in images:
        rel = etree.SubElement(root, "Relationship")
        rel.set("Id", added_rels.get(img["id"], f"rId_{img['id']}"))
        rel.set("Type", RELATIONSHIP_TYPE)
        rel.set("Target", f"media/{img['filename']}")
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _add_content_types(data: bytes, images: list[dict], added_exts: set) -> bytes:
    root = etree.fromstring(data)
    existing_exts = {e.get("Extension") for e in root if e.get("Extension")}

    for img in images:
        ext = img.get("ext", "png").lower()
        if ext not in existing_exts and ext not in added_exts:
            ct = etree.SubElement(root, "Default")
            ct.set("Extension", ext)
            ct.set("ContentType", CONTENT_TYPES.get(ext, "application/octet-stream"))
            added_exts.add(ext)
            existing_exts.add(ext)

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _replace_markers(doc_xml: str, id_map: dict, added_rels: dict) -> str:
    """[IMG:imageN] 마커를 <w:drawing> XML 로 교체"""
    pattern = re.compile(r'\[IMG:(image\d+)\]')

    def replacer(m):
        img_id   = m.group(1)
        img      = id_map.get(img_id)
        rel_id   = added_rels.get(img_id, "")
        if not img or not rel_id:
            return m.group(0)   # 매핑 없으면 그대로

        w   = img.get("width_emu",  0) or DEFAULT_WIDTH_EMU
        h   = img.get("height_emu", 0) or DEFAULT_HEIGHT_EMU
        num = int(img_id.replace("image", ""))
        return _drawing_xml(rel_id, w, h, num)

    return pattern.sub(replacer, doc_xml)


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 4:
        print("Usage: python image_injector.py <raw.docx> <images.json> <output.docx>")
        sys.exit(1)
    with open(sys.argv[2], encoding="utf-8") as f:
        imgs = json.load(f)
    inject_images(sys.argv[1], imgs, sys.argv[3])
    print(f"[OK] → {sys.argv[3]}")
