"""
main.py — DocStyle Pro 앱 진입점

실행
    python main.py
"""

import sys
from pathlib import Path

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

# 프로젝트 루트를 sys.path 에 추가
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("DocStyle Pro")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("DocStyle")

    # 전역 폰트
    font = QFont("Arial", 10)
    app.setFont(font)

    # 전역 스타일시트
    app.setStyleSheet("""
        QWidget        { font-family: 'Arial', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; }
        QScrollBar:vertical {
            width: 6px; background: #F1F5F9; border-radius: 3px;
        }
        QScrollBar::handle:vertical {
            background: #CBD5E1; border-radius: 3px; min-height: 20px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        QToolTip {
            background: #1E293B; color: #FFFFFF;
            border: 1px solid #334155; padding: 4px 8px;
            border-radius: 4px; font-size: 9px;
        }
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {
            color: #000000;
        }
        QMenu {
            background-color: #FFFFFF;
            color: #000000;
            border: 1px solid #CBD5E1;
        }
        QMenu::item {
            padding: 6px 24px;
            background-color: transparent;
            color: #000000;
        }
        QMenu::item:selected {
            background-color: #F1F5F9;
            color: #1D4ED8;
        }
    """)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
