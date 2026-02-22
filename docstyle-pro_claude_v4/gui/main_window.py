"""
main_window.py — DocStyle Pro 메인 윈도우
레이아웃: 헤더 / 왼쪽(파일+변환) / 중앙(템플릿) / 오른쪽(결과) / 상태바
"""

import sys
import tempfile
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPushButton,
    QStatusBar, QVBoxLayout, QWidget, QScrollArea
)

if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from .file_drop_zone   import FileDropZone
from .preview_panel    import PreviewPanel
from .progress_dialog  import ProgressDialog
from .template_selector import TemplateSelector
from .settings_panel   import SettingsPanel
from .api_settings_dialog import ApiSettingsDialog
from .ai_organizer_dialog import AiOrganizerDialog

APP_VERSION = "1.0.0"


class AppHeader(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(64)
        self.setStyleSheet("background: #1E293B;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)

        bar = QWidget()
        bar.setFixedSize(4, 36)
        bar.setStyleSheet("background: #DC2626; border-radius: 2px;")

        title = QLabel("DocStyle Pro")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF;")

        subtitle = QLabel("워드 파일을 출판사급 레이아웃으로")
        subtitle.setFont(QFont("Arial", 9))
        subtitle.setStyleSheet("color: #94A3B8;")

        ver = QLabel(f"v{APP_VERSION}")
        ver.setFont(QFont("Arial", 8))
        ver.setStyleSheet("color: #3B82F6; background: #1E3A5F; padding: 2px 8px; border-radius: 10px;")

        col = QVBoxLayout()
        col.setSpacing(2)
        col.addWidget(title)
        col.addWidget(subtitle)

        layout.addWidget(bar)
        layout.addSpacing(10)
        layout.addLayout(col)
        layout.addStretch()
        layout.addWidget(ver)


class LeftPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: #FFFFFF;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        sec1 = QLabel("① 파일 선택")
        sec1.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        sec1.setStyleSheet("color: #374151;")

        # Beginner Feature: Template Gallery Button
        self.btn_new_doc = QPushButton("📄 새 문서 만들기 (마크다운 템플릿)")
        self.btn_new_doc.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_new_doc.setStyleSheet("""
            QPushButton {
                background: #F1F5F9;
                color: #3B82F6;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background: #E2E8F0; }
        """)

        self.drop_zone = FileDropZone()

        hint = QLabel("📌  .md 파일 권장 — 박스·Q&A·프롬프트 등\n모든 요소를 정확하게 표현합니다.\n.docx 파일도 지원하나 서식 추론에 한계가 있습니다.")
        hint.setFont(QFont("Arial", 8))
        hint.setStyleSheet("color: #64748B; background: #F8FAFC; border-radius: 6px; padding: 8px;")
        hint.setWordWrap(True)

        sec_ai = QLabel("② AI 원고 정리 (선택)")
        sec_ai.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        sec_ai.setStyleSheet("color: #374151;")

        ai_layout = QHBoxLayout()
        self.btn_ai_organize = QPushButton("✨ AI 원고 정리")
        self.btn_ai_organize.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ai_organize.setStyleSheet("""
            QPushButton {
                background: #8B5CF6;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background: #7C3AED; }
            QPushButton:disabled { background: #E5E7EB; color: #9CA3AF; }
        """)
        self.btn_ai_settings = QPushButton("⚙️ 설정")
        self.btn_ai_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ai_settings.setFixedWidth(60)
        self.btn_ai_settings.setStyleSheet("""
            QPushButton {
                background: #F1F5F9;
                color: #475569;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background: #E2E8F0; }
        """)
        ai_layout.addWidget(self.btn_ai_organize, 1)
        ai_layout.addWidget(self.btn_ai_settings)

        sec2 = QLabel("③ 변환 실행")
        sec2.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        sec2.setStyleSheet("color: #374151;")

        self.settings_panel = SettingsPanel()

        self.convert_btn = QPushButton("🚀  변환 시작")
        self.convert_btn.setFixedHeight(46)
        self.convert_btn.setEnabled(False)
        self.convert_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.convert_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self._apply_btn_style(False)

        layout.addWidget(sec1)
        layout.addWidget(self.btn_new_doc)
        layout.addWidget(self.drop_zone)
        layout.addWidget(hint)
        layout.addSpacing(4)
        
        layout.addWidget(sec_ai)
        layout.addLayout(ai_layout)
        layout.addSpacing(4)
        
        layout.addWidget(self.settings_panel)
        layout.addSpacing(4)
        layout.addWidget(sec2)
        layout.addWidget(self.convert_btn)
        layout.addStretch()

    def _apply_btn_style(self, enabled: bool):
        if enabled:
            self.convert_btn.setStyleSheet(
                "QPushButton { background: #DC2626; color: #FFFFFF; border: none; border-radius: 10px; font-size: 12px; font-weight: bold; }"
                "QPushButton:hover { background: #B91C1C; }"
                "QPushButton:pressed { background: #991B1B; }"
            )
        else:
            self.convert_btn.setStyleSheet(
                "QPushButton { background: #E2E8F0; color: #94A3B8; border: none; border-radius: 10px; font-size: 12px; }"
            )

    def set_file_ready(self, ready: bool):
        self.convert_btn.setEnabled(ready)
        self._apply_btn_style(ready)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._loaded_path = ""
        self._output_path = ""
        self._template_id = "01"

        self.setWindowTitle("DocStyle Pro")
        self.setMinimumSize(1100, 720)
        self.resize(1280, 780)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(AppHeader())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self._left   = LeftPanel()
        self._left_scroll = QScrollArea()
        self._left_scroll.setWidget(self._left)
        self._left_scroll.setWidgetResizable(True)
        self._left_scroll.setFixedWidth(290)
        self._left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._left_scroll.setStyleSheet("QScrollArea { border: none; border-right: 1px solid #E5E7EB; background: #FFFFFF; }")

        self._center = TemplateSelector()
        self._right  = PreviewPanel()
        self._right.setMinimumWidth(240)
        self._right.setMaximumWidth(320)
        self._right.setStyleSheet("background: #F8FAFC; border-left: 1px solid #E5E7EB;")

        body.addWidget(self._left_scroll)
        body.addWidget(self._center, 1)
        body.addWidget(self._right)
        root.addLayout(body, 1)

        self._status = QStatusBar()
        self._status.setStyleSheet("QStatusBar { background: #1E293B; color: #94A3B8; font-size: 9px; }")
        self._status.showMessage("준비됨  ·  파일을 로드하면 변환을 시작할 수 있습니다")
        self.setStatusBar(self._status)

    def _connect_signals(self):
        self._left.btn_new_doc.clicked.connect(self._on_new_doc_clicked)
        self._left.btn_ai_settings.clicked.connect(self._on_ai_settings_clicked)
        self._left.btn_ai_organize.clicked.connect(self._on_ai_organize_clicked)
        self._left.drop_zone.file_loaded.connect(self._on_file_loaded)
        self._left.drop_zone.file_error.connect(self._on_file_error)
        self._left.convert_btn.clicked.connect(self._on_convert_clicked)
        self._center.template_selected.connect(self._on_template_selected)

    def _on_ai_settings_clicked(self):
        dlg = ApiSettingsDialog(self)
        dlg.exec()

    def _on_ai_organize_clicked(self):
        dlg = AiOrganizerDialog(self)
        if dlg.exec():
            # User accepted the result, save it as a new .md file
            save_path, _ = QFileDialog.getSaveFileName(
                self, "정리된 원고 저장", str(Path.home() / "AI_정리_원고.md"), "Markdown files (*.md)"
            )
            if save_path:
                try:
                    with open(save_path, 'w', encoding='utf-8') as f:
                        f.write(dlg.final_md)
                    
                    import subprocess
                    subprocess.run(["open", save_path])
                    self._left.drop_zone._process_path(save_path)
                    self._status.showMessage(f"AI 정리 문서가 열렸습니다. 내용 추가 확인 후 변환을 누르세요. ({save_path})")
                except Exception as e:
                    QMessageBox.critical(self, "오류", f"파일 저장 중 오류가 발생했습니다.\n\n{e}")

    def _on_new_doc_clicked(self):
        templates = {
            "에세이 (감성적인 글쓰기)": "1_essay.md",
            "실용서 / 매뉴얼 (정보 전달)": "2_manual.md",
            "소설 (문학적 표현)": "3_novel.md"
        }
        item, ok = QInputDialog.getItem(
            self, "마크다운 템플릿 선택", 
            "원하시는 문서 형식을 선택해주세요:", 
            list(templates.keys()), 0, False
        )
        if ok and item:
            save_path, _ = QFileDialog.getSaveFileName(
                self, "새 문서 저장 위치", str(Path.home() / "새_문서.md"), "Markdown files (*.md)"
            )
            if save_path:
                import shutil, subprocess
                src_path = Path(__file__).parent.parent / "sample_docs" / templates[item]
                
                try:
                    shutil.copy2(src_path, save_path)
                    # Open file so user can edit it immediately
                    subprocess.run(["open", save_path])
                    
                    # Also load it to the dropzone visually and logically
                    self._left.drop_zone._process_path(save_path)
                    self._status.showMessage(f"새 문서가 열렸습니다. 내용 작성 후 저장하시고 변환을 누르세요. ({save_path})")
                except Exception as e:
                    QMessageBox.critical(self, "오류", f"템플릿을 복사하는 중 오류가 발생했습니다.\n\n{e}")

    def _on_file_loaded(self, path: str):
        self._loaded_path = path
        self._left.set_file_ready(True)
        self._right.reset()
        self._status.showMessage(f"파일 로드됨: {Path(path).name}  ·  템플릿을 선택하고 변환을 시작하세요")

    def _on_file_error(self, msg: str):
        self._loaded_path = ""
        self._left.set_file_ready(False)
        self._status.showMessage(f"파일 오류: {msg}")

    def _on_template_selected(self, tpl_id: str):
        self._template_id = tpl_id
        tpl = self._center.get_template_info(tpl_id)
        self._status.showMessage(f"선택된 템플릿: {tpl['name']}  ·  {tpl['tag']}")

    def _on_convert_clicked(self):
        if not self._loaded_path:
            QMessageBox.warning(self, "파일 없음", "먼저 .docx 파일을 로드하세요.")
            return

        # 1. 임시 경로에 먼저 저장
        session_id = str(Path(self._loaded_path).stem)
        temp_dir = Path(tempfile.gettempdir()) / "docstyle_pro"
        temp_dir.mkdir(parents=True, exist_ok=True)
        self._temp_output_path = str(temp_dir / f"{session_id}_t{self._template_id}.docx")

        tpl_name = self._center.get_template_info(self._template_id)["name"]
        settings = self._left.settings_panel.get_settings()
        
        dlg = ProgressDialog(
            input_path=self._loaded_path,
            output_path=self._temp_output_path,
            template_id=self._template_id,
            template_name=tpl_name,
            custom_settings=settings,
            parent=self,
        )
        dlg.convert_done.connect(self._on_convert_done)
        dlg.exec()

    def _on_convert_done(self, result):
        if result.success:
            import subprocess
            import shutil
            
            # 2. 결과물(DOCX)을 맥 기본 앱(Word, Pages 등)으로 바로 열기
            # macOS 권한 팝업 문제를 우회하기 위해 PDF 변환을 생략합니다.
            subprocess.run(["open", result.output_path])
                
            # 3. 사용자에게 저장 여부 확인
            reply = QMessageBox.question(
                self, '미리보기 확인', 
                "미리보기 창이 열렸습니다.\n이 디자인으로 문서를 저장하시겠습니까?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard,
                QMessageBox.StandardButton.Save
            )
            
            if reply == QMessageBox.StandardButton.Save:
                # 4. 저장 위치 묻기
                stem = Path(self._loaded_path).stem
                default_name = f"{stem}_styled_t{self._template_id}.docx"
                default_path = str(Path(self._loaded_path).parent / default_name)

                save_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "결과 파일 저장 위치",
                    default_path,
                    "Word 문서 (*.docx)",
                )
                if save_path:
                    # 임시 파일을 최종 위치로 복사
                    shutil.copy2(result.output_path, save_path)
                    
                    self._right.show_result(
                        output_path=save_path,
                        element_count=result.element_count,
                        image_count=result.image_count,
                        template_id=result.template_id,
                    )
                    self._left.drop_zone.set_loaded(self._loaded_path, result.image_count)
                    self._status.showMessage(
                        f"✅ 변환 및 저장 완료  ·  요소 {result.element_count}개  ·  "
                        f"이미지 {result.image_count}개  ·  {Path(save_path).name}"
                    )
                else:
                    self._status.showMessage("저장 취소됨")
            else:
                self._status.showMessage("문서 변경사항이 취소되었습니다.")
                
            # 임시 파일 삭제 (클린업)
            try:
                Path(result.output_path).unlink(missing_ok=True)
            except Exception:
                pass

        else:
            if "취소" not in result.error:
                QMessageBox.critical(self, "변환 실패",
                    f"오류:\n\n{result.error}\n\n원본 .docx 파일인지 확인하세요.")
            self._status.showMessage(f"변환 실패 또는 취소됨")
