"""
SYSTÈME DE MONITORING ICU INTELLIGENT PAR IA
================================================
Point d'entrée principal - Exécuter ce fichier pour lancer l'application.

Utilisation :
    pip install -r requirements.txt
    python main.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.main_window import MainWindow


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Système de Monitoring ICU Intelligent par IA")
    app.setApplicationVersion("4.3.0")
    app.setOrganizationName("Laboratoire de Génie Biomédical")

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
