from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, QTextEdit, QPushButton, QLabel, QDialog
)
from PyQt6.QtGui import QColor, QTextCharFormat, QFont, QTextCursor
from pathlib import Path
from bridge.ai_organizer import chat_with_vault
import markdown


import re

class AiInsightThread(QThread):
    finished = pyqtSignal(str, list, bool)

    def __init__(self, query: str, filter_files: list[str] = None):
        super().__init__()
        self.query = query
        self.filter_files = filter_files

    def run(self):
        try:
            result, contexts = chat_with_vault(self.query, filter_files=self.filter_files)
            self.finished.emit(result, contexts, True)
        except Exception as e:
            self.finished.emit(str(e), [], False)


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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: #F8FAFC;")
        self._thread = None
        self.context_registry = []
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
        # Welcome message
        self._append_message("🤖 **AI**: 안녕하세요! 보관함(Vault)에 쌓인 원고들을 모두 읽고 기다리고 있습니다. 궁금한 점이나 새로운 아이디어가 필요하시면 질문해 주세요.")
        
        layout.addWidget(self.chat_history, 1)

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
        # Click handler is wired up in main_window.py to inject VaultExplorer state
        
        input_layout.addWidget(self.input_box, 1)
        input_layout.addWidget(self.btn_send)

        layout.addLayout(input_layout)

    def _append_message(self, markdown_text: str):
        # Convert markdown to HTML before appending
        html = markdown.markdown(markdown_text, extensions=['fenced_code', 'tables'])
        
        # We inject some CSS so the blockquotes/code look nice inside the chat
        styled_html = f"""
        <div style="margin-bottom: 20px;">
            {html}
        </div>
        <hr style="border: 0; border-top: 1px solid #E2E8F0; margin: 10px 0;">
        """
        
        self.chat_history.append(styled_html)
        
        # Scroll to bottom
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.chat_history.setTextCursor(cursor)

    def _on_send_clicked(self, checked_files: list[str] = None):
        text = self.input_box.toPlainText().strip()
        if not text:
            return
            
        self.input_box.clear()
        self._append_message(f"👤 **나**: {text}")
        
        self.btn_send.setEnabled(False)
        self.btn_send.setText("생성 중...")
        
        # In a real app, `checked_files` would be passed in from MainWindow where it has access to VaultExplorer
        self._thread = AiInsightThread(text, filter_files=checked_files)
        self._thread.finished.connect(self._on_response_received)
        self._thread.start()

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
        else:
            import webbrowser
            webbrowser.open(url.toString())

    def _on_response_received(self, result: str, contexts: list, is_success: bool):
        self.btn_send.setEnabled(True)
        self.btn_send.setText("질문하기")
        
        if is_success:
            start_idx = len(self.context_registry)
            self.context_registry.extend(contexts)
            
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
                
            modified_result = re.sub(r'\[(\d+)\]', replacer, result)
            self._append_message(f"🤖 **AI**: {modified_result}")
        else:
            self._append_message(f"❌ **시스템 오류**: 답변을 생성하지 못했습니다.\n\n상세: {result}")
