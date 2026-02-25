from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, QTextEdit, QPushButton, QLabel, QDialog
)
from PyQt6.QtGui import QColor, QTextCharFormat, QFont, QTextCursor
from pathlib import Path
from bridge.ai_organizer import chat_with_vault, generate_guide_questions
import markdown


import re

class AiInsightThread(QThread):
    finished = pyqtSignal(str, list, bool)

    def __init__(self, query: str, filter_files: list[str] = None):
        super().__init__()
        self.query = query
        self.filter_files = filter_files

    def run(self):
        print("AiInsightThread.run() started with query:", self.query, "and filters:", self.filter_files)
        try:
            result, contexts = chat_with_vault(self.query, filter_files=self.filter_files)
            print("chat_with_vault returned successfully")
            self.finished.emit(result, contexts, True)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished.emit(str(e), [], False)

class AiGuideThread(QThread):
    finished = pyqtSignal(list, bool)
    
    def __init__(self, filter_files: list[str] = None):
        super().__init__()
        self.filter_files = filter_files
        
    def run(self):
        try:
            questions = generate_guide_questions(filter_files=self.filter_files)
            self.finished.emit(questions, True)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished.emit([str(e)], False)

class SourceViewerDialog(QDialog):
    def __init__(self, file_path: str, snippet: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"소스 확인 - {Path(file_path).name}")
        self.resize(700, 500)
        layout = QVBoxLayout(self)
        
        self.viewer = QTextEdit()
        self.viewer.setReadOnly(True)
        self.viewer.setStyleSheet("background: #FFFFFF; font-size: 15px; padding: 12px; border: 1px solid #E2E8F0; border-radius: 6px; color: #334155;")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.viewer.setPlainText(f.read())
        except Exception as e:
            self.viewer.setPlainText(f"파일을 읽을 수 없습니다: {e}")
            
        layout.addWidget(self.viewer)
        
        # Guide label
        hint = QLabel("💡 AI가 참고한 원본 문단입니다. (노란색 하이라이트 표시)")
        hint.setStyleSheet("color: #64748B; font-size: 12px;")
        layout.addWidget(hint)
        
        # Highlight snippet
        cursor = self.viewer.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        self.viewer.setTextCursor(cursor)
        
        if not self.viewer.find(snippet):
            short_snippet = snippet[:40] if len(snippet) > 40 else snippet
            self.viewer.find(short_snippet)
            
        # Apply yellow background to the exact selection
        cursor = self.viewer.textCursor()
        if cursor.hasSelection():
            fmt = QTextCharFormat()
            fmt.setBackground(QColor("#FEF08A"))
            cursor.mergeCharFormat(fmt)
            
            # Keep cursor at the end of the selection so it stays scrolled into view
            self.viewer.setTextCursor(cursor)
            
        # Set focus to nothing to remove the gray selection block but keep the yellow background
        self.setFocus()

