import sys
from PyQt6.QtWidgets import QApplication, QWidget

def main():
    app = QApplication(sys.argv)
    w = QWidget()
    w.setWindowTitle("PyQt6 Test")
    w.show()
    print("Window shown")
    # Close immediately for testing
    app.quit()

if __name__ == "__main__":
    main()
