"""
settings_panel.py — 사용자 맞춤 설정 패널 (좌측 패널 내 삽입)

기능
    - 제목 폰트, 본문 폰트
    - 기본 폰트 크기
    - 줄 간격
    - 여백
    - 양쪽 정렬
    의 옵션을 선택하고 딕셔너리 형태로 반환
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QFormLayout, QGroupBox,
    QVBoxLayout, QWidget, QSpinBox
)

class SettingsPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("문서 설정 (Optional)", parent)
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                margin-top: 10px;
                background: #F8FAFC;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #475569;
                font-weight: bold;
            }
            QLabel { color: #374151; font-size: 11px; }
            QComboBox, QSpinBox {
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                background: #FFFFFF;
                padding: 4px;
                font-size: 11px;
            }
        """)

        self._build_ui()

    def _build_ui(self):
        layout = QFormLayout(self)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(10)

        # 1. 폰트 선택
        self.combo_h_font = QComboBox()
        self.combo_b_font = QComboBox()

        fonts = [
            "기본 (템플릿 종속)", "Pretendard", "Apple SD 산돌고딕 neo", 
            "Inter", "맑은 고딕", "나눔고딕", "본고딕 (Noto Sans KR)", 
            "본명조 (Noto Serif KR)", "KoPubWorld바탕체", "KoPubWorld돋움체"
        ]
        self.combo_h_font.addItems(fonts)
        self.combo_b_font.addItems(fonts)

        # 2. 폰트 크기
        self.spin_base_size = QSpinBox()
        self.spin_base_size.setRange(8, 16)
        self.spin_base_size.setValue(10)
        self.spin_base_size.setSuffix(" pt")
        self.spin_base_size.setSpecialValueText("기본 (템플릿 종속)")
        self.spin_base_size.setValue(8) # If 8 it shows '기본'. We handle this in logic

        # 3. 줄 간격
        self.combo_line_spacing = QComboBox()
        self.combo_line_spacing.addItems(["기본 (템플릿 종속 1.6)", "1.0 (좁게)", "1.15 (옛날 방식)", "1.5 (조금 넓게)", "1.6 (추천: 모던)", "1.8 (조판 느낌)"])

        # 4. 여백
        self.combo_margins = QComboBox()
        self.combo_margins.addItems(["기본", "좁게", "넓게"])

        # 5. 양쪽 정렬
        self.chk_justify = QCheckBox("본문 양쪽 맞춤 적용")
        self.chk_justify.setChecked(False)

        # Add to Form
        layout.addRow("제목 폰트:", self.combo_h_font)
        layout.addRow("본문 폰트:", self.combo_b_font)
        layout.addRow("기본 크기:", self.spin_base_size)
        layout.addRow("줄 간격:", self.combo_line_spacing)
        layout.addRow("페이지 여백:", self.combo_margins)
        layout.addRow("", self.chk_justify)

    def get_settings(self) -> dict:
        """
        사용자가 선택한 설정값을 dict 형태로 반환합니다.
        기본값이 선택된 항목은 빈 문자열로 처리하여 엔진에서 판단하게 합니다.
        """
        h_font = self.combo_h_font.currentText()
        if "기본" in h_font: h_font = ""

        b_font = self.combo_b_font.currentText()
        if "기본" in b_font: b_font = ""

        size_val = self.spin_base_size.value()
        base_size = "" if size_val <= 8 else str(size_val)

        spacing_raw = self.combo_line_spacing.currentText()
        line_spacing = ""
        if "기본" not in spacing_raw:
            line_spacing = spacing_raw.split()[0]  # "1.15" 등 추출

        margin_raw = self.combo_margins.currentText()
        margins = ""
        if margin_raw == "좁게":
            margins = "narrow"
        elif margin_raw == "넓게":
            margins = "wide"
        else:
            margins = "default"

        return {
            "h_font": h_font,
            "b_font": b_font,
            "base_size": base_size,
            "line_spacing": line_spacing,
            "margins": margins,
            "justify": self.chk_justify.isChecked()
        }
