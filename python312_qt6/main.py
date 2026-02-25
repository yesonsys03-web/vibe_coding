import sys
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout

def main():
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle('Python 3.12 + Qt6 Verify')
    layout = QVBoxLayout()
    label = QLabel('Hello from Python 3.12 + PyQt6!')
    layout.addWidget(label)
    window.setLayout(layout)
    window.show()
    print("PyQt6 window opened successfully (Python 3.12)")
    app.exec()

if __name__ == "__main__":
    main()
