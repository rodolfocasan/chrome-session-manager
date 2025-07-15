# main.py
import sys
from PyQt5.QtWidgets import QApplication
from session_manager import ChromeSessionManager





if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ChromeSessionManager()
    window.show()
    sys.exit(app.exec_())