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

import json
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QVBoxLayout,
    QWidget,
    QSpinBox,
    QLineEdit,
    QLabel,
    QTabWidget,
)


class SettingsPanel(QGroupBox):
    _MAP_FILE_NAME = "template_auto_polish_levels.json"
    _DEFAULT_TEMPLATE_LEVEL_MAP = {
        "01": "strong",
        "02": "weak",
        "03": "normal",
        "04": "strong",
        "05": "normal",
        "06": "normal",
        "07": "strong",
        "08": "strong",
        "09": "normal",
        "10": "strong",
        "11": "weak",
        "12": "weak",
        "13": "normal",
        "14": "strong",
        "15": "weak",
        "16": "normal",
        "17": "normal",
        "18": "strong",
        "19": "strong",
        "20": "normal",
        "21": "normal",
        "22": "strong",
        "23": "strong",
        "24": "normal",
        "25": "normal",
        "26": "strong",
        "27": "weak",
        "28": "normal",
        "29": "weak",
        "30": "weak",
        "31": "weak",
        "32": "weak",
        "33": "weak",
        "34": "weak",
        "35": "normal",
        "36": "normal",
        "37": "strong",
        "38": "strong",
        "39": "weak",
        "40": "normal",
        "41": "normal",
        "42": "normal",
        "43": "normal",
        "44": "weak",
        "45": "normal",
        "46": "strong",
        "47": "strong",
        "48": "strong",
        "49": "strong",
        "50": "normal",
    }

    def __init__(self, parent=None):
        super().__init__("문서 설정 (Optional)", parent)
        self._template_recommended_level = "normal"
        self._template_level_map = self._load_template_level_map()
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
                color: #000000;
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
            "기본 (템플릿 종속)",
            "Pretendard",
            "Apple SD 산돌고딕 neo",
            "Inter",
            "맑은 고딕",
            "나눔고딕",
            "본고딕 (Noto Sans KR)",
            "본명조 (Noto Serif KR)",
            "KoPubWorld바탕체",
            "KoPubWorld돋움체",
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
        self.combo_line_spacing.addItems(
            [
                "기본 (템플릿 종속 1.6)",
                "1.0 (좁게)",
                "1.15 (옛날 방식)",
                "1.5 (조금 넓게)",
                "1.6 (추천: 모던)",
                "1.8 (조판 느낌)",
            ]
        )

        self.combo_margins = QComboBox()
        self.combo_margins.setFixedHeight(28)
        self.combo_margins.addItems(["기본", "좁게", "넓게"])

        self.combo_style_preset = QComboBox()
        self.combo_style_preset.setFixedHeight(28)
        self.combo_style_preset.addItems(
            [
                "템플릿 기반 (기본)",
                "클래식 문서",
                "모던 문서",
                "리포트 문서",
                "매거진 문서",
            ]
        )

        self.combo_auto_polish = QComboBox()
        self.combo_auto_polish.setFixedHeight(28)
        self.combo_auto_polish.addItems(
            [
                "템플릿 추천 (기본)",
                "클린 (약하게)",
                "밸런스 (기본)",
                "매거진 (강하게)",
                "끄기",
            ]
        )
        self.lbl_auto_polish_preview = QLabel("")
        self.lbl_auto_polish_preview.setWordWrap(True)
        self.lbl_auto_polish_preview.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_auto_polish_preview.setMinimumHeight(72)
        self.lbl_auto_polish_preview.setStyleSheet(
            "color: #111827; background: #FFFFFF; border: 1px solid #CBD5E1;"
            "border-radius: 6px; padding: 10px; font-size: 12px;"
        )

        self.chk_justify = QCheckBox("본문 양쪽 맞춤 적용")
        self.chk_justify.setChecked(False)

        layout2.addRow("제목 폰트:", self.combo_h_font)
        layout2.addRow("본문 폰트:", self.combo_b_font)
        layout2.addRow("기본 크기:", self.spin_base_size)
        layout2.addRow("줄 간격:", self.combo_line_spacing)
        layout2.addRow("페이지 여백:", self.combo_margins)
        layout2.addRow("문서 스타일셋:", self.combo_style_preset)
        layout2.addRow("자동 디자인 보정:", self.combo_auto_polish)
        layout2.addRow("보정 미리보기:", self.lbl_auto_polish_preview)
        layout2.addRow("", self.chk_justify)

        # Add tabs
        self.tabs.addTab(tab1, "📂 기본 정보")
        self.tabs.addTab(tab2, "🎨 디자인 상세")

        self.combo_auto_polish.currentIndexChanged.connect(
            self._update_auto_polish_preview
        )
        self._update_auto_polish_preview()

    def _resolve_effective_auto_polish_level(self) -> tuple[bool, str, str]:
        """
        Returns
        -------
        (enabled, level, mode_label)
        level: off|weak|normal|strong
        """
        mode = self.combo_auto_polish.currentText()
        if mode == "끄기":
            return False, "off", mode
        if mode == "클린 (약하게)":
            return True, "weak", mode
        if mode == "매거진 (강하게)":
            return True, "strong", mode
        if mode == "밸런스 (기본)":
            return True, "normal", mode
        return True, self._template_recommended_level, mode

    def _update_auto_polish_preview(self):
        enabled, level, mode = self._resolve_effective_auto_polish_level()
        if not enabled:
            self.lbl_auto_polish_preview.setText(
                "<b>현재 모드:</b> 보정 끔<br/>"
                "원문 구조를 그대로 유지하고 자동 레이아웃 개입을 하지 않습니다."
            )
            return

        title_map = {
            "weak": "클린",
            "normal": "밸런스",
            "strong": "매거진",
        }
        desc_map = {
            "weak": "긴 문단 위주로 최소 개입",
            "normal": "리드 문단/섹션 구분을 균형 적용",
            "strong": "시각적 구획과 리듬을 적극 강화",
        }
        behavior_map = {
            "weak": "문단 분할 기준 높음, 장식 요소 적게 사용",
            "normal": "문맥 기반으로 분할/강조를 자동 조절",
            "strong": "헤딩 전환 강조와 리드 문단 적용 빈도 증가",
        }

        if mode == "템플릿 추천 (기본)":
            level_name = title_map.get(level, "밸런스")
            self.lbl_auto_polish_preview.setText(
                f"<b>현재 모드:</b> 템플릿 추천 ({level_name})<br/>"
                f"- {desc_map.get(level, desc_map['normal'])}<br/>"
                f"- {behavior_map.get(level, behavior_map['normal'])}"
            )
        else:
            self.lbl_auto_polish_preview.setText(
                f"<b>현재 모드:</b> {title_map.get(level, '밸런스')}<br/>"
                f"- {desc_map.get(level, desc_map['normal'])}<br/>"
                f"- {behavior_map.get(level, behavior_map['normal'])}"
            )

    @classmethod
    def _load_template_level_map(cls) -> dict[str, str]:
        cfg_path = Path(__file__).resolve().parent / cls._MAP_FILE_NAME
        merged = dict(cls._DEFAULT_TEMPLATE_LEVEL_MAP)

        if not cfg_path.exists():
            return merged

        try:
            loaded = json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception:
            return merged

        if not isinstance(loaded, dict):
            return merged

        valid_levels = {"weak", "normal", "strong"}
        for key, value in loaded.items():
            tpl_id = str(key).strip()
            if tpl_id.isdigit():
                tpl_id = tpl_id.zfill(2)
            level = str(value).strip().lower()
            if tpl_id and level in valid_levels:
                merged[tpl_id] = level

        return merged

    def _recommend_level_from_template(self, template_info: dict) -> str:
        tpl_id = str(template_info.get("id") or "").strip()
        if tpl_id.isdigit():
            tpl_id = tpl_id.zfill(2)
        return self._template_level_map.get(tpl_id, "normal")

    def set_template_auto_polish_hint(self, template_info: dict):
        self._template_recommended_level = self._recommend_level_from_template(
            template_info
        )
        self._update_auto_polish_preview()

    def get_settings(self) -> dict:
        """
        사용자가 선택한 설정값을 dict 형태로 반환합니다.
        기본값이 선택된 항목은 빈 문자열로 처리하여 엔진에서 판단하게 합니다.
        """
        h_font = self.combo_h_font.currentText()
        if "기본" in h_font:
            h_font = ""

        b_font = self.combo_b_font.currentText()
        if "기본" in b_font:
            b_font = ""

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

        style_raw = self.combo_style_preset.currentText()
        style_preset = "template"
        if style_raw == "클래식 문서":
            style_preset = "classic"
        elif style_raw == "모던 문서":
            style_preset = "modern"
        elif style_raw == "리포트 문서":
            style_preset = "report"
        elif style_raw == "매거진 문서":
            style_preset = "magazine"

        auto_polish, auto_polish_level, _ = self._resolve_effective_auto_polish_level()

        return {
            "h_font": h_font,
            "b_font": b_font,
            "base_size": base_size,
            "line_spacing": line_spacing,
            "margins": margins,
            "style_preset": style_preset,
            "auto_polish": auto_polish,
            "auto_polish_level": auto_polish_level,
            "justify": self.chk_justify.isChecked(),
            "cover_title": self.edit_cover_title.text().strip(),
            "cover_subtitle": self.edit_cover_subtitle.text().strip(),
            "cover_author": self.edit_cover_author.text().strip(),
            "auto_toc": self.chk_auto_toc.isChecked(),
            "header_text": self.edit_header_text.text().strip(),
            "page_numbers": self.chk_page_numbers.isChecked(),
        }
