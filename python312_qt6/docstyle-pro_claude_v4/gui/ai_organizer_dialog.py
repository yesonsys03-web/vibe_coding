from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QMessageBox, QSplitter, QWidget
)

from bridge.ai_organizer import organize_text


class AiWorkerThread(QThread):
    finished = pyqtSignal(str, bool)  # (result_text, is_success)

    def __init__(self, raw_text: str):
        super().__init__()
        self.raw_text = raw_text

    def run(self):
        try:
            result = organize_text(self.raw_text)
            self.finished.emit(result, True)
        except Exception as e:
            self.finished.emit(str(e), False)


class AiOrganizerDialog(QDialog):
    def __init__(self, parent=None, initial_text: str = ""):
        super().__init__(parent)
        self.initial_text = initial_text
        self.setWindowTitle("✨ AI 원고 정리기 (Beta)")
        self.setMinimumSize(900, 600)
        self.setStyleSheet("""
            QDialog { background: #F8FAFC; }
            QLabel { color: #374151; font-weight: bold; }
            QTextEdit {
                background: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 10px;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 13px;
                line-height: 1.5;
            }
            QPushButton {
                background: #F1F5F9;
                color: #374151;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background: #E2E8F0; }
            QPushButton:disabled { background: #E5E7EB; color: #9CA3AF; }
            
            QPushButton#btn_run {
                background: #8B5CF6;
                color: white;
                border: none;
                font-size: 13px;
            }
            QPushButton#btn_run:hover { background: #7C3AED; }
            QPushButton#btn_run:disabled { background: #C4B5FD; }
            
            QPushButton#btn_save {
                background: #10B981;
                color: white;
                border: none;
            }
            QPushButton#btn_save:hover { background: #059669; }
        """)

        self.final_md = ""
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        header = QLabel("아무렇게나 적은 글, 아이디어 메모, 혹은 긴 텍스트를 붙여넣으세요.\nAI가 문단을 나누고 소제목을 달아 깔끔한 출판용 마크다운으로 정리해 드립니다.")
        header.setStyleSheet("color: #64748B; font-weight: normal; font-size: 12px;")

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Input
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0,0,0,0)
        left_layout.addWidget(QLabel("📝 원본 텍스트"))
        self.ted_input = QTextEdit()
        self.ted_input.setPlaceholderText("여기에 텍스트를 붙여넣으세요...")
        if self.initial_text:
            self.ted_input.setPlainText(self.initial_text)
        left_layout.addWidget(self.ted_input)

        # Right: Output
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0,0,0,0)
        right_layout.addWidget(QLabel("✨ AI 정리 결과 (Markdown)"))
        self.ted_output = QTextEdit()
        self.ted_output.setPlaceholderText("결과가 여기에 표시됩니다.")
        self.ted_output.setReadOnly(True)
        self.ted_output.setStyleSheet(self.ted_output.styleSheet() + "background: #F1F5F9;")
        right_layout.addWidget(self.ted_output)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        main_layout.addWidget(header)
        main_layout.addWidget(splitter, 1)

        # Bottom Buttons
        btn_layout = QHBoxLayout()
        self.btn_run = QPushButton("마법 실행하기 🪄")
        self.btn_run.setObjectName("btn_run")
        self.btn_run.clicked.connect(self._run_ai)
        
        self.btn_save = QPushButton("이 내용으로 새 문서 만들기")
        self.btn_save.setObjectName("btn_save")
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.accept)

        self.btn_cancel = QPushButton("닫기")
        self.btn_cancel.clicked.connect(self.reject)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #8B5CF6; font-weight: normal; font-size: 12px;")

        btn_layout.addWidget(self.btn_run)
        btn_layout.addWidget(self.lbl_status)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)

        main_layout.addLayout(btn_layout)

    def _run_ai(self):
        text = self.ted_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "입력 오류", "정리할 텍스트를 먼저 입력해주세요.")
            return

        self.btn_run.setEnabled(False)
        self.btn_run.setText("AI가 영혼을 갈아넣는 중...")
        self.ted_output.clear()
        self.lbl_status.setText("통신 중... 수 초에서 1분 정도 걸릴 수 있습니다.")
        
        self.thread = AiWorkerThread(raw_text=text)
        self.thread.finished.connect(self._on_ai_finished)
        self.thread.start()

    def _on_ai_finished(self, result: str, success: bool):
        self.btn_run.setEnabled(True)
        self.btn_run.setText("마법 실행하기 🪄")
        self.lbl_status.setText("")

        if success:
            self.final_md = result
            self.ted_output.setPlainText(result)
            self.btn_save.setEnabled(True)
        else:
            QMessageBox.critical(self, "AI 오류", f"AI 호출 중 문제가 발생했습니다.\n\n{result}")
