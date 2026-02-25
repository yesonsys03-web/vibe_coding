import os
import shutil
from pathlib import Path
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QAction
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, 
    QPushButton, QMessageBox, QInputDialog, QListWidgetItem, QMenu,
    QFileDialog, QDialog, QLineEdit, QTextEdit
)
import subprocess

# Optional parsers for Add Source
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None

class PasteSourceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("텍스트 붙여넣기")
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("소스 제목을 입력하세요...")
        self.title_input.setStyleSheet("padding: 8px; border: 1px solid #CBD5E1; border-radius: 4px; color: #000000;")
        
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("여기에 텍스트 본문을 붙여넣으세요...")
        self.content_input.setStyleSheet("padding: 8px; border: 1px solid #CBD5E1; border-radius: 4px; color: #000000;")
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("저장")
        btn_save.setStyleSheet("background: #8B5CF6; color: white; padding: 6px 12px; border-radius: 4px; font-weight: bold;")
        btn_save.clicked.connect(self.accept)
        
        btn_cancel = QPushButton("취소")
        btn_cancel.setStyleSheet("background: #F1F5F9; color: #475569; padding: 6px 12px; border-radius: 4px;")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        
        layout.addWidget(QLabel("소스 제목:"))
        layout.addWidget(self.title_input)
        layout.addWidget(QLabel("본문 내용:"))
        layout.addWidget(self.content_input)
        layout.addLayout(btn_layout)

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
        self.btn_new = QPushButton("➕ 소스 추가")
        self.btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.new_menu = QMenu(self)
        self.new_menu.setStyleSheet("QMenu { background: white; border: 1px solid #ccc; font-size: 13px; } QMenu::item { padding: 8px 24px; } QMenu::item:selected { background: #DBEAFE; color: #1D4ED8; font-weight: bold; }")
        
        act_empty = QAction("📝 빈 문서 쓰기", self)
        act_empty.triggered.connect(self._create_new_file)
        
        act_paste = QAction("📋 텍스트 붙여넣기", self)
        act_paste.triggered.connect(self._on_paste_text)
        
        act_import = QAction("📂 파일 가져오기", self)
        act_import.triggered.connect(self._on_import_files)
        
        self.new_menu.addAction(act_empty)
        self.new_menu.addAction(act_paste)
        self.new_menu.addAction(act_import)
        
        self.btn_new.setMenu(self.new_menu)
        
        header_layout.addWidget(header_lbl)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_new)
        
        # Tools Layout (Select All, etc.)
        tools_layout = QHBoxLayout()
        from PyQt6.QtWidgets import QCheckBox
        self.chk_select_all = QCheckBox("전체 선택")
        self.chk_select_all.setStyleSheet("color: #475569; font-size: 11px;")
        self.chk_select_all.stateChanged.connect(self._toggle_all_files)
        tools_layout.addWidget(self.chk_select_all)
        tools_layout.addStretch()

        # List Widget
        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self._on_item_clicked)
        self.file_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self._show_context_menu)
        
        layout.addLayout(header_layout)
        layout.addLayout(tools_layout)
        layout.addWidget(self.file_list)
        
        self.refresh_list()

    def _toggle_all_files(self, state):
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            item.setCheckState(Qt.CheckState.Checked if state == Qt.CheckState.Checked.value else Qt.CheckState.Unchecked)

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
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, str(f))
            self.file_list.addItem(item)
            
    def get_checked_files(self) -> list[str]:
        checked = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                checked.append(item.data(Qt.ItemDataRole.UserRole))
        return checked

    def _create_new_file(self):
        name, ok = QInputDialog.getText(self, "새 문서", "파일 이름을 입력하세요 (확장자 제외):")
        if ok and name.strip():
            safe_name = name.strip()
            new_file = self.vault_dir / f"{safe_name}.md"
            if new_file.exists():
                QMessageBox.warning(self, "오류", "이미 존재하는 이름입니다.")
                return
            
            # Create empty file
            new_file.touch()
            self.refresh_list()
            self._select_and_emit(new_file)

    def _on_paste_text(self):
        dlg = PasteSourceDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            title = dlg.title_input.text().strip()
            content = dlg.content_input.toPlainText()
            if not title:
                title = "제목_없음"
            
            safe_name = title.replace("/", "_").replace("\\", "_")
            new_file = self.vault_dir / f"{safe_name}.md"
            
            counter = 1
            while new_file.exists():
                new_file = self.vault_dir / f"{safe_name}_{counter}.md"
                counter += 1
                
            with open(new_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self.refresh_list()
            self._select_and_emit(new_file)

    def _on_import_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "소스 파일 선택", 
            str(Path.home()), 
            "Supported Files (*.txt *.md *.pdf *.docx)"
        )
        
        if not files:
            return
            
        success_count = 0
        dest_file = None
        for path_str in files:
            src_path = Path(path_str)
            safe_name = src_path.stem.replace("/", "_").replace("\\", "_")
            ext = src_path.suffix.lower()
            
            dest_file = self.vault_dir / f"{safe_name}.md"
            counter = 1
            while dest_file.exists():
                dest_file = self.vault_dir / f"{safe_name}_{counter}.md"
                counter += 1
                
            try:
                if ext in ['.txt', '.md']:
                    shutil.copy2(src_path, dest_file)
                elif ext == '.pdf' and PdfReader:
                    reader = PdfReader(str(src_path))
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n\n"
                    with open(dest_file, 'w', encoding='utf-8') as f:
                        f.write(text.strip())
                elif ext == '.docx' and Document:
                    doc = Document(str(src_path))
                    text = "\n".join([p.text for p in doc.paragraphs])
                    with open(dest_file, 'w', encoding='utf-8') as f:
                        f.write(text.strip())
                else:
                    if ext in ['.pdf', '.docx']:
                        print(f"Failed: missing dependencies for {ext}")
                    continue
                success_count += 1
            except Exception as e:
                print(f"Failed to import {src_path.name}: {e}")
                
        if success_count > 0:
            self.refresh_list()
            if dest_file:
                self._select_and_emit(dest_file)
            QMessageBox.information(self, "가져오기 완료", f"{success_count}개의 파일을 성공적으로 보관함에 추가했습니다.")

    def _select_and_emit(self, new_file: Path):
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

    def _show_context_menu(self, pos):
        item = self.file_list.itemAt(pos)
        if not item: return

        menu = QMenu(self)
        action_rename = QAction("✏️ 이름 변경", self)
        action_delete = QAction("🗑️ 삭제", self)
        action_reveal = QAction("📂 폴더 열기", self)

        menu.addAction(action_rename)
        menu.addAction(action_delete)
        menu.addAction(action_reveal)

        action = menu.exec(self.file_list.mapToGlobal(pos))
        if action == action_rename:
            self._on_rename_file(item)
        elif action == action_delete:
            self._on_delete_file(item)
        elif action == action_reveal:
            self._on_reveal_file(item)

    def _on_rename_file(self, item):
        old_path = item.data(Qt.ItemDataRole.UserRole)
        old_name = item.text()
        
        new_name, ok = QInputDialog.getText(self, "이름 변경", "새 이름을 입력하세요 (확장자 제외):", text=old_name)
        if ok and new_name.strip() and new_name.strip() != old_name:
            new_path = Path(old_path).parent / f"{new_name.strip()}.md"
            if new_path.exists():
                QMessageBox.warning(self, "오류", "이미 존재하는 이름입니다.")
                return
            try:
                os.rename(old_path, new_path)
                from bridge.vault_indexer import delete_document, index_document
                delete_document(old_path)
                index_document(str(new_path))
                self.refresh_list()
                self.select_file(str(new_path))
                self.file_selected.emit(str(new_path))
            except Exception as e:
                QMessageBox.critical(self, "오류", f"이름 변경 실패: {e}")

    def _on_delete_file(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "삭제 확인", f"'{item.text()}' 원고를 정말 삭제하시겠습니까?\n휴지통으로 이동되지 않고 즉시 삭제됩니다.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(path)
                from bridge.vault_indexer import delete_document
                delete_document(path)
                self.refresh_list()
                self.file_selected.emit("") # Signal empty file to clear editor
            except Exception as e:
                QMessageBox.critical(self, "오류", f"파일 삭제 실패: {e}")

    def _on_reveal_file(self, item):
        import subprocess
        path = item.data(Qt.ItemDataRole.UserRole)
        subprocess.run(["open", "-R", path])

