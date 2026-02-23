"""
main_window.py — DocStyle Pro 메인 윈도우
레이아웃: 헤더 / 왼쪽(파일+변환) / 중앙(템플릿) / 오른쪽(결과) / 상태바
"""

import sys
import tempfile
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QAction
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFileDialog, QMessageBox, QStatusBar, QScrollArea,
    QTabWidget, QTextEdit, QInputDialog, QMenu, QSplitter, QTextBrowser
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
from .vault_explorer import VaultExplorer
from .insight_panel import InsightPanel
from bridge.ai_organizer import generate_draft, inline_edit, generate_toc
from bridge.vault_indexer import index_document
import markdown

APP_VERSION = "1.0.0"

class AiDraftThread(QThread):
    finished = pyqtSignal(str, bool)

    def __init__(self, title: str, subtitle: str, header: str, toc: str = ""):
        super().__init__()
        self.title_text = title
        self.subtitle_text = subtitle
        self.header_text = header
        self.toc_text = toc

    def run(self):
        try:
            result = generate_draft(self.title_text, self.subtitle_text, self.header_text, self.toc_text)
            self.finished.emit(result, True)
        except Exception as e:
            self.finished.emit(str(e), False)


class AiTocThread(QThread):
    finished = pyqtSignal(str, bool)

    def __init__(self, title: str, subtitle: str, header: str):
        super().__init__()
        self.title_text = title
        self.subtitle_text = subtitle
        self.header_text = header

    def run(self):
        try:
            result = generate_toc(self.title_text, self.subtitle_text, self.header_text)
            self.finished.emit(result, True)
        except Exception as e:
            self.finished.emit(str(e), False)


class AiInlineThread(QThread):
    finished = pyqtSignal(str, bool)

    def __init__(self, text: str, mode: str):
        super().__init__()
        self.raw_text = text
        self.mode = mode

    def run(self):
        try:
            result = inline_edit(self.raw_text, self.mode)
            self.finished.emit(result, True)
        except Exception as e:
            self.finished.emit(str(e), False)


class VaultIndexerThread(QThread):
    def __init__(self, file_path: str = None):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            if self.file_path:
                index_document(self.file_path)
                print(f"Vault index updated for: {self.file_path}")
            else:
                from bridge.vault_indexer import sync_entire_vault
                sync_entire_vault()
                print("Vault full sync complete.")
        except Exception as e:
            print(f"Vault indexer error: {e}")


