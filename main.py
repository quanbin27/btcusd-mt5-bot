# ============================================================
# BTC Sell Bot – Entry Point
# ============================================================
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from ui_app import MainWindow


def main():
    app = QApplication(sys.argv)

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
