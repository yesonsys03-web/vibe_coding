"""
preview_panel.py — DocStyle Pro 결과 미리보기 패널

기능
    - 변환 완료 후 결과 정보 표시 (요소 수 · 이미지 수 · 파일 크기)
    - 선택된 템플릿의 색상 팔레트를 시각적으로 표시
    - 파일 저장 (다른 이름으로 저장) 버튼
    - 파일 탐색기에서 열기 버튼
    - 변환 전 상태에서는 안내 메시지 표시

Signals
    save_requested(str)   저장 버튼 클릭 시 현재 output_path emit
"""

import os
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

from .template_selector import TEMPLATES


# ─────────────────────────────────────────────
# 색상 팔레트 위젯
# ─────────────────────────────────────────────

class ColorPalette(QWidget):
    """템플릿 핵심 색상 5개를 가로로 표시"""

    def __init__(self, tpl: dict, parent=None):
        super().__init__(parent)
        self._colors = [
            tpl["header"],
            tpl["accent"],
            tpl["box_bg"],
            tpl["box_border"],
            "#FFFFFF",
        ]
        self.setFixedHeight(18)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W = self.width()
        H = self.height()
        sw = W // len(self._colors)
        
        # 전체 둥근 테두리 경로
        path = QPainterPath()
        path.addRoundedRect(0, 0, W, H, 6, 6)
        p.setClipPath(path)

        for i, color in enumerate(self._colors):
            x = i * sw
            w = sw if i < len(self._colors) - 1 else W - x
            p.fillRect(x, 0, w, H, QColor(color))
        
        # 연한 외곽선
        p.setClipping(False)
        p.setPen(QColor(0, 0, 0, 20))
        p.drawRoundedRect(0, 0, W - 1, H - 1, 6, 6)
        p.end()


# ─────────────────────────────────────────────
# 통계 카드
# ─────────────────────────────────────────────

def _stat_card(label: str, value: str, accent: str) -> QWidget:
    card = QFrame()
    card.setStyleSheet(f"""
        QFrame {{
            border: 1px solid {accent}20;
            border-radius: 12px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 {accent}05, stop:1 {accent}10);
        }}
    """)
    lay = QVBoxLayout(card)
    lay.setContentsMargins(10, 12, 10, 12)
    lay.setSpacing(4)

    val_lbl = QLabel(value)
    val_lbl.setFont(QFont("Arial", 16, QFont.Weight.Bold))
    val_lbl.setStyleSheet(f"color: {accent}; border: none; background: transparent;")
    val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

    key_lbl = QLabel(label)
    key_lbl.setFont(QFont("Arial", 8, QFont.Weight.Bold))
    key_lbl.setStyleSheet("color: #94A3B8; border: none; background: transparent; text-transform: uppercase;")
    key_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

    lay.addWidget(val_lbl)
    lay.addWidget(key_lbl)
    return card


# ─────────────────────────────────────────────
# 미리보기 패널
# ─────────────────────────────────────────────

class PreviewPanel(QWidget):
    """
    오른쪽 사이드 패널.
    변환 전: 안내 메시지
    변환 후: 결과 통계 + 열기 버튼
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._output_path = ""
        self._current_tpl = TEMPLATES[0]
        self._build_ui()
        self._show_idle()

    # ── UI 구성 ──────────────────────────────

    def _build_ui(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(12)
        self._layout.addStretch()

    def _clear_layout(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ── 상태별 화면 ──────────────────────────

    def _show_idle(self):
        """변환 전 안내 화면"""
        self._clear_layout()

        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setSpacing(16)

        icon = QLabel("🏗️")
        icon.setFont(QFont("Arial", 48))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("변환 준비 완료")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #475569;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        msg = QLabel("왼쪽 패널에서 파일을 드래그하고\n원하는 템플릿을 선택하세요.")
        msg.setFont(QFont("Arial", 9))
        msg.setStyleSheet("color: #94A3B8; line-height: 140%;")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setWordWrap(True)

        lay.addStretch()
        lay.addWidget(icon)
        lay.addWidget(title)
        lay.addWidget(msg)
        lay.addStretch()

        self._layout.addWidget(container)

    def _show_result(
        self,
        output_path: str,
        element_count: int,
        image_count: int,
        template_id: str,
    ):
        """변환 완료 화면"""
        self._clear_layout()
        self._output_path = output_path

        tpl_info = next((t for t in TEMPLATES if t["id"] == template_id), TEMPLATES[0])
        self._current_tpl = tpl_info
        accent = tpl_info["accent"]

        # ── 헤더 ─────────────────────────────
        done_lbl = QLabel("✅  변환 완료")
        done_lbl.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        done_lbl.setStyleSheet(f"color: {accent};")

        tpl_lbl = QLabel(f"{tpl_info['name']}  ·  {tpl_info['tag']}")
        tpl_lbl.setFont(QFont("Arial", 9))
        tpl_lbl.setStyleSheet("color: #64748B;")

        palette = ColorPalette(tpl_info)

        self._layout.addWidget(done_lbl)
        self._layout.addWidget(tpl_lbl)
        self._layout.addWidget(palette)
        self._layout.addSpacing(4)

        # ── 구분선 ───────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #E2E8F0;")
        self._layout.addWidget(sep)

        # ── 통계 카드 ─────────────────────────
        size_kb = Path(output_path).stat().st_size // 1024

        stat_row = QHBoxLayout()
        stat_row.setSpacing(8)
        stat_row.addWidget(_stat_card("요소", str(element_count), accent))
        stat_row.addWidget(_stat_card("이미지", str(image_count), "#10B981"))
        stat_row.addWidget(_stat_card("크기", f"{size_kb}KB", "#6B7280"))
        self._layout.addLayout(stat_row)

        # ── 파일 경로 ─────────────────────────
        fname_lbl = QLabel(Path(output_path).name)
        fname_lbl.setFont(QFont("Arial", 9))
        fname_lbl.setStyleSheet(
            "color: #374151; background: #F1F5F9; "
            "border-radius: 6px; padding: 6px 10px;"
        )
        fname_lbl.setWordWrap(True)
        self._layout.addWidget(fname_lbl)

        # ── 버튼 ─────────────────────────────
        self._open_btn = self._make_btn("📂  파일 위치 열기",    "#64748B", primary=False)

        self._open_btn.clicked.connect(self._on_open)

        self._layout.addWidget(self._open_btn)
        self._layout.addStretch()

    def _make_btn(self, text: str, color: str, primary: bool) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(38)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if primary:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color}; color: #FFFFFF;
                    border: none; border-radius: 8px;
                    font-size: 11px; font-weight: bold;
                }}
                QPushButton:hover {{ background: {color}CC; }}
                QPushButton:pressed {{ background: {color}99; }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: #F8FAFC; color: {color};
                    border: 1px solid #E2E8F0; border-radius: 8px;
                    font-size: 11px;
                }}
                QPushButton:hover {{ background: #F1F5F9; }}
                QPushButton:pressed {{ background: #E2E8F0; }}
            """)
        return btn

    # ── 슬롯 ─────────────────────────────────

    def _on_open(self):
        if not self._output_path:
            return
        folder = str(Path(self._output_path).parent)
        if sys.platform == "win32":
            os.startfile(folder)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])

    # ── 공개 메서드 ───────────────────────────

    def show_result(
        self,
        output_path: str,
        element_count: int,
        image_count: int,
        template_id: str,
    ):
        self._show_result(output_path, element_count, image_count, template_id)

    def reset(self):
        self._output_path = ""
        self._show_idle()
