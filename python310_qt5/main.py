import sys
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout

def main():
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle('Python 3.10 + Qt5 Verify')
    layout = QVBoxLayout()
    label = QLabel('Hello from Python 3.10 + PyQt5!')
    layout.addWidget(label)
    window.setLayout(layout)
    window.show()
    print("PyQt5 window opened successfully (Python 3.10)")
    app.exec_()

if __name__ == "__main__":
    main()
