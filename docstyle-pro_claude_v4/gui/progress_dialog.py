"""
progress_dialog.py — DocStyle Pro 변환 진행 다이얼로그

기능
    - 변환 작업을 별도 QThread(ConvertWorker)에서 실행
    - 진행률 프로그레스바 + 상태 메시지 표시
    - 취소 버튼으로 작업 중단 가능
    - 완료 / 실패 / 취소 결과를 시그널로 전달

사용법
    dlg = ProgressDialog(input_path, output_path, template_id, parent)
    dlg.convert_done.connect(on_done)
    dlg.exec_()
"""

import sys
from pathlib import Path

from PyQt6.QtCore import QThread, Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QVBoxLayout,
)

# converter 임포트 (프로젝트 루트를 sys.path 에 추가)
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from bridge.converter import ConvertResult, convert


# ─────────────────────────────────────────────
# 워커 스레드
# ─────────────────────────────────────────────

class ConvertWorker(QThread):
    """
    변환 파이프라인을 UI 스레드와 분리해 실행.

    Signals
    -------
    progress(int, str)     진행률(0~100) + 메시지
    finished(ConvertResult)  완료 결과
    """

    progress = pyqtSignal(int, str)
    finished = pyqtSignal(object)  # ConvertResult

    def __init__(
        self,
        input_path: str,
        output_path: str,
        template_id: str,
        chapter_override: str = "",
        custom_settings: dict = None,
    ):
        super().__init__()
        self._input_path       = input_path
        self._output_path      = output_path
        self._template_id      = template_id
        self._chapter_override = chapter_override
        self._custom_settings  = custom_settings or {}
        self._stop_flag        = False

    def stop(self):
        self._stop_flag = True

    def run(self):
        def _cb(pct: int, msg: str = ""):
            if self._stop_flag:
                return
            self.progress.emit(pct, msg)

        if self._stop_flag:
            self.finished.emit(ConvertResult(success=False, error="사용자가 취소했습니다"))
            return

        result = convert(
            input_path=self._input_path,
            output_path=self._output_path,
            template_id=self._template_id,
            chapter_override=self._chapter_override,
            custom_settings=self._custom_settings,
            progress_callback=_cb,
        )

        if self._stop_flag:
            result = ConvertResult(success=False, error="사용자가 취소했습니다")

        self.finished.emit(result)


# ─────────────────────────────────────────────
# 진행 다이얼로그
# ─────────────────────────────────────────────

class ProgressDialog(QDialog):
    """
    변환 진행 상황을 표시하는 모달 다이얼로그.

    Signals
    -------
    convert_done(ConvertResult)
    """

    convert_done = pyqtSignal(object)

    def __init__(
        self,
        input_path: str,
        output_path: str,
        template_id: str,
        template_name: str = "",
        custom_settings: dict = None,
        parent=None,
    ):
        super().__init__(parent)
        self._worker = ConvertWorker(
            input_path=input_path,
            output_path=output_path,
            template_id=template_id,
            custom_settings=custom_settings
        )
        self._done   = False
        self._template_name = template_name or f"템플릿 {template_id}"

        self.setWindowTitle("변환 중...")
        self.setModal(True)
        self.setFixedSize(440, 220)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        self._build_ui()
        self._connect_signals()

    # ── UI 구성 ──────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(14)

        # 제목
        title = QLabel("DocStyle Pro — 변환 중")
        title.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #1E293B;")

        # 템플릿 이름
        tpl_lbl = QLabel(f"적용 템플릿: {self._template_name}")
        tpl_lbl.setFont(QFont("Arial", 10))
        tpl_lbl.setStyleSheet("color: #64748B;")

        # 프로그레스바
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(6)
        self._bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 3px;
                background: #F1F5F9;
            }
            QProgressBar::chunk {
                border-radius: 3px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3B82F6, stop:1 #22C55E);
            }
        """)

        # 상태 메시지
        self._msg = QLabel("준비 중...")
        self._msg.setFont(QFont("Arial", 9))
        self._msg.setStyleSheet("color: #64748B;")

        # 취소 버튼
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._cancel_btn = QPushButton("취소")
        self._cancel_btn.setFixedSize(80, 30)
        self._cancel_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                color: #475569;
                background: #FFFFFF;
                font-size: 11px;
                font-weight: bold;
                padding: 0 16px;
            }
            QPushButton:hover { background: #F8FAFC; border-color: #CBD5E1; }
            QPushButton:pressed { background: #F1F5F9; }
            QPushButton:disabled { color: #CBD5E1; background: #F8FAFC; }
        """)
        btn_row.addWidget(self._cancel_btn)

        layout.addWidget(title)
        layout.addWidget(tpl_lbl)
        layout.addSpacing(4)
        layout.addWidget(self._bar)
        layout.addWidget(self._msg)
        layout.addStretch()
        layout.addLayout(btn_row)

    def _connect_signals(self):
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._cancel_btn.clicked.connect(self._on_cancel)

    # ── 슬롯 ─────────────────────────────────

    def _on_progress(self, pct: int, msg: str):
        self._bar.setValue(pct)
        if msg:
            self._msg.setText(msg)

    def _on_finished(self, result: ConvertResult):
        self._done = True
        self.convert_done.emit(result)
        self.accept()

    def _on_cancel(self):
        self._worker.stop()
        self._msg.setText("취소 중...")
        self._cancel_btn.setEnabled(False)

    # ── 실행 ─────────────────────────────────

    def exec(self):
        self._worker.start()
        return super().exec()

    def closeEvent(self, event):
        if not self._done:
            self._worker.stop()
            self._worker.wait(2000)
        event.accept()