class InsightPanel(QWidget):
    save_note_requested = pyqtSignal(str, str)
    send_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: #F8FAFC;")
        self._thread = None
        self.context_registry = []
        self._response_history = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QLabel("💡 인사이트 랩 (NotebookLM Style)")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #1E293B;")
        
        sub_header = QLabel("보관함(DocStyle Vault)에 저장된 내 원고들을 기반으로 새로운 인사이트를 도출합니다.\n예: '내가 예전에 쓴 AI 관련 글들을 바탕으로 다음 책 목차를 추천해줘'")
        sub_header.setStyleSheet("color: #64748B; font-size: 13px; line-height: 1.5;")
        
        layout.addWidget(header)
        layout.addWidget(sub_header)

        # Chat History
        self.chat_history = QTextBrowser()
        self.chat_history.setOpenExternalLinks(False)
        self.chat_history.setOpenLinks(False)
        self.chat_history.anchorClicked.connect(self._on_anchor_clicked)
        self.chat_history.setStyleSheet("""
            QTextBrowser {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 16px;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 14px;
                color: #334155;
            }
        """)
        layout.addWidget(self.chat_history, 1)
        
        # Welcome message
        self._append_message("🤖 **AI**: 안녕하세요! 보관함(Vault)에 쌓인 원고들을 모두 읽고 기다리고 있습니다. 궁금한 점이나 새로운 아이디어가 필요하시면 질문해 주세요.")
        
        # Suggested Prompts Area
        self.suggested_layout = QHBoxLayout()
        self.suggested_buttons = []
        for _ in range(3):
            btn = QPushButton("")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: #F1F5F9;
                    color: #475569;
                    border: 1px solid #CBD5E1;
                    border-radius: 12px;
                    padding: 8px 12px;
                    font-size: 13px;
                }
                QPushButton:hover { background: #E2E8F0; color: #1E293B; }
            """)
            btn.clicked.connect(lambda checked, b=btn: self._on_suggested_clicked(b.text()))
            btn.hide() # Hidden by default until questions arrive
            self.suggested_layout.addWidget(btn)
            self.suggested_buttons.append(btn)
        self.suggested_layout.addStretch()
        layout.addLayout(self.suggested_layout)

        # Input Area
        input_layout = QHBoxLayout()
        
        self.input_box = QTextEdit()
        self.input_box.setFixedHeight(80)
        self.input_box.setPlaceholderText("질문을 입력하세요...")
        self.input_box.setStyleSheet("""
            QTextEdit {
                background: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
            }
        """)

        self.btn_send = QPushButton("질문하기")
        self.btn_send.setFixedSize(100, 80)
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send.setStyleSheet("""
            QPushButton {
                background: #8B5CF6;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background: #7C3AED; }
            QPushButton:disabled { background: #C4B5FD; }
        """)
        self.btn_send.clicked.connect(lambda checked=False: self.send_requested.emit())
        
        input_layout.addWidget(self.input_box, 1)
        input_layout.addWidget(self.btn_send)

        layout.addLayout(input_layout)

    def _append_message(self, markdown_text: str):
        # Convert markdown to HTML before appending
        html = markdown.markdown(markdown_text, extensions=['fenced_code', 'tables'])
        
        # In PyQt, complex div wrappers with inline CSS can sometimes break block rendering.
        # Minimal append string without root wrappers.
        styled_html = html + "<br><hr><br>"
        
        # append() automatically puts it at the end and handles blocks correctly
        self.chat_history.append(styled_html)
        
        # Scroll to bottom
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.chat_history.setTextCursor(cursor)

    def _on_send_clicked(self, checked_files: list[str] = None):
        print(f"InsightPanel._on_send_clicked triggered with {checked_files}")
        text = self.input_box.toPlainText().strip()
        if not text:
            print("Input box was empty, returning.")
            return
            
        self.input_box.clear()
        self._append_message(f"👤 **나**: {text}")
        
        self.btn_send.setEnabled(False)
        self.btn_send.setText("생성 중...")
        
        print("Starting AiInsightThread...")
        # In a real app, `checked_files` would be passed in from MainWindow where it has access to VaultExplorer
        self._thread = AiInsightThread(text, filter_files=checked_files)
        self._thread.finished.connect(self._on_response_received)
        self._thread.start()

    def _on_suggested_clicked(self, text: str):
        self.input_box.setText(text)
        print("Suggested button clicked, automatically asking...")
        # Automatically emit the signal so MainWindow triggers the real send
        self.send_requested.emit()
        
    def load_guide_questions(self, checked_files: list[str] = None):
        """Triggered when tab is opened or files change"""
        for btn in self.suggested_buttons:
            btn.setText("추천 질문 생성 중...")
            btn.show()
            btn.setEnabled(False)
            
        self._guide_thread = AiGuideThread(filter_files=checked_files)
        self._guide_thread.finished.connect(self._on_guide_received)
        self._guide_thread.start()
        
    def _on_guide_received(self, questions: list, success: bool):
        for btn in self.suggested_buttons:
            btn.hide()
            
        if success and questions:
            for i, q in enumerate(questions):
                if i < len(self.suggested_buttons):
                    self.suggested_buttons[i].setText(q)
                    self.suggested_buttons[i].setEnabled(True)
                    self.suggested_buttons[i].show()

    def _on_anchor_clicked(self, url):
        if url.scheme() == "http" and url.host() == "cit":
            try:
                global_idx = int(url.path().strip('/'))
                if 0 <= global_idx < len(self.context_registry):
                    ctx = self.context_registry[global_idx]
                    file_path = ctx.get("source", "")
                    snippet = ctx.get("content", "")
                    
                    # Show popup dialog with highlighted text
                    dlg = SourceViewerDialog(file_path, snippet, self)
                    dlg.exec()
            except ValueError:
                pass
        elif url.scheme() == "save":
            try:
                import datetime
                from PyQt6.QtWidgets import QInputDialog
                idx = int(url.host())
                if 0 <= idx < len(self._response_history):
                    default_title = f"AI 인사이트 - {datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    title, ok = QInputDialog.getText(self, "보관함에 저장", "저장할 파일 이름을 입력하세요:", text=default_title)
                    if ok and title.strip():
                        self.save_note_requested.emit(title.strip(), self._response_history[idx])
            except ValueError:
                pass
        else:
            import webbrowser
            webbrowser.open(url.toString())

    def _on_response_received(self, result: str, contexts: list, is_success: bool):
        print(f"InsightPanel._on_response_received triggered. success={is_success}")
        self.btn_send.setEnabled(True)
        self.btn_send.setText("질문하기")
        
        if is_success:
            start_idx = len(self.context_registry)
            self.context_registry.extend(contexts)
            
            self._response_history.append(result)
            history_idx = len(self._response_history) - 1
            
            # Remove leading spaces that cause accidental markdown code blocks
            lines = []
            for line in result.split("\n"):
                if line.startswith("    ") or line.startswith("\t"):
                    lines.append(line.lstrip())
                else:
                    lines.append(line)
            clean_result = "\n".join(lines)
            
            # Replace [1], [2], etc. inside the markdown with custom hyperlinks
            def replacer(match):
                try:
                    local_idx = int(match.group(1)) - 1
                    if 0 <= local_idx < len(contexts):
                        global_idx = start_idx + local_idx
                        return f'<a href="http://cit/{global_idx}" style="color: #2563EB; text-decoration: none; font-weight: bold;">[{match.group(1)}]</a>'
                except ValueError:
                    pass
                return match.group(0)
                
            modified_result = re.sub(r'\[(\d+)\]', replacer, clean_result)
            
            # Inject save footer with empty lines to ensure it forms its own block
            footer = f'\n\n<p align="right" style="margin-top: 10px;"><a href="save://{history_idx}" style="color: #10B981; font-weight: bold; text-decoration: none;">[💾 소스로 보관함에 저장하기]</a></p>\n'
            self._append_message(f"🤖 **AI**: {modified_result}{footer}")
        else:
            self._append_message(f"❌ **시스템 오류**: 답변을 생성하지 못했습니다.\n\n상세: {result}")
