import os
from pathlib import Path
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, 
    QPushButton, QMessageBox, QInputDialog, QListWidgetItem
)

class VaultExplorer(QWidget):
    file_selected = pyqtSignal(str) # Emits the full absolute path of the selected .md file

    def __init__(self, parent=None):
        super().__init__(parent)
        self.vault_dir = Path.home() / "Documents" / "DocStyle_Vault"
        self._ensure_vault_exists()
        
        self.setFixedWidth(220)
        self.setStyleSheet("""
            QWidget {
                background: #F8FAFC;
                border-right: 1px solid #E2E8F0;
            }
            QLabel {
                color: #374151;
                font-weight: bold;
                font-size: 13px;
                padding: 4px;
            }
            QListWidget {
                border: none;
                background: transparent;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 6px;
                margin-bottom: 2px;
                color: #475569;
            }
            QListWidget::item:hover {
                background: #E2E8F0;
            }
            QListWidget::item:selected {
                background: #DBEAFE;
                color: #1D4ED8;
                font-weight: bold;
            }
            QPushButton {
                background: #EFF6FF;
                color: #2563EB;
                border: 1px solid #BFDBFE;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background: #DBEAFE; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 16, 10, 16)
        layout.setSpacing(8)
        
        # Header
        header_layout = QHBoxLayout()
        header_lbl = QLabel("📚 내 소스 보관함")
        self.btn_new = QPushButton("+ 새 원고")
        self.btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_new.clicked.connect(self._create_new_file)
        
        header_layout.addWidget(header_lbl)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_new)
        
        # List Widget
        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self._on_item_clicked)
        
        layout.addLayout(header_layout)
        layout.addWidget(self.file_list)
        
        self.refresh_list()

    def _ensure_vault_exists(self):
        if not self.vault_dir.exists():
            self.vault_dir.mkdir(parents=True, exist_ok=True)

    def refresh_list(self):
        self.file_list.clear()
        if not self.vault_dir.exists():
            return
            
        md_files = sorted(self.vault_dir.glob("*.md"), key=os.path.getmtime, reverse=True)
        for f in md_files:
            item = QListWidgetItem(f.stem) # Show without .md extension
            item.setData(Qt.ItemDataRole.UserRole, str(f))
            self.file_list.addItem(item)

    def _create_new_file(self):
        name, ok = QInputDialog.getText(self, "새 소스 생성", "파일 이름을 입력하세요 (확장자 제외):")
        if ok and name.strip():
            safe_name = name.strip()
            new_file = self.vault_dir / f"{safe_name}.md"
            if new_file.exists():
                QMessageBox.warning(self, "오류", "이미 존재하는 이름입니다.")
                return
            
            # Create empty file
            new_file.touch()
            self.refresh_list()
            
            # Auto-select the newly created file
            for i in range(self.file_list.count()):
                item = self.file_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == str(new_file):
                    self.file_list.setCurrentItem(item)
                    self.file_selected.emit(str(new_file))
                    break

    def _on_item_clicked(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        self.file_selected.emit(path)

    def select_file(self, path: str):
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == path:
                self.file_list.setCurrentItem(item)
                break
