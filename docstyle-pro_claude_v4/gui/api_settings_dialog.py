import json
import logging
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QObject
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFormLayout, QWidget, QStackedWidget,
    QMessageBox
)

import google_auth_oauthlib.flow
from google.oauth2.credentials import Credentials

CREDENTIALS_FILE = Path(__file__).parent.parent / "settings" / "ai_credentials.json"
CLIENT_SECRETS_FILE = Path(__file__).parent.parent / "settings" / "client_secrets.json"
SCOPES = ['https://www.googleapis.com/auth/generative-language']

logger = logging.getLogger(__name__)

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handles the OAuth 2.0 redirect callback."""
    def log_message(self, format, *args):
        pass  # Suppress HTTP server logs

    def do_GET(self):
        query = urlparse(self.path).query
        params = parse_qs(query)

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        if "code" in params:
            # Send HTML page
            self.wfile.write(("""
                <html>
                <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
                    <h2 style="color: #10B981;">인증 성공!</h2>
                    <p>DocStyle Pro로 돌아가서 창을 확인해주세요.</p>
                    <script>
                        setTimeout(function() { window.close(); }, 3000);
                    </script>
                </body>
                </html>
            """).encode('utf-8'))
            self.server.auth_code = params["code"][0]
        else:
            self.wfile.write(("<html><body><h2>인증이 취소되었거나 오류가 발생했습니다.</h2></body></html>").encode('utf-8'))
            self.server.auth_code = None

class ApiSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI 원고 정리기 설정")
        self.setFixedSize(450, 300)
        self.setStyleSheet("""
            QDialog { background: #FFFFFF; }
            QLabel { color: #374151; }
            QLineEdit, QComboBox {
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 6px;
                background: #F8FAFC;
            }
            QPushButton {
                background: #F1F5F9;
                color: #374151;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover { background: #E2E8F0; }
            QPushButton#btn_save {
                background: #3B82F6;
                color: white;
                border: none;
            }
            QPushButton#btn_save:hover { background: #2563EB; }
            QPushButton#btn_oauth {
                background: #10B981;
                color: white;
                border: none;
            }
            QPushButton#btn_oauth:hover { background: #059669; }
        """)

        self._creds = self._load_credentials()

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # 1. Provide Selection
        lbl_provider = QLabel("<b>사용할 AI 모델:</b>")
        self.combo_provider = QComboBox()
        self.combo_provider.addItems(["OpenAI (ChatGPT)", "Anthropic (Claude)", "Google (Gemini)"])
        self.combo_provider.currentIndexChanged.connect(self._on_provider_changed)

        hbox = QHBoxLayout()
        hbox.addWidget(lbl_provider)
        hbox.addWidget(self.combo_provider, 1)
        layout.addLayout(hbox)

        # 2. Stacked Widget for settings
        self.stack = QStackedWidget()

        # OpenAI Page
        self.page_openai = QWidget()
        lay_oa = QFormLayout(self.page_openai)
        lay_oa.setContentsMargins(0, 0, 0, 0)
        self.edit_openai_key = QLineEdit()
        self.edit_openai_key.setEchoMode(QLineEdit.EchoMode.Password)
        lay_oa.addRow("API Key:", self.edit_openai_key)
        self.stack.addWidget(self.page_openai)

        # Claude Page
        self.page_claude = QWidget()
        lay_cl = QFormLayout(self.page_claude)
        lay_cl.setContentsMargins(0, 0, 0, 0)
        self.edit_claude_key = QLineEdit()
        self.edit_claude_key.setEchoMode(QLineEdit.EchoMode.Password)
        lay_cl.addRow("API Key:", self.edit_claude_key)
        self.stack.addWidget(self.page_claude)

        # Gemini Page
        self.page_gemini = QWidget()
        lay_gm = QVBoxLayout(self.page_gemini)
        lay_gm.setContentsMargins(0, 0, 0, 0)

        lay_gm_key = QFormLayout()
        lay_gm_key.setContentsMargins(0, 0, 0, 0)
        self.edit_gemini_key = QLineEdit()
        self.edit_gemini_key.setEchoMode(QLineEdit.EchoMode.Password)
        lay_gm_key.addRow("API Key:", self.edit_gemini_key)

        lbl_or = QLabel("<b>[또는]</b>")
        lbl_or.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_gemini_status = QLabel("현재 상태: <b>로그인 필요</b>")
        self.btn_gemini_login = QPushButton("🔑 Google 계정으로 로그인 (OAuth)")
        self.btn_gemini_login.setObjectName("btn_oauth")
        self.btn_gemini_login.clicked.connect(self._start_oauth_flow)
        
        info = QLabel("※ Google OAuth를 사용하려면 'client_secrets.json' 파일이 필요합니다.")
        info.setStyleSheet("color: #94A3B8; font-size: 11px;")

        lay_gm.addLayout(lay_gm_key)
        lay_gm.addWidget(lbl_or)
        lay_gm.addWidget(self.lbl_gemini_status)
        lay_gm.addWidget(self.btn_gemini_login)
        lay_gm.addWidget(info)
        lay_gm.addStretch()
        self.stack.addWidget(self.page_gemini)

        layout.addWidget(self.stack, 1)

        # Buttons
        btns = QHBoxLayout()
        btn_cancel = QPushButton("취소")
        btn_cancel.clicked.connect(self.reject)
        self.btn_save = QPushButton("저장")
        self.btn_save.setObjectName("btn_save")
        self.btn_save.clicked.connect(self._save_and_close)
        btns.addStretch()
        btns.addWidget(btn_cancel)
        btns.addWidget(self.btn_save)
        layout.addLayout(btns)

        self._populate_ui()

    def _load_credentials(self) -> dict:
        CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if CREDENTIALS_FILE.exists():
            try:
                with open(CREDENTIALS_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"provider": "OpenAI (ChatGPT)", "openai_key": "", "claude_key": "", "gemini_key": "", "gemini_token": None}

    def _save_credentials(self):
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump(self._creds, f, indent=4)

    def _populate_ui(self):
        p = self._creds.get("provider", "OpenAI (ChatGPT)")
        idx = self.combo_provider.findText(p)
        if idx >= 0:
            self.combo_provider.setCurrentIndex(idx)
        
        self.edit_openai_key.setText(self._creds.get("openai_key", ""))
        self.edit_claude_key.setText(self._creds.get("claude_key", ""))
        self.edit_gemini_key.setText(self._creds.get("gemini_key", ""))
        
        if self._creds.get("gemini_token"):
            self.lbl_gemini_status.setText("현재 상태: <b style='color:#10B981'>✅ 성공적으로 연결됨</b>")
            self.btn_gemini_login.setText("다시 로그인하기")

    def _on_provider_changed(self, index: int):
        self.stack.setCurrentIndex(index)

    def _save_and_close(self):
        self._creds["provider"] = self.combo_provider.currentText()
        self._creds["openai_key"] = self.edit_openai_key.text()
        self._creds["claude_key"] = self.edit_claude_key.text()
        self._creds["gemini_key"] = self.edit_gemini_key.text()
        self._save_credentials()
        self.accept()

    def _start_oauth_flow(self):
        if not CLIENT_SECRETS_FILE.exists():
            QMessageBox.critical(self, "오류", "client_secrets.json 파일이 settings 폴더에 없습니다.\nGoogle Cloud Console에서 다운로드 받아주세요.")
            return

        self.btn_gemini_login.setEnabled(False)
        self.btn_gemini_login.setText("로그인 중...")
        
        def run_flow():
            try:
                # 1. Start local server
                server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
                server.auth_code = None

                # 2. Generate Google OAuth URL
                flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
                    str(CLIENT_SECRETS_FILE),
                    scopes=SCOPES
                )
                flow.redirect_uri = 'http://localhost:8080/'
                auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')

                # 3. Open Browser
                webbrowser.open(auth_url)

                # 4. Wait for callback (blocks thread)
                server.handle_request()
                
                if server.auth_code:
                    flow.fetch_token(code=server.auth_code)
                    creds = flow.credentials
                    
                    self._creds["gemini_token"] = {
                        'token': creds.token,
                        'refresh_token': creds.refresh_token,
                        'token_uri': creds.token_uri,
                        'client_id': creds.client_id,
                        'client_secret': creds.client_secret,
                        'scopes': creds.scopes
                    }
                    # Update UI on main thread safely by calling a method (simplified here)
                    QMetaObject.invokeMethod(self, "_on_oauth_success", Qt.ConnectionType.QueuedConnection)
                else:
                    QMetaObject.invokeMethod(self, "_on_oauth_fail", Qt.ConnectionType.QueuedConnection)

            except Exception as e:
                logger.error(f"OAuth error: {e}")
                QMetaObject.invokeMethod(self, "_on_oauth_fail", Qt.ConnectionType.QueuedConnection)
            finally:
                server.server_close()

        # Run in background to not block GUI
        from PyQt6.QtCore import QMetaObject
        threading.Thread(target=run_flow, daemon=True).start()

    @pyqtSlot()
    def _on_oauth_success(self):
        self._save_credentials()
        self.lbl_gemini_status.setText("현재 상태: <b style='color:#10B981'>✅ 성공적으로 연결됨</b>")
        self.btn_gemini_login.setText("다시 로그인하기")
        self.btn_gemini_login.setEnabled(True)
        QMessageBox.information(self, "성공", "Google 계정 연결이 완료되었습니다.")

    @pyqtSlot()
    def _on_oauth_fail(self):
        self.btn_gemini_login.setEnabled(True)
        self.btn_gemini_login.setText("🔑 Google 계정으로 로그인 (OAuth)")
        QMessageBox.warning(self, "실패", "인증을 완료하지 못했습니다.")
