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
    QVBoxLayout, QWidget, QSpinBox, QLineEdit, QLabel, QTabWidget
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
            QComboBox, QSpinBox, QLineEdit {
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                background: #FFFFFF;
                padding: 4px 6px;
                font-size: 12px;
            }
        """)

        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 16, 8, 8)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                background: #E2E8F0;
                color: #64748B;
                padding: 8px 12px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                border: 1px solid #CBD5E1;
                border-bottom: none;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #FFFFFF;
                color: #0F172A;
                border: 1px solid #CBD5E1;
                border-bottom: 1px solid #FFFFFF;
            }
            QTabWidget::pane {
                border: 1px solid #CBD5E1;
                background: #FFFFFF;
                border-radius: 4px;
                border-top-left-radius: 0;
            }
        """)
        main_layout.addWidget(self.tabs)

        # --- Tab 1: 기본 정보 ---
        tab1 = QWidget()
        layout1 = QFormLayout(tab1)
        layout1.setContentsMargins(12, 16, 12, 16)
        layout1.setSpacing(14)

        self.edit_cover_title = QLineEdit()
        self.edit_cover_title.setFixedHeight(28)
        self.edit_cover_title.setPlaceholderText("책 제목을 입력하세요")
        self.edit_cover_subtitle = QLineEdit()
        self.edit_cover_subtitle.setFixedHeight(28)
        self.edit_cover_subtitle.setPlaceholderText("부제목 (선택사항)")
        self.edit_cover_author = QLineEdit()
        self.edit_cover_author.setFixedHeight(28)
        self.edit_cover_author.setPlaceholderText("저자명 (선택사항)")
        
        self.chk_auto_toc = QCheckBox("자동 목차 생성 (표지 다음 장)")
        self.chk_auto_toc.setChecked(True)

        self.edit_header_text = QLineEdit()
        self.edit_header_text.setFixedHeight(28)
        self.edit_header_text.setPlaceholderText("머리글에 표시할 텍스트 (선택사항)")
        
        self.chk_page_numbers = QCheckBox("바닥글에 쪽 번호 추가")
        self.chk_page_numbers.setChecked(True)

        layout1.addRow("책 제목:", self.edit_cover_title)
        layout1.addRow("부제목:", self.edit_cover_subtitle)
        layout1.addRow("저자명:", self.edit_cover_author)
        layout1.addRow("", self.chk_auto_toc)
        layout1.addRow(QLabel("<b>[머리글 & 바닥글]</b>"))
        layout1.addRow("머리글:", self.edit_header_text)
        layout1.addRow("", self.chk_page_numbers)

        # --- Tab 2: 디자인 상세 ---
        tab2 = QWidget()
        layout2 = QFormLayout(tab2)
        layout2.setContentsMargins(12, 16, 12, 16)
        layout2.setSpacing(14)

        self.combo_h_font = QComboBox()
        self.combo_h_font.setFixedHeight(28)
        self.combo_b_font = QComboBox()
        self.combo_b_font.setFixedHeight(28)
        fonts = [
            "기본 (템플릿 종속)", "Pretendard", "Apple SD 산돌고딕 neo", 
            "Inter", "맑은 고딕", "나눔고딕", "본고딕 (Noto Sans KR)", 
            "본명조 (Noto Serif KR)", "KoPubWorld바탕체", "KoPubWorld돋움체"
        ]
        self.combo_h_font.addItems(fonts)
        self.combo_b_font.addItems(fonts)

        self.spin_base_size = QSpinBox()
        self.spin_base_size.setFixedHeight(28)
        self.spin_base_size.setRange(8, 16)
        self.spin_base_size.setValue(10)
        self.spin_base_size.setSuffix(" pt")
        self.spin_base_size.setSpecialValueText("기본 (템플릿 종속)")
        self.spin_base_size.setValue(8)

        self.combo_line_spacing = QComboBox()
        self.combo_line_spacing.setFixedHeight(28)
        self.combo_line_spacing.addItems(["기본 (템플릿 종속 1.6)", "1.0 (좁게)", "1.15 (옛날 방식)", "1.5 (조금 넓게)", "1.6 (추천: 모던)", "1.8 (조판 느낌)"])

        self.combo_margins = QComboBox()
        self.combo_margins.setFixedHeight(28)
        self.combo_margins.addItems(["기본", "좁게", "넓게"])

        self.chk_justify = QCheckBox("본문 양쪽 맞춤 적용")
        self.chk_justify.setChecked(False)

        layout2.addRow("제목 폰트:", self.combo_h_font)
        layout2.addRow("본문 폰트:", self.combo_b_font)
        layout2.addRow("기본 크기:", self.spin_base_size)
        layout2.addRow("줄 간격:", self.combo_line_spacing)
        layout2.addRow("페이지 여백:", self.combo_margins)
        layout2.addRow("", self.chk_justify)

        # Add tabs
        self.tabs.addTab(tab1, "📂 기본 정보")
        self.tabs.addTab(tab2, "🎨 디자인 상세")

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
            "justify": self.chk_justify.isChecked(),
            "cover_title": self.edit_cover_title.text().strip(),
            "cover_subtitle": self.edit_cover_subtitle.text().strip(),
            "cover_author": self.edit_cover_author.text().strip(),
            "auto_toc": self.chk_auto_toc.isChecked(),
            "header_text": self.edit_header_text.text().strip(),
            "page_numbers": self.chk_page_numbers.isChecked(),
        }