class AiEditorWidget(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = None

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        
        cursor = self.textCursor()
        if cursor.hasSelection():
            ai_menu = QMenu("✨ AI 글쓰기 보조", self)
            
            action_polish = ai_menu.addAction("✨ 문장 다듬기 (Polish)")
            action_expand = ai_menu.addAction("📝 살 붙이기 (Expand)")
            action_summary = ai_menu.addAction("✂️ 핵심 요약 (Summarize)")
            
            action_polish.triggered.connect(lambda: self._run_ai("polish"))
            action_expand.triggered.connect(lambda: self._run_ai("expand"))
            action_summary.triggered.connect(lambda: self._run_ai("summarize"))
            
            menu.insertSeparator(menu.actions()[0])
            menu.insertMenu(menu.actions()[0], ai_menu)
            
        menu.exec(event.globalPos())

    def _run_ai(self, mode: str):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
            
        selected_text = cursor.selectedText()
        
        # Disable interaction temporarily
        self.setReadOnly(True)
        cursor.insertText("\n⏳ (AI 처리 중...)\n")
        
        self._thread = AiInlineThread(selected_text, mode)
        self._thread.finished.connect(lambda res, success, cur=self.textCursor(), old_txt=selected_text: self._on_ai_done(res, success, cur, old_txt))
        self._thread.start()

    def _on_ai_done(self, result: str, is_success: bool, cursor, old_text: str):
        self.setReadOnly(False)
        
        # Re-select the "AI 처리 중" text we inserted 
        cursor.movePosition(cursor.MoveOperation.Up, cursor.MoveMode.MoveAnchor, 2)
        cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, 2)
        
        if is_success:
            cursor.insertText(result)
        else:
            QMessageBox.critical(self.window(), "AI 오류", f"처리 중 오류가 발생했습니다: {result}")
            cursor.insertText(old_text)
            
        self.setFocus()


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

        sec1 = QLabel("① 원고 준비")
        sec1.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        sec1.setStyleSheet("color: #374151;")

        self.doc_tabs = QTabWidget()
        self.doc_tabs.setStyleSheet("""
            QTabBar::tab {
                background: #F1F5F9;
                color: #64748B;
                padding: 8px 12px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                border: 1px solid #E2E8F0;
                border-bottom: none;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background: #FFFFFF;
                color: #0F172A;
                border: 1px solid #E2E8F0;
                border-bottom: 2px solid #FFFFFF;
            }
            QTabWidget::pane {
                border: 1px solid #E2E8F0;
                background: #FFFFFF;
                border-radius: 6px;
                border-top-left-radius: 0;
            }
        """)

        # --- Tab 1: 파일 로드 ---
        tab1_widget = QWidget()
        tab1_layout = QVBoxLayout(tab1_widget)
        tab1_layout.setContentsMargins(12, 16, 12, 16)
        tab1_layout.setSpacing(12)

        # Beginner Feature: Template Gallery Button
        self.btn_new_doc = QPushButton("📄 새 문서 만들기 (마크다운 템플릿)")
        self.btn_new_doc.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_new_doc.setStyleSheet("""
            QPushButton {
                background: #EFF6FF;
                color: #2563EB;
                border: 1px solid #BFDBFE;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background: #DBEAFE; }
        """)

        self.drop_zone = FileDropZone()

        hint = QLabel("📌 .md 파일 권장 — 박스·Q&A 등 서식을 완벽하게 지원합니다. (.docx 파일도 가능)")
        hint.setFont(QFont("Arial", 11))
        hint.setStyleSheet("color: #64748B; background: #F8FAFC; border-radius: 6px; padding: 10px;")
        hint.setWordWrap(True)

        tab1_layout.addWidget(self.btn_new_doc)
        tab1_layout.addWidget(self.drop_zone)
        tab1_layout.addWidget(hint)

        # --- Tab 2: 에디터 ---
        tab2_widget = QWidget()
        tab2_layout = QVBoxLayout(tab2_widget)
        tab2_layout.setContentsMargins(2, 2, 2, 2)
        
        ai_draft_layout = QHBoxLayout()
        ai_draft_layout.setSpacing(4)
        
        btn_ai_style = """
            QPushButton {
                background: #F8FAFC;
                color: #8B5CF6;
                border: 1px solid #E2E8F0;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background: #F1F5F9; border-color: #CBD5E1; color: #7C3AED; }
            QPushButton:disabled { background: #E5E7EB; color: #9CA3AF; }
        """
        
        self.btn_ai_toc = QPushButton("📑 AI 목차 기획")
        self.btn_ai_toc.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ai_toc.setStyleSheet(btn_ai_style)
        
        self.btn_ai_draft = QPushButton("✨ AI 본문 초안 자동 생성")
        self.btn_ai_draft.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ai_draft.setStyleSheet(btn_ai_style)
        
        ai_draft_layout.addWidget(self.btn_ai_toc)
        ai_draft_layout.addWidget(self.btn_ai_draft)
        
        tab2_layout.addLayout(ai_draft_layout)

        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(4)
        
        btn_style = """
            QPushButton {
                background: #FFFFFF;
                color: #475569;
                border: 1px solid #E2E8F0;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QPushButton:hover { background: #F8FAFC; border-color: #CBD5E1; color: #0F172A; }
        """
        
        self.btn_md_h1 = QPushButton("H1")
        self.btn_md_h1.setStyleSheet(btn_style)
        self.btn_md_h1.setToolTip("제목 1")
        
        self.btn_md_h2 = QPushButton("H2")
        self.btn_md_h2.setStyleSheet(btn_style)
        self.btn_md_h2.setToolTip("제목 2")
        
        self.btn_md_bold = QPushButton("B")
        self.btn_md_bold.setStyleSheet(btn_style + "QPushButton { font-weight: bold; }")
        self.btn_md_bold.setToolTip("굵게")
        
        self.btn_md_quote = QPushButton("❝")
        self.btn_md_quote.setStyleSheet(btn_style)
        self.btn_md_quote.setToolTip("인용구")
        
        self.btn_md_tip = QPushButton("💡 팁")
        self.btn_md_tip.setStyleSheet(btn_style)
        
        self.btn_md_warn = QPushButton("⚠️ 경고")
        self.btn_md_warn.setStyleSheet(btn_style)
        
        toolbar_layout.addWidget(self.btn_md_h1)
        toolbar_layout.addWidget(self.btn_md_h2)
        toolbar_layout.addWidget(self.btn_md_bold)
        toolbar_layout.addWidget(self.btn_md_quote)
        toolbar_layout.addWidget(self.btn_md_tip)
        toolbar_layout.addWidget(self.btn_md_warn)
        toolbar_layout.addStretch()
        
        tab2_layout.addLayout(toolbar_layout)

        # QSplitter to hold Editor (Left) and Live Preview (Right)
        self.editor_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.editor_splitter.setHandleWidth(1)
        self.editor_splitter.setStyleSheet("QSplitter::handle { background: #E2E8F0; }")

        # Left side: Editor
        editor_wrapper = QWidget()
        editor_vbox = QVBoxLayout(editor_wrapper)
        editor_vbox.setContentsMargins(0, 0, 0, 0)
        
        self.text_editor = AiEditorWidget()
        self.text_editor.setPlaceholderText("여기에 노션처럼 자유롭게 글을 작성해보세요...\n\n# 제목 1\n## 제목 2\n\n- 리스트 항목\n> [Tip] 기억해둘 만한 팁")
        self.text_editor.setMinimumHeight(400)
        self.text_editor.setStyleSheet("""
            QTextEdit {
                border: none;
                background: #FFFFFF;
                color: #374151;
                font-family: 'Pretendard', 'Apple SD Gothic Neo', 'Inter', sans-serif;
                font-size: 14px;
                padding: 12px;
            }
        """)
        editor_vbox.addWidget(self.text_editor)
        
        # Right side: Live Preview
        self.text_preview = QTextBrowser()
        self.text_preview.setOpenExternalLinks(True)
        self.text_preview.setStyleSheet("""
            QTextBrowser {
                border: none;
                background: #F8FAFC;
                padding: 12px;
            }
        """)

        self.editor_splitter.addWidget(editor_wrapper)
        self.editor_splitter.addWidget(self.text_preview)
        self.editor_splitter.setSizes([500, 500]) # Even split initially
        
        tab2_layout.addWidget(self.editor_splitter)

        self.doc_tabs.addTab(tab1_widget, "📁 파일 로드")
        self.doc_tabs.addTab(tab2_widget, "📝 직접 작성")
        
        self.insight_panel = InsightPanel()
        self.doc_tabs.addTab(self.insight_panel, "💡 인사이트 랩")

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
        layout.addWidget(self.doc_tabs)
        layout.addSpacing(4)
        
        layout.addWidget(sec_ai)
        layout.addLayout(ai_layout)
        layout.addSpacing(4)
        
        layout.addWidget(self.settings_panel)
        layout.addSpacing(4)
        layout.addWidget(sec2)
        layout.addWidget(self.convert_btn)
        layout.addStretch()

        self.text_editor.textChanged.connect(self._evaluate_ready_state)
        self.doc_tabs.currentChanged.connect(self._evaluate_ready_state)

    def _apply_btn_style(self, enabled: bool):
        self.convert_btn.setEnabled(enabled)
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

    def set_file_ready(self, _):
        # We ignore the boolean passed from dropzone and evaluate dynamically
        self._evaluate_ready_state()

    def _evaluate_ready_state(self):
        idx = self.doc_tabs.currentIndex()
        if idx == 0:
            is_ready = bool(self.drop_zone.loaded_path)
        else:
            is_ready = bool(self.text_editor.toPlainText().strip())
        self._apply_btn_style(is_ready)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._loaded_path = ""
        self._output_path = ""
        self._template_id = "01"
        self._active_vault_file = None

        self.setWindowTitle("DocStyle Pro")
        self.setMinimumSize(1100, 720)
        self.resize(1280, 780)
        self._build_ui()
        self._connect_signals()
        
        # Trigger full vault sync on startup
        self._full_sync_thread = VaultIndexerThread(None)
        self._full_sync_thread.start()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(AppHeader())

        # Main horizontal splitter for the three core panels
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setHandleWidth(1)
        self.main_splitter.setStyleSheet("QSplitter::handle { background: #E5E7EB; }")

        self._left   = LeftPanel()
        self._left_scroll = QScrollArea()
        self._left_scroll.setWidget(self._left)
        self._left_scroll.setWidgetResizable(True)
        # Removed fixed width so it can be resized
        self._left_scroll.setMinimumWidth(320)
        self._left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._left_scroll.setStyleSheet("QScrollArea { border: none; border-right: 1px solid #E5E7EB; background: #FFFFFF; }")

        self._center = TemplateSelector()
        self._right  = PreviewPanel()
        self._right.setMinimumWidth(240)
        self._right.setMaximumWidth(320)
        self._right.setStyleSheet("background: #F8FAFC; border-left: 1px solid #E5E7EB;")
        
        self._vault_explorer = VaultExplorer()

        self.main_splitter.addWidget(self._vault_explorer)
        self.main_splitter.addWidget(self._left_scroll)
        self.main_splitter.addWidget(self._center)
        self.main_splitter.addWidget(self._right)
        
        # Set initial ratio: Vault, Left (editor), Center (templates), Right (preview)
        self.main_splitter.setSizes([220, 500, 400, 260])
        
        root.addWidget(self.main_splitter, 1)

        self._status = QStatusBar()
        self._status.setStyleSheet("QStatusBar { background: #1E293B; color: #94A3B8; font-size: 9px; }")
        self._status.showMessage("준비됨  ·  파일을 로드하면 변환을 시작할 수 있습니다")
        self.setStatusBar(self._status)

    def _connect_signals(self):
        self._left.btn_new_doc.clicked.connect(self._on_new_doc_clicked)
        self._left.btn_ai_settings.clicked.connect(self._on_ai_settings_clicked)
        self._left.btn_ai_organize.clicked.connect(self._on_ai_organize_clicked)
        self._left.btn_ai_draft.clicked.connect(self._on_ai_draft_clicked)
        self._left.btn_ai_toc.clicked.connect(self._on_ai_toc_clicked)
        self._left.drop_zone.file_loaded.connect(self._on_file_loaded)
        self._left.drop_zone.file_error.connect(self._on_file_error)
        self._left.convert_btn.clicked.connect(self._on_convert_clicked)
        self._center.template_selected.connect(self._on_template_selected)
        
        self._left.text_editor.textChanged.connect(self._update_live_preview)
        self._left.text_editor.textChanged.connect(self._auto_save_vault_file)
        
        self._vault_explorer.file_selected.connect(self._on_vault_file_selected)
        
        # Toolbar connect
        self._left.btn_md_h1.clicked.connect(lambda: self._insert_md_snippet("# ", ""))
        self._left.btn_md_h2.clicked.connect(lambda: self._insert_md_snippet("## ", ""))
        self._left.btn_md_bold.clicked.connect(lambda: self._insert_md_snippet("**", "**"))
        self._left.btn_md_quote.clicked.connect(lambda: self._insert_md_snippet("> ", ""))
        self._left.btn_md_tip.clicked.connect(lambda: self._insert_md_snippet("> [Tip] ", ""))
        self._left.btn_md_warn.clicked.connect(lambda: self._insert_md_snippet("> [Warning] ", ""))
        
        # Connect InsightPanel send button to inject checked files from VaultExplorer
        self._left.insight_panel.send_requested.connect(self._on_insight_send_clicked)
        
        # Connect Save Note signal from InsightPanel
        self._left.insight_panel.save_note_requested.connect(self._on_save_note_requested)
        
        # Connect Tab changes to trigger Smart Guide loading
        self._left.doc_tabs.currentChanged.connect(self._on_tab_changed)
        
        # Also trigger if items are checked while in the Insight tab
        self._vault_explorer.file_list.itemChanged.connect(lambda item: self._on_tab_changed(self._left.doc_tabs.currentIndex()))

    def _on_tab_changed(self, index: int):
        # Index 2 is Insight Lab
        if index == 2:
            checked_files = self._vault_explorer.get_checked_files()
            self._left.insight_panel.load_guide_questions(checked_files)

    def _on_insight_send_clicked(self):
        checked_files = self._vault_explorer.get_checked_files()
        print(f"MainWindow._on_insight_send_clicked triggered. Selected files: {checked_files}")
        self._left.insight_panel._on_send_clicked(checked_files)

    def _on_save_note_requested(self, title: str, content: str):
        safe_name = title.replace("/", "_").replace("\\", "_")
        new_file = self._vault_explorer.vault_dir / f"{safe_name}.md"
        
        # Avoid overwriting
        counter = 1
        while new_file.exists():
            new_file = self._vault_explorer.vault_dir / f"{safe_name}_{counter}.md"
            counter += 1
            
        try:
            with open(new_file, 'w', encoding='utf-8') as f:
                f.write(content)
            self._vault_explorer.refresh_list()
            QMessageBox.information(self, "저장 완료", f"'{new_file.name}'가 내 소스 보관함에 성공적으로 저장되었습니다.")
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", f"파일을 저장하는 중 오류가 발생했습니다: {e}")

    def _insert_md_snippet(self, prefix: str, suffix: str):
        editor = self._left.text_editor
        cursor = editor.textCursor()
        
        if cursor.hasSelection():
            text = cursor.selectedText()
            cursor.insertText(f"{prefix}{text}{suffix}")
        else:
            cursor.insertText(f"{prefix}텍스트{suffix}")
            # Move cursor back to select "텍스트" so user can type over it immediately
            cursor.movePosition(cursor.MoveOperation.Left, cursor.MoveMode.KeepAnchor, len("텍스트") + len(suffix))
            cursor.movePosition(cursor.MoveOperation.Right, cursor.MoveMode.KeepAnchor, len("텍스트"))
        
        editor.setTextCursor(cursor)
        editor.setFocus()

    def _update_live_preview(self):
        md_text = self._left.text_editor.toPlainText()
        
        html = markdown.markdown(md_text, extensions=['fenced_code', 'tables'])
        
        css = """
        <style>
            body { font-family: 'Pretendard', 'Apple SD Gothic Neo', sans-serif; color: #333; line-height: 1.6; }
            h1 { font-size: 1.5em; border-bottom: 1px solid #ddd; padding-bottom: 5px; color: #0F172A; }
            h2 { font-size: 1.3em; margin-top: 1em; color: #1E293B; }
            h3 { font-size: 1.1em; }
            blockquote { 
                border-left: 4px solid #CBD5E1; 
                padding-left: 10px; 
                color: #475569; 
                margin: 1em 0; 
                background: #F1F5F9;
                padding: 10px;
                border-radius: 4px;
            }
            code { background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; font-family: monospace; }
            pre { background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }
        </style>
        """
        self._left.text_preview.setHtml(css + html)

    def _on_vault_file_selected(self, path: str):
        self._active_vault_file = path
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Block signals so auto-save doesn't fire while setting text
            self._left.text_editor.blockSignals(True)
            self._left.text_editor.setPlainText(content)
            self._left.text_editor.blockSignals(False)
            self._update_live_preview()
            self._left.doc_tabs.setCurrentIndex(1) # Switch to Editor tab
        except Exception as e:
            print(f"Failed to read vault file: {e}")

    def _auto_save_vault_file(self):
        if self._active_vault_file:
            content = self._left.text_editor.toPlainText()
            try:
                with open(self._active_vault_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                print(f"Failed to auto-save vault file: {e}")
            
            # Debounce the heavy vector indexing operation (wait 5s after last typing)
            if hasattr(self, '_index_timer'):
                self._index_timer.stop()
            else:
                self._index_timer = QTimer(self)
                self._index_timer.setSingleShot(True)
                self._index_timer.timeout.connect(self._trigger_vault_indexer)
            self._index_timer.start(5000)

    def _trigger_vault_indexer(self):
        if self._active_vault_file:
            self._indexer_thread = VaultIndexerThread(self._active_vault_file)
            self._indexer_thread.start()

    def _on_ai_draft_clicked(self):
        settings = self._left.settings_panel.get_settings()
        title = settings.get("cover_title", "").strip()
        subtitle = settings.get("cover_subtitle", "").strip()
        header = settings.get("header_text", "").strip()
        
        # Read the current editor content (TOC) to guide the draft
        current_text = self._left.text_editor.toPlainText().strip()

        if not title:
            QMessageBox.warning(self, "입력 필요", "AI 초안을 생성하려면 먼저 왼쪽 설정 패널에서 '책 제목'을 입력해주세요.")
            return

        # Start AI thread
        self._left.btn_ai_draft.setEnabled(False)
        self._left.btn_ai_draft.setText("⏳ AI 초안 생성 중...")
        
        self.draft_thread = AiDraftThread(title, subtitle, header, current_text)
        self.draft_thread.finished.connect(self._on_ai_draft_done)
        self.draft_thread.start()

    def _on_ai_draft_done(self, result: str, is_success: bool):
        self._left.btn_ai_draft.setEnabled(True)
        self._left.btn_ai_draft.setText("✨ AI 초안 자동 생성 (기본 정보 기반)")
        
        if is_success:
            self._left.text_editor.setPlainText(result)
            self._left.doc_tabs.setCurrentIndex(1) # Ensure Editor tab is showing
        else:
            QMessageBox.critical(self, "초안 작성 실패", f"AI 초안 작성 중 오류가 발생했습니다.\n\nAI 원고 정리 > 설정 탭의 API 키를 확인해주세요.\n\n상세: {result}")

    def _on_ai_toc_clicked(self):
        settings = self._left.settings_panel.get_settings()
        title = settings.get("cover_title", "").strip()
        subtitle = settings.get("cover_subtitle", "").strip()
        header = settings.get("header_text", "").strip()

        if not title:
            QMessageBox.warning(self, "입력 필요", "AI 목차를 기획하려면 먼저 왼쪽 설정 패널에서 '책 제목'을 입력해주세요.")
            return

        # Start AI thread
        self._left.btn_ai_toc.setEnabled(False)
        self._left.btn_ai_toc.setText("⏳ AI 목차 기획 중...")
        
        self.toc_thread = AiTocThread(title, subtitle, header)
        self.toc_thread.finished.connect(self._on_ai_toc_done)
        self.toc_thread.start()

    def _on_ai_toc_done(self, result: str, is_success: bool):
        self._left.btn_ai_toc.setEnabled(True)
        self._left.btn_ai_toc.setText("📑 AI 목차 기획")
        
        if is_success:
            self._left.text_editor.setPlainText(result)
            self._left.doc_tabs.setCurrentIndex(1) # Ensure Editor tab is showing
        else:
            QMessageBox.critical(self, "목차 기획 실패", f"AI 목차 기획 중 오류가 발생했습니다.\n\nAI 원고 정리 > 설정 탭의 API 키를 확인해주세요.\n\n상세: {result}")

    def _on_ai_settings_clicked(self):
        dlg = ApiSettingsDialog(self)
        dlg.exec()

    def _on_ai_organize_clicked(self):
        current_text = self._left.text_editor.toPlainText().strip()
        dlg = AiOrganizerDialog(self, initial_text=current_text)
        if dlg.exec():
            # User accepted the result, overwrite the editor's text
            # This will automatically trigger _auto_save_vault_file due to textChanged
            self._left.text_editor.setPlainText(dlg.final_md)
            self._status.showMessage("✨ AI 원고 정리가 완료되어 에디터와 보관함에 자동 저장되었습니다.")

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
        # Determine source
        idx = self._left.doc_tabs.currentIndex()
        if idx == 0:
            source_path = self._left.drop_zone.loaded_path
            if not source_path:
                QMessageBox.warning(self, "파일 없음", "먼저 문서를 로드하세요.")
                return
        else:
            text = self._left.text_editor.toPlainText().strip()
            if not text:
                QMessageBox.warning(self, "내용 없음", "작성된 내용이 없습니다.")
                return
            
            # Save to temporary file
            temp_path = Path.home() / ".docstyle_live_editor.md"
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(text)
            source_path = str(temp_path)

        # 1. 임시 경로에 먼저 저장
        session_id = str(Path(source_path).stem)
        temp_dir = Path(tempfile.gettempdir()) / "docstyle_pro"
        temp_dir.mkdir(parents=True, exist_ok=True)
        self._temp_output_path = str(temp_dir / f"{session_id}_t{self._template_id}.docx")

        tpl_name = self._center.get_template_info(self._template_id)["name"]
        settings = self._left.settings_panel.get_settings()
        
        dlg = ProgressDialog(
            input_path=source_path,
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
