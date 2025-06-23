# main.py

import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from home import MainWindow
import config

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    app = QApplication(sys.argv)
    app.setApplicationName("Yu-Gi-Oh! Database")
    app.setOrganizationName("Team Rocket")
    try:
        app.setWindowIcon(QIcon(config.ICON_FILE))
    except:
        logging.warning(f"Icon file not found at '{config.ICON_FILE}'")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()