import sys
import sqlite3
import os
import shutil
import json
import re
import textwrap
from datetime import datetime
from datetime import timedelta
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog, QPrintDialog
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QCalendarWidget, QLabel, QPushButton, 
                           QLineEdit, QTextEdit, QMessageBox, QScrollArea,
                           QMenu, QDialog, QSpinBox, QToolButton, QFrame, QCheckBox, 
                           QComboBox, QListWidget, QListWidgetItem, QSystemTrayIcon, 
                           QAction, QMenuBar, QGroupBox, QFormLayout, QFileDialog, QTreeWidget, QTreeWidgetItem, QRadioButton, QButtonGroup, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QDate, QLocale, QRect, QPoint, QRectF
from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QIcon, QPen, QPainter, QPainterPath, QPixmap

class NoticeDialog(QDialog):
    def __init__(self, parent=None, notice_id=None):
        super().__init__(parent)
        self.parent = parent
        self.notice_id = notice_id
        self.initUI()
        self.load_current_notice()

    def load_current_notice(self):
        try:
            with self.parent.conn:
                self.parent.cursor.execute('''
                    SELECT content FROM notices 
                    ORDER BY created_time DESC 
                    LIMIT 1
                ''')
                result = self.parent.cursor.fetchone()
                if result:
                    self.content_input.setText(result[0])
        except Exception as e:
            QMessageBox.critical(self, '오류', f'공지사항 로드 중 오류가 발생했습니다: {str(e)}')

    def initUI(self):
        self.setWindowTitle('공지사항 관리')
        self.setModal(True)
        self.setMinimumWidth(400)
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # 내용 입력
        content_label = QLabel('내용:')
        content_label.setStyleSheet("""
            QLabel {
                color: #333333;
                font-weight: bold;
                font-size: 13px;
            }
        """)
        
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText('공지사항 내용을 입력하세요')
        self.content_input.setStyleSheet("""
            QTextEdit {
                padding: 8px;
                border: 1px solid #cccccc;
                border-radius: 5px;
                background-color: white;
                color: #333333;
                font-size: 13px;
            }
            QTextEdit:focus {
                border: 1px solid #5CD1E5;
            }
        """)
        self.content_input.setMinimumHeight(200)
        layout.addWidget(content_label)
        layout.addWidget(self.content_input)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton('저장')
        cancel_btn = QPushButton('취소')
        
        for btn in [save_btn, cancel_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    padding: 8px 20px;
                    background-color: #5CD1E5;
                    border: none;
                    border-radius: 5px;
                    color: white;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #4BA3B3;
                }
            """)
            btn.setFixedWidth(100)
        
        cancel_btn.setStyleSheet("""
            QPushButton {
                    padding: 8px 20px;
                    background-color: #5CD1E5;
                    border: none;
                    border-radius: 5px;
                    color: white;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #4BA3B3;
        """)
        
        save_btn.clicked.connect(self.save_notice)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
    def save_notice(self):
        content = self.content_input.toPlainText().strip()
        
        if not content:
            QMessageBox.warning(self, '경고', '내용을 입력해주세요.')
            return
            
        try:
            with self.parent.conn:
                # 기존 공지사항이 있는지 확인
                self.parent.cursor.execute('SELECT id FROM notices LIMIT 1')
                result = self.parent.cursor.fetchone()
                
                if result:  # 기존 공지사항이 있으면 업데이트
                    self.parent.cursor.execute('''
                        UPDATE notices 
                        SET content = ?, created_by = ?, created_time = datetime('now', 'localtime')
                        WHERE id = ?
                    ''', (content, self.parent.current_user, result[0]))
                else:  # 없으면 새로 추가
                    self.parent.cursor.execute('''
                        INSERT INTO notices (content, created_by, created_time)
                        VALUES (?, ?, datetime('now', 'localtime'))
                    ''', (content, self.parent.current_user))
                    
            QMessageBox.information(self, '알림', '공지사항이 저장되었습니다.')
            self.parent.load_latest_notice()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, '오류', f'공지사항 저장 중 오류가 발생했습니다: {str(e)}')

class MainWindow(QMainWindow):
    def __init__(self, selected_date=None):
        super().__init__()
        self.selected_date = selected_date
        self.setWindowTitle("완료 선적 리스트")
        self.setGeometry(100, 100, 400, 600)
        self.setAcceptDrops(True)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        
        # 트리 위젯으로 변경
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["폴더/파일"])
        layout.addWidget(self.tree_widget)
        # 입력 항목들을 담을 수평 레이아웃
        input_layout = QHBoxLayout()
        
        # Environments 콤보박스
        env_label = QLabel("Environments:")
        self.env_combo = QComboBox()
        self.env_combo.addItems(["BB", "TGN", "BM", "KOTH", "MS"])
        input_layout.addWidget(env_label)
        input_layout.addWidget(self.env_combo)
        
        # Jobs 입력
        jobs_label = QLabel("Jobs:")
        self.jobs_input = QLineEdit()
        self.jobs_input.setFixedWidth(150)
        input_layout.addWidget(jobs_label)
        input_layout.addWidget(self.jobs_input)
        
        self.main_radio = QRadioButton("본편")
        self.retake_radio = QRadioButton("Retake")

        # 버튼 그룹으로 묶어서 하나만 선택되게 함
        self.episode_group = QButtonGroup()
        self.episode_group.addButton(self.main_radio)
        self.episode_group.addButton(self.retake_radio)

        # 레이아웃에 추가
        input_layout.addWidget(self.main_radio)
        input_layout.addWidget(self.retake_radio)

        layout.addLayout(input_layout)
        
        # 버튼들
        button_layout = QHBoxLayout()
        self.create_btn = QPushButton("리스트 생성")
        self.save_btn = QPushButton("저장")
        self.reset_btn = QPushButton("초기화")

        self.create_btn.setFixedWidth(100)
        self.save_btn.setFixedWidth(100)
        self.reset_btn.setFixedWidth(100)
                
        self.create_btn.clicked.connect(self.create_list)
        self.save_btn.clicked.connect(self.save_file)
        self.reset_btn.clicked.connect(self.reset_all)
        
        button_layout.addWidget(self.create_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.reset_btn)
        layout.addLayout(button_layout)
        
        main_widget.setLayout(layout)
        
        self.folder_contents = {}
        self.current_folder = None

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            is_first_folder = len(self.folder_contents) == 0
            
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if os.path.isdir(file_path):
                    self.current_folder = file_path
                    folder_name = os.path.basename(os.path.normpath(file_path))
                    
                    # 모든 하위 파일들을 재귀적으로 수집
                    all_files = []
                    exclude_items = ['.DS_Store', 'groups', 'library', 'palette-library']
                
                    for root, dirs, files in os.walk(file_path):
                        for file in files:
                            if file not in exclude_items:
                                # 파일명만 추출 (경로 제외)
                                all_files.append(os.path.basename(file))
                    
                    # 폴더명 표시
                    folder_item = QTreeWidgetItem(self.tree_widget)
                    folder_item.setText(0, folder_name)
                    
                    # 내용 개수 표시
                    count_item = QTreeWidgetItem(folder_item)
                    count_item.setText(0, f"▼ {len(all_files)}개")
                    
                    # 파일들 표시
                    for file in sorted(all_files):
                        file_item = QTreeWidgetItem(count_item)
                        file_item.setText(0, file)
                    
                    folder_item.setExpanded(True)
                    count_item.setExpanded(True)
                    
                    if is_first_folder:
                        self.jobs_input.setText(folder_name)
                    
                    self.folder_contents[file_path] = {
                        'name': folder_name,
                        'contents': all_files
                    }
                
                event.acceptProposedAction()

    def create_list(self):
        if self.folder_contents:
            tk_contents = {}
            other_contents = []
            
            for folder_path, data in self.folder_contents.items():
                contents = data['contents']
                for content in contents:
                    # .mov 파일만 처리
                    if not content.endswith('.mov'):
                        continue
                    
                    # 파일명에서 .mov 확장자 제거
                    base_name = content.replace('.mov', '')
                    
                    # TK나 v00x 포함 여부 확인
                    tk_found = False
                    for word in base_name.split('_'):
                        if 'TK' in word.upper():  # 대소문자 구분 없이 TK 검사
                            tk_number = word
                            tk_found = True
                            break
                        elif word.lower().startswith('v') and len(word) == 4 and word[1:].isdigit():
                            version_num = int(word[1:])  # v002 -> 2
                            tk_number = f'TK{version_num}'  # TK2
                            tk_found = True
                            break
                    
                    if tk_found:
                        if tk_number not in tk_contents:
                            tk_contents[tk_number] = []
                        tk_contents[tk_number].append(base_name)
                    else:
                        other_contents.append(base_name)
            
            # 공통 헤더 정보
            formatted_text = f"environments: {self.env_combo.currentText()}\n" \
                            f"jobs: {self.jobs_input.text()}\n" \
                            f"episode_type: {'Retake' if self.retake_radio.isChecked() else '본편'}\n" \
                            f"선적 날짜: {self.selected_date if self.selected_date else datetime.now().strftime('%Y-%m-%d')}\n\n"
            
            # TK 목록 추가
            for tk in sorted(tk_contents.keys()):
                items = sorted(tk_contents[tk])
                if items:
                    formatted_text += f"=== {tk} 목록 ({len(items)}개) ===\n"
                    for i in range(0, len(items), 4):
                        chunk = items[i:i+4]
                        formatted_text += "    ".join(chunk) + "\n"
                    formatted_text += "\n"
            
            # 본편 Scene 목록 추가
            if other_contents:
                formatted_text += f"=== Scene 목록 ({len(other_contents)}개) ===\n"
                for i in range(0, len(other_contents), 4):
                    chunk = other_contents[i:i+4]
                    formatted_text += "    ".join(chunk) + "\n"
            
            self.list_data = formatted_text
            self.save_file()
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("리스트가 완료되었습니다.")
            msg.setWindowTitle("완료")
            msg.exec_()

    def save_file(self):
        if hasattr(self, 'list_data'):
            # 두 가능한 경로 설정
            base_paths = [
                '/USA_DB/test_jn/ship_list',
                '/System/Volumes/Data/mnt/USA_DB/test_jn/ship_list',
                '/System/Volumes/Data/USA_DB/test_jn/ship_list'
            ]
            
            date_str = self.selected_date if self.selected_date else datetime.now().strftime('%Y-%m-%d')
            file_name = f"{self.env_combo.currentText()}-{self.jobs_input.text()}-{date_str}.txt"
            
            # 각 경로에 디렉토리 생성 및 파일 저장
            for base_path in base_paths:
                os.makedirs(base_path, exist_ok=True)
                file_path = os.path.join(base_path, file_name)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.list_data)

    def reset_all(self):
        self.tree_widget.clear()
        self.jobs_input.clear()
        self.folder_contents.clear()
        self.current_folder = None
        if hasattr(self, 'list_data'):
            del self.list_data

class UserManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 두 가능한 경로 설정
        base_paths = [
            '/USA_DB/test_jn',
            '/System/Volumes/Data/mnt/USA_DB/test_jn',
            '/System/Volumes/Data/USA_DB/test_jn'
        ]
        
        # 실제 존재하는 경로 확인
        for base_path in base_paths:
            if os.path.exists(base_path):
                self.users_file = os.path.join(base_path, 'scheduler_user.json')
                break
        else:
            # 기본 경로 설정
            self.users_file = '/USA_DB/test_jn/scheduler_user.json'
        self.current_dept = None
        self.users = {}  # Initialize users dictionary
        self.load_users()
        self.initUI()  # UI 초기화를 먼저 실행
        last_user = self.load_last_user()  # 그 다음 마지막 사용자 로드
        if last_user:  # 마지막으로 id_input 설정
            self.username_input.setText(last_user)
            
            
    def initUI(self):
        self.setWindowTitle('사용자 관리')
        self.setFixedSize(600, 700)
        layout = QVBoxLayout()
        
        # 사용자 목록
        users_group = QGroupBox('사용자 목록')
        users_layout = QVBoxLayout()
        self.users_list = QListWidget()
        self.users_list.itemClicked.connect(self.on_user_selected)
        users_layout.addWidget(self.users_list)
        users_group.setLayout(users_layout)

        # 새 사용자 추가 버튼
        new_user_btn = QPushButton('새 사용자 추가')
        new_user_btn.clicked.connect(self.clear_user_form)
        new_user_btn.setStyleSheet("""
            QPushButton {
                color: black;
                background-color: #E4F7BA;
                border: none;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #D4E7AA;
            }
        """)
        users_layout.addWidget(new_user_btn)
        
        # 사용자 정보
        input_group = QGroupBox('사용자 정보')
        input_layout = QVBoxLayout()
        
        # 사용자명 입력
        name_layout = QHBoxLayout()
        name_label = QLabel('사용자명:')
        self.username_input = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.username_input)
        
        # 부서 선택
        # 부서 선택 (버튼으로 변경)
        dept_layout = QHBoxLayout()
        dept_label = QLabel('부서:')
        dept_label.setFixedWidth(80)
        dept_layout.addWidget(dept_label)
        
        self.dept_buttons = {}
        for dept in ['3D', '번역부', '제작부', '카메라', '시스템', '기타']:
            btn = QPushButton(dept)
            btn.setCheckable(True)
            btn.setChecked(False)
            btn.setFocusPolicy(Qt.NoFocus)  # 포커스 정책 설정
            btn.clicked.connect(lambda checked, d=dept: self.select_department(d))
            dept_layout.addWidget(btn)
            self.dept_buttons[dept] = btn
        
        input_layout.addLayout(name_layout)
        input_layout.addLayout(dept_layout)
        input_group.setLayout(input_layout)
        
        permission_group = QGroupBox('권한 설정')
        permission_layout = QVBoxLayout()

        # 일정 관리 버튼 추가
        manage_btn = QPushButton('일정 관리')
        manage_btn.setCheckable(True)
        manage_btn.clicked.connect(self.toggle_event_management)
        permission_layout.addWidget(manage_btn)

        # 기본 권한
        self.permissions = {
            'edit': QCheckBox('일정 수정'),      
            'delete': QCheckBox('일정 삭제'),     # 일정창의 삭제 버튼
            'move': QCheckBox('일정 이동'),
            'list_create': QCheckBox('완료 리스트 생성'),
            'context_menu_add': QCheckBox('메뉴 일정 추가'),    # 우클릭 메뉴 추가
            'context_menu_edit': QCheckBox('메뉴 일정 편집')    # 우클릭 메뉴 편집
        }

        # 상태 변경 권한
        self.status_permissions = {
            'planned': QCheckBox('예정 상태 변경'),
            'complete': QCheckBox('완료 상태 변경')
        }

        # 일정 관리 권한 그룹
        event_manage_group = QGroupBox('일정 관리 권한')
        event_manage_layout = QVBoxLayout()
        event_manage_layout.addWidget(self.permissions['edit'])
        event_manage_layout.addWidget(self.permissions['delete'])
        event_manage_layout.addWidget(self.permissions['move'])
        event_manage_layout.addWidget(self.permissions['list_create'])
        event_manage_group.setLayout(event_manage_layout)
        permission_layout.addWidget(event_manage_group)

        # 메뉴 권한 그룹
        menu_group = QGroupBox('메뉴 권한')
        menu_layout = QVBoxLayout()
        menu_layout.addWidget(self.permissions['context_menu_add'])
        menu_layout.addWidget(self.permissions['context_menu_edit'])
        menu_group.setLayout(menu_layout)
        permission_layout.addWidget(menu_group)

        # 상태 변경 권한 체크박스 추가
        status_box = QGroupBox('상태 변경 권한')
        status_layout = QVBoxLayout()
        for perm in self.status_permissions.values():
            status_layout.addWidget(perm)
        status_box.setLayout(status_layout)
        permission_layout.addWidget(status_box)
        permission_group.setLayout(permission_layout)
        
        # 버튼
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton('저장')
        delete_btn = QPushButton('삭제')
        save_btn.clicked.connect(self.save_user)
        delete_btn.clicked.connect(self.delete_user)
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(delete_btn)
        
        layout.addWidget(users_group)
        layout.addWidget(input_group)
        layout.addWidget(permission_group)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
        
        self.update_users_list()    

    def toggle_event_management(self):
        # 버튼의 체크 상태 확인
        is_checked = self.sender().isChecked()
        
        # 관련 권한들 체크/해제
        self.permissions['edit'].setChecked(is_checked)
        self.permissions['delete'].setChecked(is_checked)
        self.permissions['move'].setChecked(is_checked)
        self.permissions['context_menu_add'].setChecked(is_checked)
        self.permissions['context_menu_edit'].setChecked(is_checked)            

    def clear_user_form(self):
        # 입력 필드 초기화
        self.username_input.clear()
        
        # 부서 선택 해제
        for btn in self.dept_buttons.values():
            btn.setChecked(False)
        self.current_dept = None
        
        # 권한 체크박스 해제
        for cb in self.permissions.values():
            cb.setChecked(False)
        for cb in self.status_permissions.values():
            cb.setChecked(False)
        
        # 사용자 목록 선택 해제
        self.users_list.clearSelection()        

    def select_department(self, dept):
        for btn in self.dept_buttons.values():
            btn.setChecked(False)
        # 현재 선택된 부서가 있고, 같은 부서를 다시 클릭한 경우
        if self.current_dept == dept:
            self.dept_buttons[dept].setChecked(False)
            self.current_dept = None
        else:
            # 다른 부서를 선택한 경우
            if self.current_dept:
                self.dept_buttons[self.current_dept].setChecked(False)
            self.dept_buttons[dept].setChecked(True)
            self.current_dept = dept
            
    def update_users_list(self):
        self.users_list.clear()
        for username, data in self.users.items():
            self.users_list.addItem(f"{username} - [{data['group']}]")
            
    def on_user_selected(self, item):
        username = item.text().split(' - ')[0]
        user_data = self.users[username]
        self.username_input.setText(username)
        
        # 부서 버튼 상태 업데이트
        for dept, btn in self.dept_buttons.items():
            btn.setChecked(dept == user_data['group'])
        
        # 모든 체크박스를 먼저 해제
        for checkbox in self.permissions.values():
            checkbox.setChecked(False)
        for checkbox in self.status_permissions.values():
            checkbox.setChecked(False)
        
        # 해당 사용자의 권한에 따라 체크박스 설정
        for perm_name, checked in user_data['permissions'].items():
            if perm_name in self.permissions:
                self.permissions[perm_name].setChecked(checked)
        
        for status_name, checked in user_data['status_permissions'].items():
            if status_name in self.status_permissions:
                self.status_permissions[status_name].setChecked(checked)
    
    def save_user(self):
        username = self.username_input.text()
        if not username:
            QMessageBox.warning(self, '경고', '사용자명을 입력하세요.')
            return
            
        # 선택된 부서 확인
        selected_dept = None
        for dept, btn in self.dept_buttons.items():
            if btn.isChecked():
                selected_dept = dept
                break
        
        if not selected_dept:
            QMessageBox.warning(self, '경고', '부서를 선택하세요.')
            return
        
        # 새로운 사용자 정보
        user_data = {
            'group': selected_dept,
            'permissions': {name: cb.isChecked() for name, cb in self.permissions.items()},
            'status_permissions': {name: cb.isChecked() for name, cb in self.status_permissions.items()}
        }
        
        # 기존 사용자인 경우 수정 확인
        if username in self.users:
            reply = QMessageBox.question(
                self, 
                '사용자 수정', 
                f'"{username}" 사용자의 정보를 수정하시겠습니까?',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
                
        # 사용자 정보 저장/수정
        self.users[username] = user_data
        
        try:
            os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=4)
            
            self.update_users_list()
            QMessageBox.information(self, '성공', '사용자 정보가 저장되었습니다.')
        except Exception as e:
            QMessageBox.warning(self, '오류', f'사용자 정보 저장 중 오류가 발생했습니다: {str(e)}')

    def delete_user(self):
        username = self.username_input.text()
        if username in self.users:
            reply = QMessageBox.question(self, '확인', f'{username}을(를) 삭제하시겠습니까?',
                                    QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    del self.users[username]
                    with open(self.users_file, 'w') as f:
                        json.dump(self.users, f, indent=4)
                    self.update_users_list()
                    self.username_input.clear()
                    # 부서 버튼 선택 해제
                    for btn in self.dept_buttons.values():
                        btn.setChecked(False)
                    # 권한 체크박스 해제
                    for cb in self.permissions.values():
                        cb.setChecked(False)
                    for cb in self.status_permissions.values():
                        cb.setChecked(False)
                    QMessageBox.information(self, '성공', '사용자가 삭제되었습니다.')
                except Exception as e:
                    QMessageBox.warning(self, '오류', f'사용자 삭제 중 오류가 발생했습니다: {str(e)}')

    def load_users(self):
        try:
            # 파일이 존재하는 경로 확인
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    self.users = json.load(f)
            else:
                self.users = {}
                # 디렉토리가 없으면 생성 시도
                for base_path in ['/USA_DB/test_jn', '/System/Volumes/Data/mnt/USA_DB/test_jn', '/System/Volumes/Data/USA_DB/test_jn']:
                    try:
                        os.makedirs(base_path, exist_ok=True)
                        self.users_file = os.path.join(base_path, 'scheduler_user.json')
                        with open(self.users_file, 'w') as f:
                            json.dump(self.users, f, indent=4)
                        break
                    except Exception:
                        continue
        except Exception as e:
            print(f"Error loading users: {e}")
            self.users = {}

    def save_last_user(self, username):
        file_path = '/Users/usabatch/last_user_id.txt'
        try:
            # 디렉토리가 없으면 생성
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            # 파일 쓰기
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(username)
                f.flush()  # 버퍼 강제 저장
        except Exception as e:
            print(f"Error saving last user: {e}")

    def load_last_user(self):
        file_path = '/Users/usabatch/last_user_id.txt'
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:  # 내용이 있는 경우에만 반환
                        return content
        except Exception as e:
            print(f"Error loading last user: {e}")
        return "" 

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        base_paths = [
            '/USA_DB/test_jn',
            '/System/Volumes/Data/mnt/USA_DB/test_jn',
            '/System/Volumes/Data/USA_DB/test_jn'
        ]
        
        # 실제 존재하는 경로 확인
        for base_path in base_paths:
            if os.path.exists(base_path):
                self.users_file = os.path.join(base_path, 'scheduler_user.json')
                break
        else:
            # 기본 경로 설정
            self.users_file = '/USA_DB/test_jn/scheduler_user.json'
        self.load_users()
        last_user = self.load_last_user()
        self.initUI()
        if last_user:
            self.id_input.setText(last_user)
            self.id_input.selectAll()

    def load_users(self):
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    self.users = json.load(f)
            else:
                self.users = {}
                os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
                with open(self.users_file, 'w') as f:
                    json.dump(self.users, f, indent=4)
        except Exception as e:
            print(f"Error loading users: {e}")
            self.users = {}            

    def save_last_user(self, username):
        file_path = '/Users/usabatch/last_user_id.txt'
        try:
            # 디렉토리가 없으면 생성
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            # 파일 쓰기
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(username)
                f.flush()  # 버퍼 강제 저장
        except Exception as e:
            print(f"Error saving last user: {e}")

    def load_last_user(self):
        file_path = '/Users/usabatch/last_user_id.txt'
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:  # 내용이 있는 경우에만 반환
                        return content
        except Exception as e:
            print(f"Error loading last user: {e}")
        return "" 
        
    def initUI(self):
        self.setWindowTitle('Yeson 스케줄러')
        self.setFixedSize(400, 450)
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # 메인 컨테이너
        main_widget = QWidget()
        main_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 10px;
            }
        """)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # 제목 레이블
        title_label = QLabel('Yeson 스케줄러')
        title_label.setStyleSheet("""
            font-size: 30px;
            color: #333333;
            font-weight: bold;
            padding: 10px;
        """)
        title_label.setAlignment(Qt.AlignCenter)

        # 설명 레이블
        info_label = QLabel('기본 아이디는 guest입니다')
        info_label.setStyleSheet("""
            font-size: 15px;
            color: #888888;
            padding: 0px;
        """)
        info_label.setAlignment(Qt.AlignCenter)
        
        # 입력 필드 컨테이너
        input_container = QWidget()
        input_layout = QVBoxLayout()
        input_layout.setSpacing(15)
        
        # 아이디 입력
        id_layout = QHBoxLayout()
        id_label = QLabel('   아이디')
        id_label.setStyleSheet("color: #666666; font-weight: bold;")
        id_label.setFixedWidth(70)
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText('아이디를 입력하세요')
        self.id_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: #f8f8f8;
                color: #333333;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #5CD1E5;
                background-color: white;
            }
        """)
        self.id_input.textChanged.connect(self.on_id_changed)
        id_layout.addWidget(id_label)
        id_layout.addWidget(self.id_input)
        
        # 비밀번호 입력
        pw_layout = QHBoxLayout()
        pw_label = QLabel('비밀번호')
        pw_label.setStyleSheet("color: #666666; font-weight: bold;")
        pw_label.setFixedWidth(70)
        self.pw_input = QLineEdit()
        self.pw_input.setPlaceholderText('비밀번호를 입력하세요')
        self.pw_input.setEchoMode(QLineEdit.Password)
        self.pw_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: #f8f8f8;
                color: #333333;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #5CD1E5;
                background-color: white;
            }
        """)
        pw_layout.addWidget(pw_label)
        pw_layout.addWidget(self.pw_input)
        self.pw_widget = QWidget()
        self.pw_widget.setLayout(pw_layout)
        self.pw_widget.hide()
        
        # 로그인 버튼
        login_btn = QPushButton('로그인')
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #5CD1E5;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #4BA3B3;
            }
        """)
        login_btn.clicked.connect(self.check_login)
        
        # 레이아웃 구성
        input_layout.addLayout(id_layout)
        input_layout.addWidget(self.pw_widget)
        input_container.setLayout(input_layout)
        
        main_layout.addWidget(title_label)
        main_layout.addWidget(info_label)
        main_layout.addWidget(input_container)
        main_layout.addWidget(login_btn, alignment=Qt.AlignCenter)
        main_layout.addStretch()
        
        main_widget.setLayout(main_layout)
        layout.addWidget(main_widget)
        self.setLayout(layout)
            
    def on_id_changed(self, text):
        # admin 계정일 때만 비밀번호 입력창 표시
        if text.lower() == 'admin':
            self.pw_widget.show()
        else:
            self.pw_widget.hide()
            self.pw_input.clear()
            
    # LoginDialog의 check_login 메서드 수정
    def check_login(self):
        id = self.id_input.text()
        
        if id.lower() == 'admin':
            if self.pw_input.text() == "zmflsj":
                self.current_user = 'admin'
                self.save_last_user(id)
                self.permissions = {
                    'permissions': {
                        'add': True,
                        'edit': True,
                        'delete': True,
                        'move': True,
                        'list_create': True,
                        'context_menu_add': True,    # 우클릭 메뉴 추가 권한
                        'context_menu_edit': True    # 우클릭 메뉴 편집 권한
                    },
                    'status_permissions': {
                        'planned': True,
                        'progress': True,
                        'complete': True
                    }
                }
                self.accept()
            else:
                QMessageBox.warning(self, '경고', '비밀번호가 잘못되었습니다.')
        else:
            # 사용자 정보 파일에서 확인
            base_paths = [
                '/USA_DB/test_jn',
                '/System/Volumes/Data/mnt/USA_DB/test_jn',
                '/System/Volumes/Data/USA_DB/test_jn'
            ]
            
            user_found = False
            for base_path in base_paths:
                users_file = os.path.join(base_path, 'scheduler_user.json')
                if os.path.exists(users_file):
                    with open(users_file, 'r') as f:
                        users = json.load(f)
                        if id in users:
                            self.current_user = id
                            self.save_last_user(id)
                            self.permissions = {
                                'permissions': users[id]['permissions'],
                                'status_permissions': users[id]['status_permissions']
                            }
                            self.accept()
                            user_found = True
                            break
            
            if not user_found:
                QMessageBox.warning(self, '경고', '등록되지 않은 사용자입니다.')

class CustomCalendarWidget(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dates_with_events = set()    # 일정이 있는 날짜
        self.completed_dates = set()      # 완료된 일정 날짜
        self.my_dates = set()            # 내가 작성한 일정이 있는 날짜
        self.show_my_events = False      # 내 일정만 보기 상태
        self.current_user = None         # 현재 로그인한 사용자
        self.filtered_dates = None       # 필터링된 일정이 있는 날짜
        self.holidays = {
            '01-01': '신정',
            '01-27': '임시공휴일(설날)',
            '01-28': '설날',
            '01-29': '설날',
            '01-30': '설날',
            '03-01': '삼일절',
            '03-03': '대체공휴일(삼일절)',
            '05-05': '어린이날',
            '05-06': '대체공휴일(어린이날)',
            '05-15': '부처님오신날',
            '06-06': '현충일',
            '08-15': '광복절',
            '10-03': '개천절',
            '10-05': '추석',
            '10-06': '추석',
            '10-07': '추석',
            '10-08': '대체공휴일(추석)',
            '10-09': '한글날',
            '12-25': '크리스마스'
        }
        
    def setDatesWithEvents(self, dates, completed_dates):
        """일정이 있는 날짜와 완료된 날짜 설정"""
        self.dates_with_events = set(dates)
        self.completed_dates = set(completed_dates)
        self.updateCells()
        
    def setMyDates(self, my_dates):
        """내가 작성한 일정이 있는 날짜 설정"""
        self.my_dates = set(my_dates)
        
    def setCurrentUser(self, user):
        """현재 로그인한 사용자 설정"""
        self.current_user = user
        
    def setShowMyEvents(self, show):
        """내 일정만 보기 상태 설정"""
        self.show_my_events = show
        self.updateCells()

    def update_filtered_dates(self, filtered_dates):
        """필터링된 날짜 설정"""
        self.filtered_dates = filtered_dates
        self.updateCells()        
    
    def paintCell(self, painter, rect, date):
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 날짜 상태 확인
        is_other_month = date.month() != self.monthShown()
        date_str = date.toString('MM-dd')
        is_holiday = date_str in self.holidays
        is_sunday = date.dayOfWeek() == 7

        # 배경 그리기
        if is_other_month:
            painter.fillRect(rect, QColor('#f0f0f0'))
        else:
            painter.fillRect(rect, QColor('white'))
        
        triangle_size = min(rect.width(), rect.height()) // 2

        # 오늘 날짜 표시
        if date == QDate.currentDate():
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor('#00D8FF'))
            circle_size = min(rect.width(), rect.height()) * 0.4
            circle_x = rect.x() + (rect.width() - circle_size) / 2
            circle_y = rect.y() + (rect.height() - circle_size) / 2
            painter.drawEllipse(QRectF(circle_x, circle_y, circle_size, circle_size))

        # 날짜 텍스트 그리기
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        
        # 날짜 색상 설정
        if is_other_month:
            painter.setPen(QColor('#aaaaaa'))
        elif is_holiday or is_sunday:
            painter.setPen(QColor('red'))
        elif date.dayOfWeek() == 6:
            painter.setPen(QColor('blue'))
        else:
            painter.setPen(QColor('black'))

        # 날짜 텍스트 그리기
        painter.drawText(rect, Qt.AlignCenter, str(date.day()))

        # 일정 표시 여부 결정
        should_show_event = False
        if self.show_my_events:  # 내 일정만 보기가 활성화된 경우
            should_show_event = date in self.my_dates
        elif hasattr(self, 'filtered_dates') and self.filtered_dates:  # 필터링된 날짜가 있는 경우
            should_show_event = date in self.filtered_dates
        else:  # 필터가 없는 경우
            should_show_event = date in self.dates_with_events

        # 일정이 있고 필터링되지 않은 경우에만 표시
        if should_show_event:
            all_completed = date in self.completed_dates
            triangle_color = QColor('gray') if all_completed else QColor('#B7F0B1')
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(triangle_color)
            
            points = [
                QPoint(rect.x() + rect.width(), rect.y()),
                QPoint(rect.x() + rect.width() - triangle_size, rect.y()),
                QPoint(rect.x() + rect.width(), rect.y() + triangle_size)
            ]
            painter.drawPolygon(points)
            
            # 텍스트 설정 및 그리기
            font = painter.font()
            font.setPointSize(14)
            font.setBold(True)
            font.setWeight(75)
            painter.setFont(font)
            
            text_rect = QRect(
                rect.x(),
                rect.y() + rect.height() - 25,
                rect.width(),
                13
            )
            
            path = QPainterPath()
            text = "선적 완료" if all_completed else "선적 예정"
            path.addText(
                text_rect.x() + (text_rect.width() - painter.fontMetrics().width(text)) / 2,
                text_rect.y() + painter.fontMetrics().ascent(),
                font,
                text
            )
            
            if all_completed:
                painter.setPen(QPen(QColor('#050099'), 1))
                painter.setBrush(QColor('yellow'))
            else:
                painter.setPen(QPen(QColor('#28a745'), 1))
                painter.setBrush(QColor('#B7F0B1'))
            
            painter.drawPath(path)

        # 선택된 날짜 표시
        if date == self.selectedDate():
            painter.setPen(QPen(QColor('#191919'), 5, Qt.SolidLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(
                rect.x() + 2,
                rect.y() + 2,
                rect.width() - 4,
                rect.height() - 4
            )




class EditEventsDialog(QDialog):
    def __init__(self, date, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.date = date
        self.selected_event = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('일정 편집')
        self.setGeometry(300, 300, 500, 400)
        layout = QVBoxLayout()

        # QListWidget으로 변경
        self.events_list = QListWidget()
        self.events_list.setDragDropMode(QListWidget.InternalMove)  # 드래그 앤 드롭 활성화
        self.events_list.setSelectionMode(QListWidget.SingleSelection)
        self.events_list.model().rowsMoved.connect(self.on_items_moved)
        
        # 스크롤 영역 설정
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.events_list)
        scroll.setStyleSheet("background-color: white;")

        # 버튼
        buttons_layout = QHBoxLayout()
        add_button = QPushButton('일정 추가')
        edit_button = QPushButton('수정')
        delete_button = QPushButton('선택 삭제')
        close_button = QPushButton('닫기')

        # 버튼 스타일 설정
        button_style = """
            QPushButton {
                color: black;
                background-color: #a7e255;
                border: none;
                padding: 5px 15px;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: #96cc4a;
            }
        """
        add_button.setStyleSheet(button_style)
        edit_button.setStyleSheet(button_style)
        delete_button.setStyleSheet(button_style)
        close_button.setStyleSheet(button_style)

        # 버튼 연결
        add_button.clicked.connect(self.add_new_event)
        edit_button.clicked.connect(self.edit_selected_event)
        delete_button.clicked.connect(self.delete_selected_events)
        close_button.clicked.connect(self.reject)

        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(edit_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addWidget(close_button)

        # 레이아웃에 위젯 추가
        layout.addWidget(scroll)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        self.load_events()

    def add_new_event(self):
        selected_date = self.parent.calendar.selectedDate().toPyDate().strftime('%Y-%m-%d')
        dialog = AddEventDialog(selected_date, self)
        if dialog.exec_() == QDialog.Accepted:
            self.parent.add_event(dialog.get_event_data())
            self.load_events()  # 일정 목록 새로고침




    def on_items_moved(self, parent, start, end, destination, row):
        # 이동된 순서대로 이벤트 ID와 순서 저장
        for i in range(self.events_list.count()):
            item = self.events_list.item(i)
            widget = self.events_list.itemWidget(item)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    event_id = checkbox.property('event_id')
                    if event_id:
                        # 데이터베이스의 display_order 업데이트
                        self.parent.cursor.execute('''
                            UPDATE events 
                            SET display_order = ? 
                            WHERE id = ?
                        ''', (i, event_id))
        
        self.parent.conn.commit()
        # 메인 창의 일정 목록 업데이트
        self.parent.show_events()        

    def load_events(self):
        self.events_list.clear()
        cursor = self.parent.cursor
        
        # admin 계정인 경우 모든 일정을 표시
        if self.parent.current_user == 'admin':
            cursor.execute('''
                SELECT id, title, time, description, status, created_by 
                FROM events 
                WHERE date = ? 
                ORDER BY display_order, time
            ''', (self.date,))
        else:
            # 일반 사용자는 자신이 만든 일정만 표시
            cursor.execute('''
                SELECT id, title, time, description, status, created_by 
                FROM events 
                WHERE date = ? AND created_by = ?
                ORDER BY display_order, time
            ''', (self.date, self.parent.current_user))
        
        events = cursor.fetchall()

        # 전체 일정 개수 표시
        count_item = QListWidgetItem(f'전체 일정: {len(events)}개')
        count_item.setFlags(count_item.flags() & ~Qt.ItemIsDragEnabled)  # 드래그 비활성화
        count_item.setBackground(QColor('#f0f0f0'))
        count_item.setForeground(QColor('black'))
        self.events_list.addItem(count_item)
        
        for event in events:
            item_widget = QWidget()
            item_layout = QHBoxLayout()
            item_layout.setContentsMargins(5, 5, 5, 5)
            
            # 상태에 따른 배경색 설정
            bg_color = '#B2EBF4' if event[4] == '예정' else '#D5D5D5'
            item_widget.setStyleSheet(f"background-color: {bg_color};")
                
            checkbox = QCheckBox()
            checkbox.setProperty('event_id', event[0])
            checkbox.setStyleSheet("""
                QCheckBox::indicator {
                    width: 13px;
                    height: 13px;
                    border: 2px solid #0078FF;
                }
                QCheckBox::indicator:unchecked {
                    background-color: transparent;
                }
                QCheckBox::indicator:checked {
                    background-color: #0078FF;
                }
            """)
            
            info_text = f"[{event[4]}] {event[1]}"
            if event[2]:
                info_text += f" - {event[2]}"
            if event[3]:
                info_text += f"\n설명: {event[3]}"
            info_text += f"\n작성자: {event[5]}"
            
            info_label = QLabel(info_text)
            info_label.setWordWrap(True)
            info_label.setStyleSheet("color: black;")

            item_layout.addWidget(checkbox)
            item_layout.addWidget(info_label)
            item_layout.addStretch()
            
            item_widget.setLayout(item_layout)
            
            list_item = QListWidgetItem()
            list_item.setSizeHint(item_widget.sizeHint())
            self.events_list.addItem(list_item)
            self.events_list.setItemWidget(list_item, item_widget)

    def edit_selected_event(self):
        selected_items = []
        for i in range(self.events_list.count()):
            item = self.events_list.item(i)
            widget = self.events_list.itemWidget(item)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    selected_items.append((item, checkbox.property('event_id')))

        if not selected_items:
            QMessageBox.warning(self, '경고', '수정할 일정을 선택하세요.')
            return
        
        if len(selected_items) > 1:
            QMessageBox.warning(self, '경고', '하나의 일정만 선택하세요.')
            return

        selected_item, event_id = selected_items[0]
        
        # 선택된 이벤트 정보 가져오기
        self.parent.cursor.execute('''
            SELECT title, description, created_by, created_time, status
            FROM events 
            WHERE id = ?
        ''', (event_id,))
        event = self.parent.cursor.fetchone()

        if event:
            # 권한 체크
            is_admin = self.parent.current_user == 'admin'
            is_creator = event[2] == self.parent.current_user
            has_permission = is_admin or is_creator

            if has_permission:
                # 수정 다이얼로그 표시
                dialog = AddEventDialog(self.date, self)
                dialog.setWindowTitle('일정 수정')

                self.parent.cursor.execute('''
                    SELECT visibility FROM events WHERE id = ?
                ''', (event_id,))
                visibility_data = self.parent.cursor.fetchone()
                
                if visibility_data and visibility_data[0]:
                    visible_depts = visibility_data[0].split(',')
                    # 전체 비공개인 경우
                    if visibility_data[0] == 'private':
                        dialog.private_check.setChecked(True)
                    else:
                        # 부서별 체크박스 설정
                        for dept, checkbox in dialog.dept_checks.items():
                            checkbox.setChecked(dept in visible_depts)
                
                # 기존 일정 정보 설정
                if event[0].startswith('[') and ']' in event[0]:
                    program = event[0][1:event[0].index(']')]
                    remaining = event[0][event[0].index(']')+1:].strip()
                    
                    index = dialog.program_combo.findText(program)
                    if index >= 0:
                        dialog.program_combo.setCurrentIndex(index)
                        
                        prefix = dialog.prefix_label.text()
                        if remaining.startswith(prefix):
                            number = remaining[len(prefix):].split()[0]
                            dialog.number_input.setText(number)
                            
                            if '본편' in remaining:
                                dialog.type_본편.setChecked(True)
                            elif 'ReTake' in remaining:
                                dialog.type_retake.setChecked(True)
                else:
                    dialog.manual_check.setChecked(True)
                    dialog.title_input.setText(event[0])

                dialog.description_input.setText(event[1] if event[1] else '')

                if dialog.exec_() == QDialog.Accepted:
                    updated_data = dialog.get_event_data()
                    self.parent.cursor.execute('''
                        UPDATE events 
                        SET title = ?, description = ?, status = ?, visibility = ?
                        WHERE id = ?
                    ''', (updated_data['title'], updated_data['description'], event[4], updated_data['visibility'], event_id))
                    self.parent.conn.commit()
                    self.load_events()
                    self.parent.show_events()
                    self.parent.update_calendar_events()
            else:
                QMessageBox.warning(self, '경고', '이 일정을 수정할 권한이 없습니다.')
        else:
            QMessageBox.warning(self, '경고', '선택한 일정 정보를 찾을 수 없습니다.')

    def delete_selected_events(self):
        selected_items = []
        for i in range(self.events_list.count()):
            item = self.events_list.item(i)
            widget = self.events_list.itemWidget(item)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    selected_items.append((item, checkbox.property('event_id')))

        if not selected_items:
            QMessageBox.warning(self, '경고', '삭제할 일정을 선택하세요.')
            return

        # 권한 체크
        can_delete = []
        for item, event_id in selected_items:
            self.parent.cursor.execute('SELECT created_by FROM events WHERE id = ?', (event_id,))
            created_by = self.parent.cursor.fetchone()[0]
            
            is_admin = self.parent.current_user == 'admin'
            is_creator = created_by == self.parent.current_user
            
            if is_admin or is_creator:
                can_delete.append(event_id)

        if not can_delete:
            QMessageBox.warning(self, '경고', '선택한 일정을 삭제할 권한이 없습니다.')
            return

        reply = QMessageBox.question(self, '일정 삭제', 
                                '선택한 일정을 삭제하시겠습니까?',
                                QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            for event_id in can_delete:
                self.parent.cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
            self.parent.conn.commit()
            
            self.load_events()
            self.parent.show_events()
            self.parent.update_calendar_events()

class AddEventDialog(QDialog):
    def __init__(self, date, parent=None):
        super().__init__(parent)
        self.date = date
        self.initUI()

    def initUI(self):
        self.setWindowTitle('일정 추가')
        self.setGeometry(300, 300, 400, 350)
        layout = QVBoxLayout()

        # 제목 선택 영역
        title_group = QWidget()
        title_layout = QHBoxLayout()
        title_group.setLayout(title_layout)

        # 콤보박스와 프리픽스 영역
        combo_prefix_layout = QHBoxLayout()
        
        # 콤보박스
        self.program_combo = QComboBox()
        self.program_combo.addItems(["BB", "TGN", "BM", "KOTH", "MS"])
        self.program_combo.currentTextChanged.connect(self.update_prefix)
        combo_prefix_layout.addWidget(self.program_combo)

        # 프리픽스 선택 콤보박스
        self.prefix_combo = QComboBox()
        self.prefix_combo.setFixedWidth(80)
        self.prefix_combo.hide()  # 초기에는 숨김
        combo_prefix_layout.addWidget(self.prefix_combo)
        
        # 프리픽스와 숫자 입력
        self.prefix_label = QLabel()
        self.number_input = QLineEdit()
        self.number_input.setFixedWidth(50)
        self.number_input.setPlaceholderText('번호')
        combo_prefix_layout.addWidget(self.prefix_label)
        combo_prefix_layout.addWidget(self.number_input)
        
        title_layout.addLayout(combo_prefix_layout)

        type_group = QWidget()
        type_layout = QHBoxLayout()
        self.type_본편 = QCheckBox('본편')
        self.type_retake = QCheckBox('ReTake')
        type_layout.addWidget(self.type_본편)
        type_layout.addWidget(self.type_retake)
        type_group.setLayout(type_layout)

        # 체크박스 상태 변경 시 다른 체크박스 해제
        self.type_본편.stateChanged.connect(lambda state: self.type_retake.setChecked(False) if state else None)
        self.type_retake.stateChanged.connect(lambda state: self.type_본편.setChecked(False) if state else None)

        title_layout.addWidget(type_group)

        # 직접 입력 옵션
        input_group = QWidget()
        input_layout = QVBoxLayout()
        input_group.setLayout(input_layout)

        self.manual_check = QCheckBox('직접 입력')
        self.manual_check.stateChanged.connect(self.toggle_manual_input)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText('일정 제목')
        self.title_input.setEnabled(False)

        input_layout.addWidget(self.manual_check)
        input_layout.addWidget(self.title_input)

        # 시간과 설명 입력
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText('일정 설명')

        visibility_group = QGroupBox("공개 설정")
        visibility_layout = QHBoxLayout()  # QVBoxLayout에서 QHBoxLayout으로 변

        # 전체 비공개 체크박스
        self.private_check = QCheckBox("전체 비공개")
        self.private_check.stateChanged.connect(self.toggle_private)
        visibility_layout.addWidget(self.private_check)
        
        # 부서별 체크박스
        self.dept_checks = {}
        departments = ['3D', '번역부', '제작부', '카메라', '시스템', '기타']
        for dept in departments:
            checkbox = QCheckBox(dept)
            checkbox.setChecked(True)  # 기본값은 모두 체크
            self.dept_checks[dept] = checkbox
            visibility_layout.addWidget(checkbox)
        
        visibility_group.setLayout(visibility_layout)
        layout.addWidget(visibility_group)

        # 버튼
        buttons_layout = QHBoxLayout()
        save_button = QPushButton('저장')
        cancel_button = QPushButton('취소')
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)

        # 레이아웃에 위젯 추가
        layout.addWidget(title_group)
        layout.addWidget(input_group)
        layout.addWidget(QLabel('설명:'))
        layout.addWidget(self.description_input)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        
        # 초기 프리픽스 설정
        self.update_prefix(self.program_combo.currentText())

    def toggle_private(self, state):
        # 전체 비공개 체크 시 모든 부서 체크박스 해제 및 비활성화
        for checkbox in self.dept_checks.values():
            checkbox.setChecked(not bool(state))
            checkbox.setEnabled(not bool(state))        

    def update_prefix(self, program):
        prefix_options = {
            'BB': ['EASA', 'FASA'],
            'TGN': ['5LBW', '6LBW'],
            'BM': ['BM_'],
            'MS': ['MS_'],
            'KOTH': ['']
        }
        
        self.prefix_combo.clear()
        self.prefix_combo.addItems(prefix_options[program])
        
        if program in ['BB', 'TGN']:
            self.prefix_combo.show()
        else:
            self.prefix_combo.hide()
            self.prefix_combo.setCurrentText(prefix_options[program][0])

    def toggle_manual_input(self, state):
        self.title_input.setEnabled(state == Qt.Checked)
        self.program_combo.setEnabled(state != Qt.Checked)
        self.number_input.setEnabled(state != Qt.Checked)
        self.type_본편.setEnabled(state != Qt.Checked)
        self.type_retake.setEnabled(state != Qt.Checked)

    def get_event_data(self):
        # 제목 생성
        if self.manual_check.isChecked():
            title = self.title_input.text()
        else:
            program = self.program_combo.currentText()
            prefix = self.prefix_combo.currentText() 
            number = self.number_input.text()
            type_str = ''
            if self.type_본편.isChecked():
                type_str = '[본편]'
            elif self.type_retake.isChecked():
                type_str = '[ReTake]'
                
            title = f'[{program}] {prefix}{number} {type_str}'

        # 부서별 공개 설정
        if hasattr(self, 'private_check') and self.private_check.isChecked():
            visibility = "private"
        else:
            visible_depts = []
            if hasattr(self, 'dept_checks'):
                for dept, cb in self.dept_checks.items():
                    if cb.isChecked():
                        visible_depts.append(dept)
            visibility = ",".join(visible_depts) if visible_depts else "private"

        return {
            'title': title,
            'description': self.description_input.toPlainText(),
            'date': self.date,
            'visibility': visibility
        }


class SchedulerApp(QMainWindow):
    def __init__(self, current_user=None, permissions=None):
        super().__init__()
        self.current_user = current_user
        self.permissions = permissions
        self.current_dept = None  # 부서 정보 초기화
    
        # 사용자 정보 파일에서 부서 정보 가져오기
        base_paths = [
            '/USA_DB/test_jn',
            '/System/Volumes/Data/mnt/USA_DB/test_jn',
            '/System/Volumes/Data/USA_DB/test_jn'
        ]
        
        for base_path in base_paths:
            users_file = os.path.join(base_path, 'scheduler_user.json')
            if os.path.exists(users_file):
                try:
                    with open(users_file, 'r') as f:
                        users = json.load(f)
                        if self.current_user in users:
                            self.current_dept = users[self.current_user]['group']
                            break
                except Exception as e:
                    print(f"사용자 정보 읽기 오류: {str(e)}")
        self.initDB()           # DB 초기화를 먼저
        self.initUI()
        self.setupTrayIcon()          # UI 초기화는 그 다음에
        self.show_initial_events()
        self.setupNotificationTimer()  # 타이머 설정 추가

        self.date_check_timer = QTimer(self)
        self.date_check_timer.timeout.connect(self.check_date)
        self.date_check_timer.start(60000)  # 1분마다 체크
        self.last_date = QDate.currentDate()

    def load_latest_notice(self):
        try:
            with self.conn:
                self.cursor.execute('''
                    SELECT content, created_by, created_time 
                    FROM notices 
                    ORDER BY created_time DESC 
                    LIMIT 1
                ''')
                result = self.cursor.fetchone()
                
                if result:
                    content, created_by, created_time = result
                    self.notice_label.setText(f"📢 공지사항: {content}\n작성자: {created_by} ({created_time})")
                    self.notice_label.show()
                else:
                    self.notice_label.hide()
        except Exception as e:
            print(f"공지사항 로드 오류: {str(e)}")        

    def check_date(self):
        current_date = QDate.currentDate()
        if current_date != self.last_date:
            self.go_to_today()
            self.last_date = current_date
                
    def get_username(self):
        return self.username_input.text()

    def setupTrayIcon(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon = QIcon('/USA_DB/test_jn/shipping.icns')
        self.tray_icon.setIcon(icon)
        self.setWindowIcon(icon)
        
        # 트레이 아이콘 메뉴
        tray_menu = QMenu()
        show_action = tray_menu.addAction("창 보이기")
        show_action.triggered.connect(self.show)
        quit_action = tray_menu.addAction("종료")
        quit_action.triggered.connect(QApplication.quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()        

    def show_initial_events(self):
        # 오늘 날짜의 이벤트를 표시
        today_date = QDate.currentDate().toPyDate().strftime('%Y-%m-%d')
        
        # 오늘 날짜를 캘린더에서 선택
        self.calendar.setSelectedDate(QDate.currentDate())
        
        # 오늘 날짜의 이벤트 표시
        self.show_events()    

    def initDB(self):
        base_paths = [
            '/USA_DB/test_jn',
            '/System/Volumes/Data/mnt/USA_DB/test_jn',
            '/System/Volumes/Data/USA_DB/test_jn'
        ]

        # lock 파일 확인 및 삭제
        for base_path in base_paths:
            lock_path = os.path.join(base_path, 'scheduler.db.lock')
            if os.path.exists(lock_path):
                try:
                    if os.path.isfile(lock_path):
                        os.remove(lock_path)
                    elif os.path.isdir(lock_path):
                        shutil.rmtree(lock_path)
                    print(f"Lock file removed: {lock_path}")
                except Exception as e:
                    print(f"Error removing lock file {lock_path}: {e}")
        
        # 데이터베이스 연결 초기화
        self.conn = None
        self.cursor = None
        
        # 실제 존재하는 경로 확인
        for base_path in base_paths:
            try:
                os.makedirs(base_path, exist_ok=True)  # 디렉토리가 없으면 생성
                db_path = os.path.join(base_path, 'scheduler.db')
                self.conn = sqlite3.connect(db_path, isolation_level=None)  # autocommit 모드
                self.conn.execute('PRAGMA journal_mode=WAL')  # WAL 모드 사용
                self.conn.execute('PRAGMA busy_timeout=5000')  # timeout 설정
                self.cursor = self.conn.cursor()
                break
            except (OSError, sqlite3.OperationalError) as e:
                print(f"Error with path {base_path}: {e}")
                continue
        
        if not self.conn or not self.cursor:
            # 모든 경로가 실패한 경우 현재 디렉토리에 생성
            db_path = 'scheduler.db'
            self.conn = sqlite3.connect(db_path, isolation_level=None)
            self.conn.execute('PRAGMA journal_mode=WAL')
            self.conn.execute('PRAGMA busy_timeout=5000')
            self.cursor = self.conn.cursor()

        try:
            with self.conn:
                # events 테이블 생성 (모든 컬럼 포함)
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        date TEXT NOT NULL,
                        time TEXT,
                        description TEXT,
                        status TEXT DEFAULT '예정',
                        display_order INTEGER DEFAULT 0,
                        created_by TEXT,
                        visibility TEXT DEFAULT 'all',
                        likes INTEGER DEFAULT 0,
                        created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_time TIMESTAMP,
                        admin_memo TEXT
                    )
                ''')

                # users 테이블 생성
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        user_group TEXT NOT NULL,
                        permissions TEXT NOT NULL
                    )
                ''')

                # notices 테이블 생성
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        content TEXT NOT NULL,
                        created_by TEXT NOT NULL,
                        created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                self.cursor.execute("PRAGMA table_info(notices)")
                notice_columns = [column[1] for column in self.cursor.fetchall()]

                # notices 테이블에 필요한 컬럼 추가
                if 'created_by' not in notice_columns:
                    self.cursor.execute('ALTER TABLE notices ADD COLUMN created_by TEXT NOT NULL DEFAULT "admin"')
                if 'created_time' not in notice_columns:
                    self.cursor.execute('ALTER TABLE notices ADD COLUMN created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP')

                # events 테이블 컬럼 확인 및 추가 (기존 코드)
                self.cursor.execute("PRAGMA table_info(events)")
                columns = [column[1] for column in self.cursor.fetchall()]

                # 컬럼 존재 여부 확인
                self.cursor.execute("PRAGMA table_info(events)")
                columns = [column[1] for column in self.cursor.fetchall()]

                # 컬럼 존재 여부 확인
                self.cursor.execute("PRAGMA table_info(events)")
                columns = [column[1] for column in self.cursor.fetchall()]

                # 필요한 컬럼 추가
                required_columns = {
                    'visibility': 'TEXT DEFAULT "all"',
                    'likes': 'INTEGER DEFAULT 0',
                    'created_by': 'TEXT',
                    'created_time': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                    'completed_time': 'TIMESTAMP',
                    'admin_memo': 'TEXT',
                    'display_order': 'INTEGER DEFAULT 0'
                }

                for column, type_def in required_columns.items():
                    if column not in columns:
                        self.cursor.execute(f'ALTER TABLE events ADD COLUMN {column} {type_def}')
                        if column == 'created_by':
                            self.cursor.execute("UPDATE events SET created_by = 'default_user' WHERE created_by IS NULL")

        finally:
            self.cursor.close()
            self.cursor = self.conn.cursor()



    def initUI(self):
        self.setWindowTitle('Yeson 스케줄러 -v9.6')
        self.setGeometry(100, 100, 1500, 900) 

        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)
        menu_bar.setNativeMenuBar(False)

        # File 메뉴 추가 (현재 사용자 표시)
        file_menu = menu_bar.addMenu(f"- User: {self.current_user}")

        # admin 계정일 때만 관리 메뉴 추가
        if self.current_user == 'admin':
            admin_menu = menu_bar.addMenu('관리')
            user_action = QAction('사용자 관리', self)
            user_action.triggered.connect(self.show_user_management)
            admin_menu.addAction(user_action)

            notice_action = QAction('공지사항 작성', self)
            notice_action.triggered.connect(self.show_notice_management)
            admin_menu.addAction(notice_action)        

        # 파일 메뉴 추가
        file_menu = menu_bar.addMenu('파일')
        print_action = QAction('프린터', self)
        print_action.triggered.connect(self.print_scheduler)
        file_menu.addAction(print_action)            

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_widget.setStyleSheet("background-color: #f0f0f0;")
        
        # 전체 레이아웃 설정
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 공지사항 레이블 생성 및 설정
        self.notice_label = QLabel()
        self.notice_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 5px;
                padding: 8px;
                margin: 5px;
                color: #495057;
                font-size: 13px;
            }
        """)
        main_layout.addWidget(self.notice_label)

        self.load_latest_notice()
        
        # 캘린더와 이벤트를 위한 수평 레이아웃
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)

        # 왼쪽 패널 (캘린더)
        left_panel = QWidget()
        left_panel.setStyleSheet("background-color: #f0f0f0;")
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)

        # 캘린더 위젯 설정
        self.calendar = CustomCalendarWidget()
        self.calendar.clicked.connect(self.show_events)
        self.calendar.setContextMenuPolicy(Qt.CustomContextMenu)
        self.calendar.customContextMenuRequested.connect(self.show_context_menu)

        self.calendar.currentPageChanged.connect(self.on_month_changed)
        self.calendar.activated.connect(self.handle_date_activated)
        
        # 캘린더 크기 설정
        self.calendar.setMinimumSize(600, 400)
        
        # 캘린더 헤더 설정
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.LongDayNames)
        self.calendar.setGridVisible(True)
        
        # 한글 로케일 설정
        korean_locale = QLocale(QLocale.Korean)
        self.calendar.setLocale(korean_locale)

        self.calendar.setStyleSheet("""
            /* 전체 캘린더 스타일 */
            QCalendarWidget {
                background-color: white;
            }
            /* 네비게이션 바 스타일 */
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #e8f5e9;
                padding: 5px;
            }
            /* 화살표 버튼 스타일 */
            QCalendarWidget QToolButton#qt_calendar_prevmonth,
            QCalendarWidget QToolButton#qt_calendar_nextmonth {
                padding: 5px;
                margin: 0 30px;
                color: black;
                background: transparent;
            }
            /* 달력 날짜 테이블 스타일 */
            QCalendarWidget QTableView {
                background-color: white;
                selection-background-color: transparent;
                selection-color: black;
                color: black;
                border: none;
            }
            /* 선택된 날짜 셀 스타일 */
            QCalendarWidget QTableView::item:selected {
                border: 3px solid #5CD1E5;
                background-color: transparent;
            }
            /* 날짜 셀 pressed 효과 */
            QCalendarWidget QTableView::item:pressed {
                border: 3px solid #5CD1E5;
                background-color: transparent;
            }
            /* 날짜 셀 hover 효과 */
            QCalendarWidget QTableView::item:hover {
                border: 2px solid #5CD1E5;
                background-color: transparent;
            }
            QCalendarWidget QWidget { 
                alternate-background-color: #BDBDBD;
            }
            QCalendarWidget QAbstractItemView:section {
                background-color: #BDBDBD;
                color: black;
            }
            QCalendarWidget QTableView QHeaderView::section {
                background-color: #BDBDBD;
                color: black;
                padding: 5px;
                border: 1px solid #cccccc;
            }
            /* 월/년 선택 버튼 스타일 */
            QCalendarWidget QToolButton {
                color: black;
                background: transparent;
                padding: 0px 15px;
                border-radius: 8px;
                margin: 0 5px;
            }
            /* 월 드롭다운 메뉴 스타일 */
            QCalendarWidget QMenu {
                color: black;
                background-color: white;
                border: 1px solid #ccc;
            }
            /* 년도 스핀박스 스타일 */
            QCalendarWidget QSpinBox {
                color: black;
                background: transparent;
                padding: 3px;
            }
            /* 이전/다음 달 날짜 스타일 */
            QCalendarWidget QTableView:disabled {
                color: #aaaaaa;
            }
            /* 셀 테두리 스타일 */
            QCalendarWidget QTableView::item {
                border: 1px solid #cccccc;
            }
        """)
        # 일요일 - 빨간색
        sunday_format = self.calendar.weekdayTextFormat(Qt.Sunday)
        sunday_format.setForeground(QColor(255, 0, 0))
        self.calendar.setWeekdayTextFormat(Qt.Sunday, sunday_format)
        
        # 토요일 - 파란색
        saturday_format = self.calendar.weekdayTextFormat(Qt.Saturday)
        saturday_format.setForeground(QColor(0, 0, 255))
        self.calendar.setWeekdayTextFormat(Qt.Saturday, saturday_format)

        left_layout.addWidget(self.calendar)
       
        # 오른쪽 패널 (일정 목록)
        right_panel = QWidget()
        right_panel.setStyleSheet("background-color: #f0f0f0;")
        right_layout = QVBoxLayout(right_panel)

        # 헤더 위젯 (검색 영역)
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)

        # 검색 라벨과 검색창
        search_label = QLabel('일정 검색:')
        search_label.setStyleSheet("color: black; font-size: 13pt; padding-right: 5px;")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('일정 검색...')
        self.search_input.setFixedWidth(200)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 15px;
                background-color: white;
                color: black;
            }
            QLineEdit:focus {
                border: 1px solid #5CD1E5;
            }
        """)
        self.search_input.textChanged.connect(self.search_events)
        self.search_input.returnPressed.connect(lambda: self.search_events(self.search_input.text()))

        # 세부 검색창 설정
        self.detail_search_input = QLineEdit()
        self.detail_search_input.setPlaceholderText('결과 내 검색...')
        self.detail_search_input.setFixedWidth(200)
        self.detail_search_input.setStyleSheet(self.search_input.styleSheet())
        self.detail_search_input.hide()
        self.detail_search_input.textChanged.connect(self.detail_search)

        # 체크박스들
        self.detail_search_check = QCheckBox('세부검색')
        self.detail_search_check.setStyleSheet("QCheckBox {color: black; font-size: 12px; padding-left: 10px;}")
        self.detail_search_check.stateChanged.connect(self.toggle_detail_search)

        # 버튼들
        today_button = QPushButton('오늘로 →')
        refresh_button = QPushButton('새로고침')
        for button in [today_button, refresh_button]:
            button.setFixedSize(70, 30)
            
        today_button.setStyleSheet("""
            QPushButton {
                color: black;
                background-color: #5CD1E5;
                border: none;
                font-size: 12px;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: #4BA3B3;
            }
        """)
        refresh_button.setStyleSheet("""
            QPushButton {
                color: black;
                background-color: #a7e255;
                border: none;
                font-size: 12px;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: #96cc4a;
            }
        """)
        today_button.clicked.connect(self.go_to_today)
        refresh_button.clicked.connect(self.refresh_events)

        # 헤더 레이아웃에 위젯 추가
        header_layout.addWidget(search_label)
        header_layout.addWidget(self.search_input)
        header_layout.addWidget(self.detail_search_input)
        header_layout.addWidget(self.detail_search_check)
        header_layout.addStretch()
        header_layout.addWidget(today_button)
        header_layout.addWidget(refresh_button)

        # 일정 카운트 및 필터 레이아웃
        count_layout = QHBoxLayout()

        # 일정 개수 표시
        current_date = self.calendar.selectedDate().toPyDate().strftime('%Y-%m-%d')
        self.cursor.execute('SELECT DISTINCT id FROM events WHERE date = ? AND title IS NOT NULL', (current_date,))
        events_count = len(self.cursor.fetchall())
        self.count_label = QLabel(f'전체 일정: {events_count}개')
        self.count_label.setStyleSheet("color: black; padding: 0px 5px; margin: 0px; font-size: 12px;")
        count_layout.addWidget(self.count_label)
        count_layout.addStretch()

        # 작품 타입 필터
        type_filter_layout = QHBoxLayout()
        self.type_filters = {}
        for event_type in ['BB', 'TGN', 'BM', 'KOTH', 'MS']:
            checkbox = QCheckBox(event_type)
            checkbox.setStyleSheet("""
                QCheckBox {
                    color: black;
                    font-size: 12px;
                    padding: 5px;
                }
                QCheckBox:hover {
                    color: #5CD1E5;
                }
            """)
            checkbox.stateChanged.connect(self.show_events)
            self.type_filters[event_type] = checkbox
            type_filter_layout.addWidget(checkbox)
        count_layout.addLayout(type_filter_layout)
        count_layout.addStretch()

        # 추가 필터 체크박스
        # 체크박스 생성 부분을 다음과 같이 수정
        self.my_events_check = QCheckBox('내가 쓴 일정만 보기')
        self.planned_events_check = QCheckBox('예정 일정만 보기')

        for checkbox in [self.my_events_check, self.planned_events_check]:
            checkbox.setStyleSheet("""
                QCheckBox {
                    color: black;
                    font-size: 12px;
                    padding: 5px;
                }
                QCheckBox:hover {
                    color: #5CD1E5;
                }
            """)
            checkbox.stateChanged.connect(self.show_events)
            count_layout.addWidget(checkbox)


        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #cccccc;")

        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setStyleSheet("background-color: #f0f0f0;")
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: #f0f0f0;")
        self.events_layout = QVBoxLayout(scroll_content)
        scroll.setWidget(scroll_content)

        # 오른쪽 패널에 모든 위젯 추가
        right_layout.addWidget(header_widget)
        right_layout.addLayout(count_layout)
        right_layout.addWidget(line)
        right_layout.addWidget(scroll)

        # 메인 레이아웃에 패널 추가
        content_layout.addWidget(left_panel)
        content_layout.addWidget(right_panel)

    def show_notice_management(self):
        try:
            # NoticeDialog 호출 시 notice_id 매개변수 제거
            dialog = NoticeDialog(self)  # self만 전달
            if dialog.exec_() == QDialog.Accepted:
                self.load_latest_notice()
        except Exception as e:
            QMessageBox.critical(self, '오류', f'공지사항 관리 중 오류가 발생했습니다: {str(e)}')


        
    def save_notice(self):
        content = self.content_input.toPlainText().strip()
        
        if not content:
            QMessageBox.warning(self, '경고', '내용을 입력해주세요.')
            return
            
        try:
            with self.parent.conn:
                if self.notice_id:  # 수정
                    self.parent.cursor.execute('''
                        UPDATE notices 
                        SET content = ?, created_by = ?, created_time = datetime('now', 'localtime')
                        WHERE id = ?
                    ''', (content, self.parent.current_user, self.notice_id))
                else:  # 새로 작성
                    self.parent.cursor.execute('''
                        INSERT INTO notices (content, created_by, created_time)
                        VALUES (?, ?, datetime('now', 'localtime'))
                    ''', (content, self.parent.current_user))
            
            QMessageBox.information(self, '알림', '공지사항이 저장되었습니다.')
            self.parent.load_latest_notice()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, '오류', f'공지사항 저장 중 오류가 발생했습니다: {str(e)}')        

    def print_scheduler(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOrientation(QPrinter.Landscape)  # 가로 방향 설정
        printer.setPageSize(QPrinter.A4)  # A4 용지 크기
        
        # 프린트 미리보기 다이얼로그 생성
        preview = QPrintPreviewDialog(printer, self)
        preview.setWindowTitle("인쇄 미리보기")
        preview.setWindowState(Qt.WindowMaximized)  # 최대화된 창으로 표시
        
        # 미리보기 창에서 인쇄 버튼 클릭시 실행될 함수
        def on_preview(printer):
            painter = QPainter()
            painter.begin(printer)
            
            # 창 크기를 프린터 페이지에 맞게 조정
            scale_factor = min(printer.pageRect().width() / self.width(),
                            printer.pageRect().height() / self.height())
            painter.scale(scale_factor, scale_factor)
            
            # 현재 창을 프린터로 렌더링
            self.render(painter)
            painter.end()
    
        preview.paintRequested.connect(on_preview)
        preview.exec_()

          
    def go_to_today(self):
        today = QDate.currentDate()
        self.calendar.setSelectedDate(today)
        self.show_events()

    def toggle_detail_search(self, state):
        self.detail_search_input.setVisible(state == Qt.Checked)
        if not state:
            self.detail_search_input.clear()
            self.show_events()

    def toggle_result_search(self, state):
        if state and self.search_input.text():
            self.detail_search(self.detail_search_input.text())
        elif self.detail_search_input.text():
            self.search_events(self.search_input.text())

    def detail_search(self, keyword):
        if not keyword:
            self.search_events(self.search_input.text())
            return
            
        # 현재 표시된 결과 내에서 검색
        for i in reversed(range(self.events_layout.count())):
            widget = self.events_layout.itemAt(i).widget()
            if widget:
                should_hide = True
                for child in widget.findChildren(QLabel):
                    if keyword.lower() in child.text().lower():
                        should_hide = False
                        break
                widget.setVisible(not should_hide)
            
        

    def search_events(self, keyword):
        try:
            with self.conn:
                if not keyword:
                    self.show_events()
                    return
                    
                query = '''
                    SELECT id, title, date, description, status, created_by 
                    FROM events 
                    WHERE (title LIKE ? OR description LIKE ? OR date LIKE ?)
                '''
                
                # 기본 파라미터
                params = [
                    f'%{keyword}%', 
                    f'%{keyword}%', 
                    f'%{keyword}%'
                ]

                selected_types = [type_name for type_name, checkbox in self.type_filters.items() 
                            if checkbox.isChecked()]
                if selected_types:
                    type_conditions = []
                    for type_name in selected_types:
                        type_conditions.append(f"title LIKE '%[{type_name}]%'")
                    query += f" AND ({' OR '.join(type_conditions)})"
                
                # 내가 쓴 일정만 보기가 체크된 경우
                if self.my_events_check.isChecked():
                    query += ' AND created_by = ?'
                    params.append(self.current_user)
                else:
                    # 일반적인 권한 체크
                    query += ''' AND (
                        created_by = ? OR 
                        visibility = 'all' OR 
                        visibility LIKE ? OR
                        ? = 'admin'
                    )'''
                    params.extend([
                        self.current_user,
                        f"%{self.current_dept}%",
                        self.current_user
                    ])

                if self.planned_events_check.isChecked():
                    query += ' AND status = ?'
                    params.append('예정')        
                
                query += ' ORDER BY date'
                
                self.cursor.execute(query, params)
                events = self.cursor.fetchall()
                
                # 기존 이벤트 위젯 제거
                for i in reversed(range(self.events_layout.count())):
                    item = self.events_layout.itemAt(i)
                    if item is not None:
                        widget = item.widget()
                        if widget is not None:
                            widget.setParent(None)
                        else:
                            self.events_layout.removeItem(item)
                
                # 완료 리스트 파일 검색
                list_results = []
                base_paths = [
                    '/USA_DB/test_jn/ship_list',
                    '/System/Volumes/Data/mnt/USA_DB/test_jn/ship_list'
                ]
                
                for base_path in base_paths:
                    if not os.path.exists(base_path):
                        continue
                        
                    for filename in os.listdir(base_path):
                        try:
                            program_match = re.search(r'(BB|TGN|BM|KOTH|MS)-', filename)
                            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
                            
                            if program_match and date_match:
                                date = date_match.group(1)
                                program = program_match.group(1)

                                if selected_types and program not in selected_types:
                                    continue
                                
                                # 권한 체크 쿼리 구성
                                auth_query = '''
                                    SELECT visibility 
                                    FROM events 
                                    WHERE date = ? 
                                    AND title LIKE ?
                                '''
                                auth_params = [date, f'%{program}%']
                                
                                # 내가 쓴 일정만 보기가 체크된 경우
                                if self.my_events_check.isChecked():
                                    auth_query += ' AND created_by = ?'
                                    auth_params.append(self.current_user)
                                else:
                                    auth_query += ''' AND (
                                        created_by = ? OR 
                                        visibility = 'all' OR 
                                        visibility LIKE ? OR
                                        visibility IS NULL
                                    )'''
                                    auth_params.extend([
                                        self.current_user,
                                        f"%{self.current_dept}%"
                                    ])
                                
                                # 예정 일정만 보기가 체크된 경우
                                if self.planned_events_check.isChecked():
                                    auth_query += ' AND status = ?'
                                    auth_params.append('예정')
                                
                                self.cursor.execute(auth_query, auth_params)
                                
                                if self.cursor.fetchone():
                                    with open(os.path.join(base_path, filename), 'r', encoding='utf-8') as f:
                                        content = f.read()
                                        if keyword.lower() in content.lower():
                                            list_results.append({
                                                'filename': filename,
                                                'date': date,
                                                'content': content
                                            })
                        except Exception as e:
                            print(f"파일 읽기 오류: {str(e)}")
                
                # 일정 검색 결과 표시
                for event in events:
                    event_widget = QWidget()
                    event_widget.setFixedHeight(150)
                    event_layout = QVBoxLayout()
                    
                    # 제목 표시
                    title_text = f"[{event[4]}] {event[1]}"
                    title_label = QLabel()
                    title_label.setText(title_text.replace(
                        keyword, 
                        f'<span style="background-color: yellow;">{keyword}</span>'
                    ))
                    title_label.setTextFormat(Qt.RichText)
                    title_label.setStyleSheet("color: black; font-weight: bold; font-size: 13pt;")
                    
                    # 설명 표시
                    if event[3]:
                        desc_text = f"설명: {event[3]}"
                        desc_label = QLabel()
                        desc_label.setText(desc_text.replace(
                            keyword,
                            f'<span style="background-color: yellow;">{keyword}</span>'
                        ))
                        desc_label.setTextFormat(Qt.RichText)
                        desc_label.setWordWrap(True)
                        desc_label.setStyleSheet("color: black;")
                    
                    # 날짜 표시
                    date_text = f"날짜: {event[2]} (작성자: {event[5]})"
                    date_label = QLabel(date_text)
                    date_label.setStyleSheet("color: gray;")
                    
                    event_layout.addWidget(title_label)
                    if event[3]:
                        event_layout.addWidget(desc_label)
                    event_layout.addWidget(date_label)
                    
                    event_widget.mousePressEvent = lambda e, date=event[2]: self.go_to_date(date)
                    event_widget.setLayout(event_layout)
                    event_widget.setStyleSheet("""
                        QWidget {
                            background-color: white;
                            border: 1px solid #cccccc;
                            border-radius: 5px;
                            padding: 10px;
                        }
                        QWidget:hover {
                            background-color: #f0f0f0;
                        }
                    """)
                    
                    self.events_layout.addWidget(event_widget)
                
                # 완료 리스트 검색 결과 표시
                for result in list_results:
                    list_widget = QWidget()
                    list_widget.setFixedHeight(150)
                    list_layout = QVBoxLayout()
                    
                    # 파일명 표시
                    file_label = QLabel(f"완료 리스트: {result['filename']}")
                    file_label.setStyleSheet("color: black; font-weight: bold; font-size: 13pt;")
                    
                    # 내용 미리보기
                    preview_text = result['content'][:200].replace(
                        keyword,
                        f'<span style="background-color: yellow;">{keyword}</span>'
                    )
                    preview_label = QLabel(preview_text + "...")
                    preview_label.setTextFormat(Qt.RichText)
                    preview_label.setWordWrap(True)
                    preview_label.setStyleSheet("color: black;")
                    
                    # 날짜 표시
                    date_label = QLabel(f"날짜: {result['date']}")
                    date_label.setStyleSheet("color: gray;")
                    
                    list_layout.addWidget(file_label)
                    list_layout.addWidget(preview_label)
                    list_layout.addWidget(date_label)
                    
                    list_widget.mousePressEvent = lambda e, date=result['date']: self.go_to_date(date)
                    list_widget.setLayout(list_layout)
                    list_widget.setStyleSheet("""
                        QWidget {
                            background-color: #FFE4B5;
                            border: 1px solid #cccccc;
                            border-radius: 5px;
                            padding: 10px;
                        }
                        QWidget:hover {
                            background-color: #FFD700;
                        }
                    """)
                    
                    self.events_layout.addWidget(list_widget)

        
        finally:
            self.cursor.close()
            self.cursor = self.conn.cursor()            

    def open_list_file_direct(self, filename):
        for base_path in ['/USA_DB/test_jn/ship_list',
                        '/System/Volumes/Data/mnt/USA_DB/test_jn/ship_list',
                        '/System/Volumes/Data/USA_DB/test_jn/ship_list']:
            file_path = os.path.join(base_path, filename)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    dialog = QDialog(self)
                    dialog.setWindowTitle(f"완료 리스트 - {filename}")
                    dialog.setGeometry(100, 100, 600, 400)
                    layout = QVBoxLayout()
                    text_edit = QTextEdit()
                    text_edit.setPlainText(content)
                    text_edit.setReadOnly(True)
                    layout.addWidget(text_edit)
                    dialog.setLayout(layout)
                    dialog.exec_()
                    return
                except Exception as e:
                    print(f"파일 읽기 오류: {str(e)}")
        

    def go_to_date(self, date_str):
        # 선택한 날짜로 이동
        selected_date = QDate.fromString(date_str, "yyyy-MM-dd")
        self.calendar.setSelectedDate(selected_date)
        self.calendar.setCurrentPage(selected_date.year(), selected_date.month())
        self.search_input.clear()        
        self.show_events()

    def show_user_management(self):
        dialog = UserManagementDialog(self)
        dialog.exec_()          

    def show_current_events(self):
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%H:%M')
        
        # 현재 날짜의 모든 일정 조회
        self.cursor.execute('''
            SELECT title, time, status 
            FROM events 
            WHERE date = ? 
            ORDER BY time
        ''', (current_date,))
        
        events = self.cursor.fetchall()
        
        if not events:
            # 알림 데이터베이스에 저장
            self.cursor.execute('''
                INSERT INTO notifications (title, message, time, date, sent)
                VALUES (?, ?, ?, ?, 0)
            ''', ('일정 알림', '오늘 예정된 일정이 없습니다.', current_time, current_date))
            self.conn.commit()
            return
        
        # 일정 목록 생성
        event_list = ""
        for event in events:
            event_list += f"[{event[2]}] {event[0]}"
            if event[1]:
                event_list += f" - {event[1]}"
            event_list += "\n"
        
        # 알림 데이터베이스에 저장
        self.cursor.execute('''
            INSERT INTO notifications (title, message, time, date, sent)
            VALUES (?, ?, ?, ?, 0)
        ''', ('오늘의 일정', event_list, current_time, current_date))
        self.conn.commit()


    def refresh_events(self):
        # 데이터베이스 연결 갱신
        self.conn.commit()

        self.load_latest_notice()
        
        # 캘린더의 이벤트 표시만 업데이트
        self.update_calendar_events()
        
        # 검색 중이 아닐 때만 일정 목록 새로고침
        if not self.search_input.text():
            # 현재 선택된 날짜의 일정 수 다시 조회
            current_date = self.calendar.selectedDate().toPyDate().strftime('%Y-%m-%d')
            self.cursor.execute('''
                SELECT DISTINCT id, title, time, description, status 
                FROM events 
                WHERE date = ? AND title IS NOT NULL
                ORDER BY display_order, time
            ''', (current_date,))
            events = self.cursor.fetchall()
            
            # 일정 개수 레이블 업데이트
            self.count_label.setText(f'전체 일정: {len(events)}개')
            
            # 현재 선택된 날짜의 이벤트를 다시 불러옴
            self.show_events()



    def handle_date_activated(self, date):
        selected_date = date.toPyDate().strftime('%Y-%m-%d')
        
        # 권한이 있는 일정이 있는지 확인
        self.cursor.execute('''
            SELECT COUNT(*) FROM events 
            WHERE date = ? AND (
                created_by = ? OR 
                visibility = 'all' OR 
                visibility LIKE ? OR
                ? = 'admin'
            )
        ''', (
            selected_date,
            self.current_user,
            f"%{self.current_dept}%",
            self.current_user
        ))
        event_count = self.cursor.fetchone()[0]
        
        # 권한이 있는 일정이 있으면 편집창 표시
        if event_count > 0:
            dialog = EditEventsDialog(selected_date, self)
            dialog.exec_()
        # 일정이 없고 일정 추가 권한이 있는 경우 추가창 표시
        elif self.permissions.get('permissions', {}).get('context_menu_add', False):
            dialog = AddEventDialog(selected_date, self)
            if dialog.exec_() == QDialog.Accepted:
                self.add_event(dialog.get_event_data())




    def show_context_menu(self, pos):   
        menu = QMenu(self)
        selected_date = self.calendar.selectedDate().toPyDate().strftime('%Y-%m-%d')
        
        # 일정 추가 메뉴
        if self.permissions.get('permissions', {}).get('context_menu_add', False):
            add_action = menu.addAction('일정 추가')
        
        # 일정이 있는지 확인
        self.cursor.execute('''
            SELECT COUNT(*) FROM events 
            WHERE date = ? AND created_by = ?
        ''', (selected_date, self.current_user))
        user_event_count = self.cursor.fetchone()[0]
        
        # 일정이 있으면 편집 메뉴 표시 (권한 체크는 EditEventsDialog 내에서 처리)
        if user_event_count > 0 or self.current_user == 'admin':
            dit_action = menu.addAction('일정 편집')
        
        if menu.isEmpty():
            return
                
        action = menu.exec_(self.calendar.mapToGlobal(pos))

        if action == add_action if 'add_action' in locals() else None:
            dialog = AddEventDialog(selected_date, self)
            if dialog.exec_() == QDialog.Accepted:
                self.add_event(dialog.get_event_data())
        elif action == edit_action if 'edit_action' in locals() else None:
            dialog = EditEventsDialog(selected_date, self)
            dialog.exec_()

    def on_month_changed(self, year, month):
        # 월이 변경될 때마다 캘린더 이벤트 업데이트
        self.update_calendar_events()            

    def add_event(self, event_data):
        try:
            with self.conn:
                # 일정 추가
                self.cursor.execute('''
                    INSERT INTO events (
                        title, date, description, status, created_by, 
                        created_time, visibility
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event_data['title'],
                    event_data['date'],
                    event_data['description'],
                    '예정',
                    self.current_user,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    event_data['visibility']
                ))
                
                # 현재 선택된 날짜의 일정 수 조회
                current_date = self.calendar.selectedDate().toPyDate().strftime('%Y-%m-%d')
                self.cursor.execute('''
                    SELECT id, title, description, status, created_by, created_time
                    FROM events 
                    WHERE date = ? AND title IS NOT NULL
                    ORDER BY display_order
                ''', (current_date,))
                events = self.cursor.fetchall()
                
                # 일정 개수 레이블 업데이트
                self.count_label.setText(f'전체 일정: {len(events)}개')
        finally:
            self.cursor.close()
            self.cursor = self.conn.cursor()
        
        # 캘린더 날짜 설정
        new_date = QDate.fromString(event_data['date'], "yyyy-MM-dd")
        self.calendar.setSelectedDate(new_date)
        self.calendar.setCurrentPage(new_date.year(), new_date.month())
        
        # UI 업데이트
        self.show_events()
        self.update_calendar_events()




    def update_calendar_events(self):
        try:
            with self.conn:
                # 현재 표시된 월의 첫째 날과 마지막 날 구하기
                current_page = self.calendar.monthShown()
                current_year = self.calendar.yearShown()
                first_day = QDate(current_year, current_page, 1)
                last_day = first_day.addMonths(1).addDays(-1)

                # 모든 날짜 포맷 초기화
                for day in range(first_day.daysTo(last_day) + 1):
                    date = first_day.addDays(day)
                    self.calendar.setDateTextFormat(date, QTextCharFormat())

                # 해당 월의 모든 일정이 있는 날짜 조회
                query = '''
                    SELECT date, COUNT(*) as total_count, 
                    SUM(CASE WHEN status = '완료' THEN 1 ELSE 0 END) as completed_count
                    FROM events 
                    WHERE date BETWEEN ? AND ? 
                    AND (
                        created_by = ? OR 
                        visibility = 'all' OR 
                        visibility LIKE ? OR
                        ? = 'admin'
                    )
                    GROUP BY date
                '''
                
                params = [
                    first_day.toString('yyyy-MM-dd'),
                    last_day.toString('yyyy-MM-dd'),
                    self.current_user,
                    f"%{self.current_dept}%",
                    self.current_user
                ]

                self.cursor.execute(query, params)
                results = self.cursor.fetchall()
                
                dates_with_events = set()
                completed_dates = set()
                
                for date_str, total, completed in results:
                    date = QDate.fromString(date_str, "yyyy-MM-dd")
                    if total > 0:
                        dates_with_events.add(date)
                    if total == completed and total > 0:
                        completed_dates.add(date)

                self.calendar.setDatesWithEvents(dates_with_events, completed_dates)
        finally:
            self.cursor.close()
            self.cursor = self.conn.cursor()


    def update_event_status(self, event_id, new_status):
        try:
            with self.conn:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                if new_status == '완료':
                    # 완료 상태로 변경할 때 created_time을 현재 시간으로 업데이트
                    self.cursor.execute('''
                        UPDATE events 
                        SET status = ?,
                            created_time = ?
                        WHERE id = ?
                    ''', (new_status, current_time, event_id))
                else:
                    # 예정 상태로 변경할 때는 시간 변경 없음
                    self.cursor.execute('''
                        UPDATE events 
                        SET status = ?
                        WHERE id = ?
                    ''', (new_status, event_id))
        finally:
            self.cursor.close()
            self.cursor = self.conn.cursor()
        
        # UI 업데이트는 데이터베이스 작업 완료 후 실행
        self.show_events()
        self.update_calendar_events()



    def show_events(self):
        try:
            with self.conn:
                selected_date = self.calendar.selectedDate().toPyDate().strftime('%Y-%m-%d')
                # 기존 이벤트 위젯들을 제거
                for i in reversed(range(self.events_layout.count())):
                    item = self.events_layout.itemAt(i)
                    if item is not None:
                        widget = item.widget()
                        if widget is not None:
                            widget.setParent(None)
                        else:
                            self.events_layout.removeItem(item)

                query = '''
                    SELECT id, title, time, description, status, created_by, created_time, completed_time, date
                    FROM events 
                    WHERE date = ?
                '''
                params = [selected_date]

                selected_types = [type_name for type_name, checkbox in self.type_filters.items() 
                            if checkbox.isChecked()]
                if selected_types:
                    type_conditions = []
                    for type_name in selected_types:
                        type_conditions.append(f"title LIKE '%[{type_name}]%'")
                    query += f" AND ({' OR '.join(type_conditions)})"
                    
                    # 선택된 타입의 일정이 있는 날짜와 상태 확인
                    calendar_query = '''
                        SELECT date,
                            COUNT(*) as total_count,
                            SUM(CASE WHEN status = '완료' THEN 1 ELSE 0 END) as completed_count
                        FROM events
                        WHERE ''' + ' OR '.join([f"title LIKE '%[{t}]%'" for t in selected_types]) + '''
                        GROUP BY date
                    '''
                    
                    self.cursor.execute(calendar_query)
                    calendar_dates = self.cursor.fetchall()
                    
                    filtered_dates = set()
                    completed_dates = set()
                    for date_info in calendar_dates:
                        date = QDate.fromString(date_info[0], 'yyyy-MM-dd')
                        filtered_dates.add(date)
                        # 해당 날짜의 모든 일정이 완료된 경우에만 completed_dates에 추가
                        if date_info[1] == date_info[2] and date_info[1] > 0:
                            completed_dates.add(date)
                    
                    self.calendar.setDatesWithEvents(filtered_dates, completed_dates)
                    self.calendar.setShowMyEvents(True)
                else:
                    # 체크박스가 모두 해제된 경우 모든 일정 표시
                    self.calendar.setShowMyEvents(False)
                    self.update_calendar_events()  # 전체 일정 업데이트

                # 내가 쓴 일정만 보기가 체크된 경우
                if self.my_events_check.isChecked():
                    query += ' AND created_by = ?'
                    params.append(self.current_user)
                    
                    # 달력 업데이트를 위한 날짜 설정
                    calendar_query = '''
                        SELECT date, status FROM events 
                        WHERE created_by = ?
                    '''
                    self.cursor.execute(calendar_query, (self.current_user,))
                    calendar_dates = self.cursor.fetchall()
                    
                    my_dates = set()
                    completed_dates = set()
                    for date_info in calendar_dates:
                        my_dates.add(QDate.fromString(date_info[0], 'yyyy-MM-dd'))
                        if date_info[1] == '완료':
                            completed_dates.add(QDate.fromString(date_info[0], 'yyyy-MM-dd'))
                    
                    self.calendar.setMyDates(my_dates)
                    self.calendar.setShowMyEvents(True)
                else:
                    # 예정 일정만 보기가 체크된 경우
                    if self.planned_events_check.isChecked():
                        query += ' AND status = ?'
                        params.append('예정')
                        
                        # 예정 일정이 있는 날짜만 달력에 표시 (권한 체크 포함)
                        planned_query = '''
                            SELECT date FROM events 
                            WHERE status = ? AND (
                                created_by = ? OR 
                                visibility = 'all' OR 
                                visibility LIKE ? OR
                                visibility IS NULL
                            )
                        '''
                        self.cursor.execute(planned_query, (
                            '예정',
                            self.current_user,
                            f"%{self.current_dept}%"
                        ))
                        planned_dates = {QDate.fromString(date[0], 'yyyy-MM-dd') for date in self.cursor.fetchall()}
                        self.calendar.setMyDates(planned_dates)
                        self.calendar.setShowMyEvents(True)
                    else:
                        selected_date = self.calendar.selectedDate().toPyDate().strftime('%Y-%m-%d')
                        query += ' AND date = ?'
                        params.append(selected_date)
                        self.calendar.setShowMyEvents(False)

                # 부서별 공개 설정 조건 추가
                if self.current_user != 'admin':  # admin이 아닌 경우에만 적용
                    query += ''' AND (
                        created_by = ? OR 
                        visibility = 'all' OR 
                        visibility LIKE ? OR
                        visibility IS NULL
                    )'''
                    params.extend([
                        self.current_user,
                        f"%{self.current_dept}%"  # 현재 사용자의 부서
                    ])            

                # 정렬 추가
                query += ' ORDER BY date, display_order, time'

                # 쿼리 실행
                self.cursor.execute(query, params)
                events = self.cursor.fetchall()
                self.count_label.setText(f'전체 일정: {len(events)}개')

                for event in events:
                    event_widget = QWidget()
                    event_widget.setFixedHeight(200)

                    is_admin = self.current_user == 'admin'
                    is_creator = event[5] == self.current_user
                    has_permission = is_admin or is_creator

                    event_widget.mouseDoubleClickEvent = lambda e, title=event[1]: self.open_list_file(title)
                    event_widget.setAttribute(Qt.WA_Hover)

                    bg_color = '#B2EBF4' if event[4] == '예정' else '#D5D5D5'
                    event_widget.setStyleSheet(f"background-color: {bg_color};")
                    
                    event_layout = QVBoxLayout()
                    event_layout.setSpacing(5)

                    # 상단 레이아웃
                    top_layout = QHBoxLayout()

                    # 좋아요 버튼
                    like_btn = QPushButton('♡')
                    like_btn.setCheckable(True)
                    like_btn.setFixedSize(30, 30)
                    like_btn.setStyleSheet("""
                        QPushButton {
                            color: gray;
                            background-color: transparent;
                            border: none;
                            font-size: 20px;
                        }
                        QPushButton:checked {
                            color: #5CD1E5;
                        }
                        QPushButton:hover {
                            color: #4BA3B3;
                        }
                    """)

                    self.cursor.execute('SELECT likes FROM events WHERE id = ?', (event[0],))
                    is_liked = self.cursor.fetchone()[0]
                    if is_liked:
                        like_btn.setChecked(True)
                        like_btn.setText('👍')
                    like_btn.clicked.connect(lambda checked, eid=event[0]: self.toggle_like(eid, checked))

                    # 일정 정보
                    info_text = f"[{event[4]}] {event[1]} (작성자: {event[5]})"
                    info_label = QLabel(info_text)
                    info_label.setStyleSheet("color: black;")

                    # 상태 토글 버튼
                    status_btn = QPushButton(event[4])
                    status_btn.setMaximumWidth(80)

                    if event[4] == '예정':
                        can_use = self.permissions.get('status_permissions', {}).get('complete', False)
                        status_btn.setStyleSheet("""
                            QPushButton {
                                color: black;
                                background-color: #B2EBF4;
                                border: 1px solid #cccccc;
                                padding: 5px;
                            }
                            QPushButton:hover {
                                background-color: #99E4F4;
                            }
                        """)
                    else:
                        can_use = self.permissions.get('status_permissions', {}).get('planned', False)
                        status_btn.setStyleSheet("""
                            QPushButton {
                                color: black;
                                background-color: #D5D5D5;
                                border: 1px solid #cccccc;
                                padding: 5px;
                            }
                            QPushButton:hover {
                                background-color: #C5C5C5;
                            }
                        """)

                    status_btn.setEnabled(can_use)
                    new_status = '완료' if event[4] == '예정' else '예정'
                    status_btn.clicked.connect(
                        lambda checked, eid=event[0], s=new_status: self.update_event_status(eid, s)
                    )

                    # 상단 레이아웃에 위젯 추가
                    top_layout.addWidget(like_btn)
                    top_layout.addWidget(info_label)
                    top_layout.addWidget(status_btn)
                    event_layout.addLayout(top_layout)

                    # 시간 정보와 admin 메모를 담을 수평 레이아웃 생성
                    time_admin_layout = QHBoxLayout()

                    # 시간 정보
                    if event[6]:
                        time_str = event[6]
                        event_date = event[8]  # 실제 일정 날짜
                        if event[4] == '완료':
                            time_info = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S').strftime('%H:%M')
                            time_label = QLabel(f"완료 시간: {event_date} {time_info}")
                        else:
                            created_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                            created_time = created_time + timedelta(hours=9)
                            time_info = created_time.strftime('%H:%M')
                            time_label = QLabel(f"생성 시간: {event_date} {time_info}")
                        time_label.setStyleSheet("color: gray; font-size: 13pt;")
                        time_admin_layout.addWidget(time_label)

                    # admin 메모 추가
                    if self.current_user == 'admin':
                        admin_textbox = QLineEdit()
                        admin_textbox.setFixedWidth(350)
                        admin_textbox.setPlaceholderText("Admin 메모")
                        admin_textbox.setStyleSheet("""
                            QLineEdit {
                                background-color: white;
                                border: 1px solid #cccccc;
                                border-radius: 3px;
                                padding: 5px;
                                color: black;
                            }
                            QLineEdit:focus {
                                border: 1px solid #5CD1E5;
                            }
                        """)
                        
                        # DB에서 admin 메모 불러오기
                        self.cursor.execute('SELECT admin_memo FROM events WHERE id = ?', (event[0],))
                        admin_memo = self.cursor.fetchone()[0]
                        if admin_memo:
                            admin_textbox.setText(admin_memo)
                        
                        # 메모 저장 기능
                        admin_textbox.textChanged.connect(
                            lambda text, eid=event[0]: self.save_admin_memo(eid, text)
                        )
                        
                        # 시간 정보와 admin 메모 사이에 공간 추가
                        time_admin_layout.addStretch()
                        time_admin_layout.addWidget(admin_textbox)

                    # 수평 레이아웃을 메인 레이아웃에 추가
                    event_layout.addLayout(time_admin_layout)

                    # 설명 추가
                    if event[3]:
                        desc_label = QLabel(f"설명: {event[3]}")
                        desc_label.setStyleSheet("""
                            QLabel {
                                color: black;
                                padding: 5px;
                                max-width: 300px;
                            }
                            QToolTip {
                                color: black;
                                background-color: white;
                                border: 1px solid #cccccc;
                                padding: 5px;
                                max-width: 300px;
                                white-space: pre-wrap;
                            }
                        """)
                        desc_label.setWordWrap(True)
                        desc_label.setFixedWidth(300)
                        desc_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                        
                        # 텍스트가 너무 길 경우 말줄임표(...) 표시
                        metrics = desc_label.fontMetrics()
                        elidedText = metrics.elidedText(f"설명: {event[3]}", Qt.ElideRight, 290)
                        desc_label.setText(elidedText)
                        
                        # 툴팁 텍스트에 줄바꿈 추가
                        formatted_tooltip = textwrap.fill(event[3], width=50)
                        desc_label.setToolTip(formatted_tooltip)
                        
                        event_layout.addWidget(desc_label)

                    # 하단 레이아웃
                    bottom_layout = QHBoxLayout()

                    image_label = QLabel()
                    image_label.setFixedSize(80, 80)
                    
                    base_image_paths = [
                        '/USA_DB/test_jn/image',
                        '/System/Volumes/Data/mnt/USA_DB/test_jn/image',
                        '/System/Volumes/Data/USA_DB/test_jn/image'
                    ]

                    # 이미지 경로 찾기
                    image_path = None
                    if "BB" in event[1]:
                        image_name = "BB.png"
                    elif "BM" in event[1]:
                        image_name = "BM.png"
                    elif "TGN" in event[1]:
                        image_name = "TGN.png"
                    elif "KOTH" in event[1]:
                        image_name = "KOTH.png"
                    elif "MS" in event[1]:
                        image_name = "MS.png"    
                    else:
                        image_name = None
                        
                    if image_name:
                        # 모든 기본 경로에서 이미지 파일 찾기
                        for base_path in base_image_paths:
                            temp_path = os.path.join(base_path, image_name)
                            if os.path.exists(temp_path):
                                pixmap = QPixmap(temp_path)
                                image_label.setPixmap(pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                                break

                    bottom_layout.addWidget(image_label)
                    bottom_layout.addStretch()

                    # 리스트 매칭 확인
                    has_matching_list = False
                    base_paths = [
                        '/USA_DB/test_jn/ship_list',
                        '/System/Volumes/Data/mnt/USA_DB/test_jn/ship_list',
                        '/System/Volumes/Data/USA_DB/test_jn/ship_list'
                    ]

                    for base_path in base_paths:
                        if not os.path.exists(base_path):
                            continue
                        for filename in os.listdir(base_path):
                            if selected_date in filename and event[1].replace('[', '').replace(']', '').split()[0] in filename:
                                has_matching_list = True
                                break
                        if has_matching_list:
                            break

                    # 매칭 레이블
                    match_label = QLabel("✓ 완료 리스트 있음" if has_matching_list else "✗ 완료 리스트 없음")
                    match_label.setStyleSheet("""
                        QLabel {
                            color: #28a745;
                            padding: 5px;
                        }
                    """ if has_matching_list else """
                        QLabel {
                            color: #dc3545;
                            padding: 5px;
                        }
                    """)
                    bottom_layout.addWidget(match_label)

                    # 버튼들 추가
                    if self.permissions.get('permissions', {}).get('list_create', False):
                        list_btn = QPushButton("완료 리스트 생성")
                        list_btn.setMaximumWidth(100)
                        list_btn.setStyleSheet("""
                            QPushButton {
                                color: black;
                                background-color: #FFE4B5;
                                border: 1px solid #cccccc;
                                padding: 5px;
                                border-radius: 3px;
                            }
                            QPushButton:hover {
                                background-color: #FFD700;
                            }
                        """)
                        list_btn.clicked.connect(self.show_completion_list)
                        bottom_layout.addWidget(list_btn)

                    if has_permission:
                        if self.permissions.get('permissions', {}).get('move', False):
                            move_btn = QPushButton("일정 이동")
                            move_btn.setMaximumWidth(60)
                            move_btn.setStyleSheet("""
                                QPushButton {
                                    color: black;
                                    background-color: #E4F7BA;
                                    border: 1px solid #cccccc;
                                    padding: 5px;
                                    border-radius: 3px;
                                }
                                QPushButton:hover {
                                    background-color: #f0f0f0;
                                }
                            """)
                            move_btn.clicked.connect(lambda checked, eid=event[0]: self.start_event_move(eid))
                            bottom_layout.addWidget(move_btn)

                        if self.permissions.get('permissions', {}).get('edit', False):
                            edit_btn = QPushButton("일정 수정")
                            edit_btn.setMaximumWidth(60)
                            edit_btn.setStyleSheet("""
                                QPushButton {
                                    color: black;
                                    background-color: white;
                                    border: 1px solid #cccccc;
                                    padding: 5px;
                                    border-radius: 3px;
                                }
                                QPushButton:hover {
                                    background-color: #f0f0f0;
                                }
                            """)
                            edit_btn.clicked.connect(lambda checked, eid=event[0]: self.show_edit_dialog(selected_date, eid))
                            bottom_layout.addWidget(edit_btn)

                        if self.permissions.get('permissions', {}).get('delete', False):
                            delete_btn = QPushButton("일정 삭제")
                            delete_btn.setMaximumWidth(60)
                            delete_btn.setStyleSheet("""
                                QPushButton {
                                    color: white;
                                    background-color: #dc3545;
                                    border: 1px solid #dc3545;
                                    padding: 5px;
                                    border-radius: 3px;
                                }
                                QPushButton:hover {
                                    background-color: #c82333;
                                }
                            """)
                            delete_btn.clicked.connect(lambda checked, eid=event[0]: self.delete_event(eid))
                            bottom_layout.addWidget(delete_btn)

                    event_layout.addLayout(bottom_layout)
                    event_widget.setLayout(event_layout)
                    self.events_layout.addWidget(event_widget)

                self.events_layout.setAlignment(Qt.AlignTop)

                date_str = self.calendar.selectedDate().toString('MM-dd')
                if date_str in self.calendar.holidays:
                    holiday_widget = QWidget()
                    holiday_widget.setFixedHeight(100)
                    holiday_widget.setStyleSheet("""
                        QWidget {
                            background-color: #FFE4E4;
                            border: 1px solid #FFB6B6;
                            border-radius: 5px;
                            margin-top: 0px;
                        }
                    """)
                    
                    holiday_layout = QVBoxLayout()
                    holiday_layout.setAlignment(Qt.AlignTop)
                    
                    # 공휴일 제목
                    title_label = QLabel(f"[공휴일] {self.calendar.holidays[date_str]}")
                    title_label.setStyleSheet("color: red; font-weight: bold; font-size: 13pt;")
                    
                    # 날짜 표시
                    date_label = QLabel(f"날짜: {selected_date}")
                    date_label.setStyleSheet("color: gray;")
                    
                    holiday_layout.addWidget(title_label)
                    holiday_layout.addWidget(date_label)
                    holiday_widget.setLayout(holiday_layout)
                    
                    # 공휴일 위젯을 맨 위에 추가
                    self.events_layout.insertWidget(0, holiday_widget)

                    # 구분선 추가
                    line = QFrame()
                    line.setFrameShape(QFrame.HLine)
                    line.setFrameShadow(QFrame.Sunken)
                    line.setStyleSheet("background-color: #cccccc;")
                    self.events_layout.addWidget(line)

                if len(events) == 1:
                    self.events_layout.addStretch(1)

        
        finally:
            self.cursor.close()
            self.cursor = self.conn.cursor()  # 새로운 커서 생성            

    def save_admin_memo(self, event_id, memo):
        if self.current_user == 'admin':
            self.cursor.execute(
                'UPDATE events SET admin_memo = ? WHERE id = ?',
                (memo, event_id)
            )
            self.conn.commit()
                

    def toggle_like(self, event_id, checked):
        # UI 업데이트
        sender = self.sender()
        sender.setText('👍' if checked else '♡')
        sender.setStyleSheet("""
            QPushButton {
                color: %s;
                background-color: transparent;
                border: none;
                font-size: 20px;
            }
        """ % ('#5CD1E5' if checked else 'gray'))
        
        # 데이터베이스 업데이트
        like_value = 1 if checked else 0
        self.cursor.execute('''
            UPDATE events 
            SET likes = ?
            WHERE id = ?
        ''', (like_value, event_id))
        self.conn.commit()

    def open_list_file(self, event_title):
        selected_date = self.calendar.selectedDate().toPyDate().strftime('%Y-%m-%d')
        print(f"선택된 날짜: {selected_date}")
        
        # [TGN] 5LBW05 ReTake 형식에서 TGN-5LBW05 형식으로 변환
        title_parts = event_title.replace('[', '').replace(']', '').split()
        env_name = None
        is_retake = False
        
        if len(title_parts) >= 2:
            env_name = f"{title_parts[0]}-{title_parts[1]}"
        
        if "ReTake" in event_title:
            is_retake = True
        
        print(f"환경 이름: {env_name}, ReTake 여부: {is_retake}")
        
        if not env_name:
            return
            
        base_paths = [
            '/USA_DB/test_jn/ship_list',
            '/System/Volumes/Data/mnt/USA_DB/test_jn/ship_list',
            '/System/Volumes/Data/USA_DB/test_jn/ship_list'
        ]
        
        for base_path in base_paths:
            if not os.path.exists(base_path):
                continue
                
            print(f"검색 중인 경로: {base_path}")
            for filename in os.listdir(base_path):
                if selected_date in filename and env_name in filename:
                    file_path = os.path.join(base_path, filename)
                    print(f"매칭된 파일: {file_path}")
                    
                    # 파일명에서 TK/take 포함 여부 확인 (대소문자 구분 없이)
                    has_tk = ('tk' in filename.lower() or 'take' in filename.lower())
                    print(f"TK/take 포함 여부: {has_tk}")
                    
                    # 본편/Retake에 따른 파일 매칭
                    if is_retake:
                        # Retake인 경우 TK가 포함된 파일만 표시
                        if not has_tk:
                            continue
                    else:
                        # 본편인 경우 TK가 없는 파일이나 TK1인 파일만 표시
                        if has_tk and 'tk1' not in filename.lower():
                            continue
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            dialog = QDialog(self)
                            dialog.setWindowTitle(f"완료 리스트 - {filename}")
                            dialog.setGeometry(100, 100, 600, 400)
                            
                            layout = QVBoxLayout()
                            text_edit = QTextEdit()
                            text_edit.setPlainText(content)
                            text_edit.setReadOnly(True)
                            layout.addWidget(text_edit)
                            
                            dialog.setLayout(layout)
                            dialog.exec_()
                            return
                    except Exception as e:
                        print(f"파일 읽기 오류: {str(e)}")
                        continue
        
        QMessageBox.warning(self, '알림', '해당하는 완료 리스트 파일을 찾을 수 없습니다.')



    def show_completion_list(self):
        selected_date = self.calendar.selectedDate().toPyDate().strftime('%Y-%m-%d')
        self.completion_window = MainWindow(selected_date)
        self.completion_window.setWindowTitle("완료 리스트 생성")
        self.completion_window.show()   

    def start_event_move(self, event_id):
        self.moving_event_id = event_id
        QMessageBox.information(self, '일정 이동', '이동하실 날짜를 선택하세요.')
        # 달력 클릭 이벤트 연결
        self.calendar.clicked.connect(lambda date: self.move_event(date))

    def move_event(self, new_date):
        if hasattr(self, 'moving_event_id'):
            # 이동할 일정 정보 가져오기
            self.cursor.execute('''
                SELECT title, time, description, status 
                FROM events 
                WHERE id = ?
            ''', (self.moving_event_id,))
            event_data = self.cursor.fetchone()
            
            if event_data:
                # 새로운 날짜로 일정 이동
                self.cursor.execute('''
                    UPDATE events 
                    SET date = ? 
                    WHERE id = ?
                ''', (new_date.toPyDate().strftime('%Y-%m-%d'), self.moving_event_id))
                
                self.conn.commit()
                
                # 달력 클릭 이벤트 연결 해제
                try:
                    self.calendar.clicked.disconnect()
                except TypeError:
                    pass
                    
                delattr(self, 'moving_event_id')
                
                # 일정 목록 갱신
                self.show_events()
                self.update_calendar_events()
                
                QMessageBox.information(self, '성공', '일정이 이동되었습니다.')
                
                # 달력 클릭 이벤트 다시 연결
                self.calendar.clicked.connect(self.show_events)       

    def show_edit_dialog(self, date, event_id):
        if not self.permissions.get('permissions', {}).get('edit', False):
            QMessageBox.warning(self, '권한 없음', '일정 수정 권한이 없습니다.')
            return

        # 필요한 모든 컬럼을 명시적으로 선택
        self.cursor.execute('''
            SELECT title, description, visibility FROM events WHERE id = ?
        ''', (event_id,))
        
        event = self.cursor.fetchone()
        if event:
            dialog = AddEventDialog(date, self)
            dialog.setWindowTitle('일정 수정')

            title = event[0]
            # 프로그램 형식 확인
            if title.startswith('[') and ']' in title:
                program = title[1:title.index(']')]
                if program in ['KOTH', 'BM', 'TGN', 'BB', 'MS']:
                    dialog.program_combo.setCurrentText(program)

                # 본편/ReTake 설정
                if '본편' in title:
                    dialog.type_본편.setChecked(True)
                if 'ReTake' in title:
                    dialog.type_retake.setChecked(True)

                # 번호 설정
                number = ''.join(filter(str.isdigit, title))
                if number:
                    dialog.number_input.setText(number)
                else:
                    # 직접 입력 모드로 설정
                    dialog.manual_check.setChecked(True)
                    dialog.title_input.setText(title)
            else:
                # 직접 입력 모드로 설정
                dialog.manual_check.setChecked(True)
                dialog.title_input.setText(title)

            # 설명 설정
            if event[1]:  # description
                dialog.description_input.setText(event[1])

            if event[2]:  # visibility
                if event[2] == 'private':
                    dialog.private_check.setChecked(True)
                else:
                    visible_depts = event[2].split(',')
                    for dept, checkbox in dialog.dept_checks.items():
                        checkbox.setChecked(dept in visible_depts)    

            if dialog.exec_() == QDialog.Accepted:
                event_data = dialog.get_event_data()
                self.cursor.execute('''
                    UPDATE events 
                    SET title = ?, description = ?, visibility = ?
                    WHERE id = ?
                ''', (event_data['title'], event_data['description'], event_data['visibility'], event_id))
                self.conn.commit()
                self.show_events()
                self.update_calendar_events()


    def delete_event(self, event_id):
        reply = QMessageBox.question(
            self, '일정 삭제', 
            '선택한 일정을 삭제하시겠습니까?',
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
            self.conn.commit()
            self.show_events()
            self.update_calendar_events()

    def setupNotificationTimer(self):
        # 자동 새로고침 타이머
        self.refresh_timer = QTimer()
        self.refresh_timer.setInterval(60000)  # 1분 = 60000ms
        self.refresh_timer.timeout.connect(self.refresh_events)
        self.refresh_timer.start()

    def closeEvent(self, event):
        if hasattr(self, 'conn'):
            self.conn.close()  # 프로그램 종료 시 연결 해제
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    login = LoginDialog()
    if login.exec_() == QDialog.Accepted:
        current_user = login.current_user  # current_user 값을 가져옴
        scheduler = SchedulerApp(login.current_user, login.permissions)
        scheduler.show()
        sys.exit(app.exec_())