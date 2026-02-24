import sys
try:
    if "qt5" in sys.executable.lower() or "qt5" in sys.path[0].lower():
        from PyQt5.QtCore import QT_VERSION_STR
        print(f"Qt5 Version: {QT_VERSION_STR}")
    else:
        from PyQt6.QtCore import QT_VERSION_STR
        print(f"Qt6 Version: {QT_VERSION_STR}")
    print("Verification Successful!")
except ImportError as e:
    print(f"Verification Failed: {e}")
    sys.exit(1)
