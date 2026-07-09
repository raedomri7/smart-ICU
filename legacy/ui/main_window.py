"""
ui/main_window.py
==================
Fenêtre Principale - Disposition complète du tableau de bord ICU.

Disposition :
    GAUCHE (large) : ECG -> Signes Vitaux -> [Insights IA | Aide Décision | Timeline]
    DROITE (étroite) : Alertes -> Priorité Patients / Statut Système

À chaque tick de 2 secondes :
    1. Avance le simulateur patient (signes vitaux synthétiques + rythme ECG)
    2. Exécute les 6 agents IA par signal + Agent de Décision Clinique + Agent de Prédiction
    3. Pousse les résultats dans chaque panneau
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel
)
from PyQt5.QtCore import QTimer, QDateTime

from ui.ecg_widget import ECGWidget
from ui.vitals_panel import VitalsPanel
from ui.ai_panel import AIPredictionPanel
from ui.alerts_panel import AlertsPanel
from ui.patient_panel import PatientPriorityPanel
from ui.history_panel import HistoryPanel
from ui.decision_panel import DecisionPanel
from ui.timeline_panel import TimelinePanel
from utils.theme import apply_dark_theme, COLORS
from utils.patient_simulator import PatientSimulator


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Système de Monitoring ICU Intelligent par IA v4.3.0")
        self.setMinimumSize(1440, 920)
        self.showMaximized()

        apply_dark_theme(self)

        self.simulator = PatientSimulator()

        self._build_menu()
        self._build_header()
        self._build_central()
        self._build_statusbar()

        self.master_timer = QTimer()
        self.master_timer.timeout.connect(self._tick)
        self.master_timer.start(2000)

        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)

        # Exécute un tick immédiatement pour ne pas avoir de panneaux vides au lancement
        self._tick()

    # ----------------------------------------------------------
    def _build_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet(f"""
            QMenuBar {{ background: {COLORS['bg_header']}; color: {COLORS['text']}; border-bottom: 1px solid {COLORS['cyan']}; }}
            QMenuBar::item:selected {{ background: {COLORS['bg_card']}; }}
            QMenu {{ background: {COLORS['bg_card']}; color: {COLORS['text']}; border: 1px solid {COLORS['border']}; }}
            QMenu::item:selected {{ background: {COLORS['bg_header']}; }}
        """)

        file_menu = menubar.addMenu("Fichier")
        file_menu.addAction("Exporter le Rapport (PDF)", self._export_pdf)
        file_menu.addAction("Sauvegarder l'Historique Patient", self._save_history)
        file_menu.addSeparator()
        file_menu.addAction("Quitter", self.close)

        view_menu = menubar.addMenu("Affichage")
        view_menu.addAction("Mode Plein Écran d'Urgence", self._emergency_mode)
        view_menu.addAction("Mode Normal", self.showMaximized)

        help_menu = menubar.addMenu("Aide")
        help_menu.addAction("À propos", self._show_about)

    # ----------------------------------------------------------
    def _build_header(self):
        header = QWidget()
        header.setFixedHeight(64)
        header.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #020810, stop:0.4 #061222, stop:1 #020810);
                border-bottom: 1px solid {COLORS['cyan']};
            }}
        """)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 8, 16, 8)

        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setSpacing(2)
        title_layout.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel("SYSTÈME DE MONITORING ICU INTELLIGENT PAR IA")
        title_lbl.setStyleSheet(f"color: {COLORS['cyan']}; font-size: 18px; font-weight: bold; letter-spacing: 3px;")
        subtitle_lbl = QLabel("Plateforme d'Intelligence Biomédicale Multi-Agents  |  v4.3.0")
        subtitle_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; letter-spacing: 1px;")
        title_layout.addWidget(title_lbl)
        title_layout.addWidget(subtitle_lbl)
        layout.addWidget(title_widget)
        layout.addStretch()

        self.patient_box = self._header_box("ID PATIENT", "ICU-204")
        self.ward_box = self._header_box("SERVICE", "CICU-3B")
        self.doctor_box = self._header_box("MÉDECIN", "Dr. Karim")
        self.time_box = self._header_box("HEURE", "--:--:--")

        for box in [self.patient_box, self.ward_box, self.doctor_box, self.time_box]:
            layout.addWidget(box)
            layout.addSpacing(8)

        layout.addStretch()

        ai_status = QLabel("  ●  IA ACTIVE  ")
        ai_status.setStyleSheet(f"""
            color: {COLORS['green']}; background: rgba(0,255,136,0.05);
            border: 1px solid {COLORS['green']}; border-radius: 12px;
            font-size: 11px; font-weight: bold; letter-spacing: 2px; padding: 4px 10px;
        """)
        layout.addWidget(ai_status)

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(header)

        self._central_container = container
        self.setCentralWidget(container)

    def _header_box(self, label, value):
        box = QWidget()
        box.setStyleSheet(f"""
            QWidget {{ background: rgba(0,150,255,0.05); border: 1px solid {COLORS['border_bright']}; border-radius: 6px; padding: 4px 12px; }}
        """)
        layout = QVBoxLayout(box)
        layout.setSpacing(1)
        layout.setContentsMargins(8, 4, 8, 4)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 9px; letter-spacing: 1px; border: none; background: transparent;")
        val = QLabel(value)
        val.setObjectName("value")
        val.setStyleSheet(f"color: {COLORS['cyan']}; font-family: 'Courier New'; font-size: 13px; font-weight: bold; border: none; background: transparent;")
        layout.addWidget(lbl)
        layout.addWidget(val)
        return box

    # ----------------------------------------------------------
    def _build_central(self):
        content = QWidget()
        content.setStyleSheet(f"background: {COLORS['bg_primary']};")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)

        # COLONNE GAUCHE (large)
        left_col = QWidget()
        left_layout = QVBoxLayout(left_col)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.ecg_widget = ECGWidget(self.simulator)
        self.vitals_panel = VitalsPanel()
        self.ai_panel = AIPredictionPanel()
        self.decision_panel = DecisionPanel()
        self.history_panel = HistoryPanel()

        left_layout.addWidget(self.ecg_widget, 3)
        left_layout.addWidget(self.vitals_panel, 2)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)
        bottom_row.addWidget(self.ai_panel, 1)
        bottom_row.addWidget(self.decision_panel, 1)
        bottom_row.addWidget(self.history_panel, 1)

        bottom_widget = QWidget()
        bottom_widget.setLayout(bottom_row)
        left_layout.addWidget(bottom_widget, 4)

        # COLONNE DROITE (étroite)
        right_col = QWidget()
        right_col.setFixedWidth(310)
        right_layout = QVBoxLayout(right_col)
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.alerts_panel = AlertsPanel()
        self.patient_panel = PatientPriorityPanel()
        self.timeline_panel = TimelinePanel()

        right_layout.addWidget(self.alerts_panel, 2)
        right_layout.addWidget(self.timeline_panel, 2)
        right_layout.addWidget(self.patient_panel, 3)

        content_layout.addWidget(left_col, 1)
        content_layout.addWidget(right_col)

        self._central_container.layout().addWidget(content)

    # ----------------------------------------------------------
    def _build_statusbar(self):
        sb = self.statusBar()
        sb.setStyleSheet(f"""
            QStatusBar {{ background: {COLORS['bg_header']}; color: {COLORS['text_dim']}; border-top: 1px solid {COLORS['border']}; font-size: 10px; }}
        """)
        sb.showMessage("  Système de Monitoring ICU Intelligent par IA  |  Agents : ECG · FC · SpO2 · Temp · PA · Resp · Décision Clinique · Prédiction  |  Dataset : MIT-BIH + MIMIC-IV")

    # ----------------------------------------------------------
    def _tick(self):
        """Mise à jour principale — appelée toutes les 2 secondes."""
        ai_output = self.simulator.step()
        vitals = self.simulator.get_vitals()
        agents = ai_output['agents']
        prediction_summary = self.simulator.get_ai_prediction()

        self.vitals_panel.update_vitals(vitals, agents)
        self.ai_panel.update_prediction(prediction_summary, vitals)
        self.alerts_panel.update_alerts(prediction_summary, vitals)
        self.history_panel.update_history(vitals)
        self.decision_panel.update_decision(ai_output)
        self.timeline_panel.update_timeline(self.simulator.get_timeline_events())
        self.ecg_widget.update_from_agent(agents['ecg'])

    def _update_clock(self):
        now = QDateTime.currentDateTime()
        val = self.time_box.findChild(QLabel, "value")
        if val:
            val.setText(now.toString("hh:mm:ss"))

    # ----------------------------------------------------------
    def _export_pdf(self):
        from utils.report_generator import generate_pdf_report
        vitals = self.simulator.get_vitals()
        ai_summary = self.simulator.last_ai_output
        generate_pdf_report("ICU-204", vitals, ai_summary)

    def _save_history(self):
        from utils.data_manager import save_patient_history
        save_patient_history("ICU-204", self.simulator.history)

    def _emergency_mode(self):
        self.showFullScreen()
        self.setStyleSheet(f"QMainWindow {{ background: #000; border: 3px solid {COLORS['red']}; }}")

    def _show_about(self):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "À propos",
            "Système de Monitoring ICU Intelligent par IA v4.3.0\n\n"
            "Plateforme d'Intelligence Biomédicale Multi-Agents\n"
            "Agents : ECG, Fréquence Cardiaque, SpO2, Température, Pression Artérielle,\n"
            "Respiratoire, Décision Clinique, Prédiction\n\n"
            "Datasets : PhysioNet · MIMIC-IV · MIT-BIH\n\n"
            "Outil d'aide à la décision clinique uniquement.")
