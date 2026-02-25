"""
file_drop_zone.py — DocStyle Pro 파일 로드 위젯

기능
    - .docx 파일 드래그 & 드롭
    - 클릭하여 파일 탐색기 열기
    - 로드 후 파일 정보 표시 (이름 · 크기 · 이미지 수)
    - 유효하지 않은 파일(마크다운으로 변환된 가짜 docx) 사전 차단

시그널
    file_loaded(str)  : 유효한 .docx 경로가 확정될 때 emit
"""

import os
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QDragEnterEvent, QDropEvent, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QFileDialog,
    QLabel,
    QVBoxLayout,
    QWidget,
)


# ─────────────────────────────────────────────
# 색상 상수
# ─────────────────────────────────────────────
COLOR_IDLE = "#E2E8F0"
COLOR_HOVER = "#93C5FD"
COLOR_ACCEPT = "#34D399"
COLOR_REJECT = "#F87171"
COLOR_BG_IDLE = "#F8FAFC"
COLOR_BG_HOVER = "#EFF6FF"
COLOR_TEXT_MAIN = "#1E293B"
COLOR_TEXT_SUB = "#64748B"
COLOR_ACCENT = "#DC2626"


def _is_valid_docx(path: str) -> tuple[bool, str]:
    """
    .md 또는 진짜 .docx(ZIP) 인지 검사.
    Returns (valid: bool, reason: str)
    """
    p = Path(path)
    if not p.exists():
        return False, "파일을 찾을 수 없습니다"

    ext = p.suffix.lower()

    # 구조화 마크다운 (권장)
    if ext == ".md":
        return True, ""

    # Word 파일
    if ext == ".docx":
        with open(p, "rb") as f:
            magic = f.read(2)
        if magic != b"PK":
            return False, (
                "유효한 Word 파일이 아닙니다.\n"
                "플랫폼에서 변환된 버전이 아닌 원본 .docx 파일을 사용하세요."
            )
        return True, ""

    return False, ".md 또는 .docx 파일만 지원합니다"


def _get_file_info(path: str, image_count: int) -> str:
    size = Path(path).stat().st_size
    if size >= 1024 * 1024:
        size_str = f"{size / 1024 / 1024:.1f} MB"
    else:
        size_str = f"{size / 1024:.0f} KB"
    img_str = f"  ·  이미지 {image_count}개" if image_count > 0 else "  ·  이미지 없음"
    return f"{size_str}{img_str}"


# ─────────────────────────────────────────────
# 드롭존 위젯
# ─────────────────────────────────────────────


class FileDropZone(QWidget):
    """
    .docx 파일을 받는 드래그&드롭 존.

    Signals
    -------
    file_loaded(str)  유효한 파일 경로
    file_error(str)   오류 메시지
    """

    file_loaded = pyqtSignal(str)
    file_error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hovered = False
        self._accepted = False
        self._rejected = False
        self._loaded_path = ""
        self._image_count = 0

        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(180)

        self._build_ui()

    # ── UI 구성 ──────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._icon_label = QLabel("📄", self)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setFont(QFont("Arial", 36))
        self._icon_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )

        self._main_label = QLabel("여기에 .docx 파일을 끌어다 놓으세요", self)
        self._main_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._main_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self._main_label.setStyleSheet(f"color: {COLOR_TEXT_MAIN};")
        self._main_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )

        self._sub_label = QLabel("또는 클릭하여 파일을 선택하세요", self)
        self._sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sub_label.setFont(QFont("Arial", 10))
        self._sub_label.setStyleSheet(f"color: {COLOR_TEXT_SUB};")
        self._sub_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )

        self._info_label = QLabel("", self)
        self._info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._info_label.setFont(QFont("Arial", 9))
        self._info_label.setStyleSheet(f"color: {COLOR_TEXT_SUB};")
        self._info_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )

        layout.addStretch()
        layout.addWidget(self._icon_label)
        layout.addSpacing(8)
        layout.addWidget(self._main_label)
        layout.addSpacing(4)
        layout.addWidget(self._sub_label)
        layout.addSpacing(6)
        layout.addWidget(self._info_label)
        layout.addStretch()

    # ── 상태 업데이트 ─────────────────────────

    def set_loaded(self, path: str, image_count: int = 0):
        """파일 로드 성공 상태로 전환"""
        self._loaded_path = path
        self._image_count = image_count
        self._accepted = True
        self._rejected = False
        self._hovered = False

        name = Path(path).name
        info = _get_file_info(path, image_count)

        self._icon_label.setText("✅")
        self._main_label.setText(name)
        self._main_label.setStyleSheet(f"color: {COLOR_TEXT_MAIN}; font-weight: bold;")
        self._sub_label.setText("다른 파일을 선택하려면 클릭하세요")
        self._info_label.setText(info)
        self.update()

    def set_error(self, message: str):
        """오류 상태로 전환"""
        self._accepted = False
        self._rejected = True
        self._hovered = False

        self._icon_label.setText("⚠️")
        self._main_label.setText("파일을 불러올 수 없습니다")
        self._main_label.setStyleSheet(f"color: {COLOR_REJECT}; font-weight: bold;")
        self._sub_label.setText(message)
        self._info_label.setText("")
        self.update()

    def reset(self):
        """초기 상태로 복원"""
        self._loaded_path = ""
        self._image_count = 0
        self._accepted = False
        self._rejected = False
        self._hovered = False

        self._icon_label.setText("📄")
        self._main_label.setText("여기에 .md 또는 .docx 파일을 끌어다 놓으세요")
        self._main_label.setStyleSheet(f"color: {COLOR_TEXT_MAIN};")
        self._sub_label.setText("또는 클릭하여 파일을 선택하세요")
        self._info_label.setText("")
        self.update()

    @property
    def loaded_path(self) -> str:
        return self._loaded_path

    # ── 페인팅 ───────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 배경
        if self._accepted:
            bg = "#F0FDF4"
        elif self._rejected:
            bg = "#FEF2F2"
        elif self._hovered:
            bg = COLOR_BG_HOVER
        else:
            bg = COLOR_BG_IDLE
        painter.fillRect(self.rect(), QColor(bg))

        # 테두리
        if self._accepted:
            border_color = COLOR_ACCEPT
            border_width = 2
        elif self._rejected:
            border_color = COLOR_REJECT
            border_width = 2
        elif self._hovered:
            border_color = COLOR_HOVER
            border_width = 2
        else:
            border_color = COLOR_IDLE
            border_width = 1

        pen = QPen(
            QColor(border_color),
            border_width,
            Qt.PenStyle.DashLine if not self._accepted else Qt.PenStyle.SolidLine,
        )
        painter.setPen(pen)
        r = self.rect().adjusted(2, 2, -2, -2)
        painter.drawRoundedRect(r, 12, 12)
        painter.end()

    # ── 이벤트 ───────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._open_file_dialog()

    def _open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Word 파일 선택",
            str(Path.home()),
            "지원 파일 (*.md *.docx);;마크다운 (*.md);;Word 문서 (*.docx)",
        )
        if path:
            self._process_path(path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].toLocalFile().lower().endswith((".docx", ".md")):
                event.acceptProposedAction()
                self._hovered = True
                self.update()
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self._hovered = False
        self.update()

    def dropEvent(self, event: QDropEvent):
        self._hovered = False
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            self._process_path(path)

    def _process_path(self, path: str):
        valid, reason = _is_valid_docx(path)
        if not valid:
            self.set_error(reason)
            self.file_error.emit(reason)
        else:
            # 이미지 수는 나중에 파싱 후 업데이트
            self.set_loaded(path, 0)
            self.file_loaded.emit(path)
