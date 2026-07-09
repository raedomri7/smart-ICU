"""
ui/patient_panel.py
====================
Système Multi-Patients par Priorité — liste de patients classés par IA
+ statut système.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt
from utils.theme import COLORS, panel_style

PATIENTS = [
    {'id': 'ICU-204', 'name': 'Patient Actif', 'age': 55, 'status': 'critical', 'risk': 72},
    {'id': 'ICU-102', 'name': 'M. Hassan', 'age': 61, 'status': 'critical', 'risk': 68},
    {'id': 'ICU-115', 'name': 'F. Zahra', 'age': 45, 'status': 'moderate', 'risk': 45},
    {'id': 'ICU-120', 'name': 'A. Kamel', 'age': 73, 'status': 'stable', 'risk': 18},
    {'id': 'ICU-133', 'name': 'S. Omar', 'age': 38, 'status': 'stable', 'risk': 12},
]

STATUS_STYLE = {
    'critical': {'color': COLORS['red'], 'bg': 'rgba(255,34,68,0.12)', 'border': 'rgba(255,34,68,0.3)', 'label': 'CRITIQUE'},
    'moderate': {'color': COLORS['yellow'], 'bg': 'rgba(255,204,0,0.10)', 'border': 'rgba(255,204,0,0.28)', 'label': 'MODÉRÉ'},
    'stable':   {'color': COLORS['green'], 'bg': 'rgba(0,255,136,0.10)', 'border': 'rgba(0,255,136,0.28)', 'label': 'STABLE'},
}


class PatientItem(QWidget):
    def __init__(self, rank, patient, active=False):
        super().__init__()
        s = STATUS_STYLE[patient['status']]
        border_color = COLORS['cyan'] if active else COLORS['border']
        bg = 'rgba(0,229,255,0.05)' if active else 'rgba(0,150,255,0.03)'

        self.setStyleSheet(f"""
            QWidget {{ background: {bg}; border: 1px solid {border_color}; border-radius: 6px; }}
            QWidget:hover {{ border: 1px solid {COLORS['border_bright']}; background: rgba(0,150,255,0.06); }}
        """)
        self.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(10)

        rank_lbl = QLabel(str(rank))
        rank_lbl.setFixedWidth(18)
        rank_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-family: 'Courier New'; font-size: 11px; border: none; background: transparent;")

        id_col = QWidget()
        id_col.setStyleSheet("border: none; background: transparent;")
        id_layout = QVBoxLayout(id_col)
        id_layout.setContentsMargins(0, 0, 0, 0)
        id_layout.setSpacing(1)
        id_lbl = QLabel(patient['id'])
        id_lbl.setStyleSheet(f"color: {COLORS['text']}; font-family: 'Courier New'; font-size: 13px; font-weight: bold; border: none; background: transparent;")
        name_lbl = QLabel(f"{patient['name']}, {patient['age']} ans")
        name_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; border: none; background: transparent;")
        id_layout.addWidget(id_lbl)
        id_layout.addWidget(name_lbl)

        risk_lbl = QLabel(f"{patient['risk']}%")
        risk_lbl.setStyleSheet(f"color: {s['color']}; font-family: 'Courier New'; font-size: 12px; border: none; background: transparent;")

        badge = QLabel(s['label'])
        badge.setStyleSheet(f"""
            color: {s['color']}; background: {s['bg']}; border: 1px solid {s['border']};
            border-radius: 8px; font-size: 9px; font-weight: bold; letter-spacing: 1px; padding: 2px 7px;
        """)

        layout.addWidget(rank_lbl)
        layout.addWidget(id_col, 1)
        layout.addWidget(risk_lbl)
        layout.addWidget(badge)


class PatientPriorityPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(panel_style())
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(32)
        header.setStyleSheet(f"background: rgba(0,150,255,0.03); border-bottom: 1px solid {COLORS['border']};")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 0, 12, 0)
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {COLORS['yellow']}; font-size: 8px; border: none; background: transparent;")
        title = QLabel("PRIORITÉ PATIENTS")
        title.setStyleSheet(f"color: {COLORS['yellow']}; font-size: 11px; font-weight: bold; letter-spacing: 2px; border: none; background: transparent;")
        ai_lbl = QLabel("CLASSÉ PAR IA")
        ai_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; border: none; background: transparent;")
        h_layout.addWidget(dot)
        h_layout.addSpacing(6)
        h_layout.addWidget(title)
        h_layout.addStretch()
        h_layout.addWidget(ai_lbl)
        layout.addWidget(header)

        list_widget = QWidget()
        list_widget.setStyleSheet(f"background: {COLORS['bg_card']};")
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(8, 8, 8, 8)
        list_layout.setSpacing(5)

        for i, patient in enumerate(PATIENTS):
            item = PatientItem(i + 1, patient, active=(patient['id'] == 'ICU-204'))
            list_layout.addWidget(item)

        list_layout.addStretch()
        layout.addWidget(list_widget, 1)

        sys_widget = QWidget()
        sys_widget.setStyleSheet(f"background: {COLORS['bg_card']}; border-top: 1px solid {COLORS['border']};")
        sys_layout = QVBoxLayout(sys_widget)
        sys_layout.setContentsMargins(12, 8, 12, 8)
        sys_layout.setSpacing(5)

        sys_title = QLabel("STATUT SYSTÈME")
        sys_title.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 9px; letter-spacing: 2px; border: none; background: transparent;")
        sys_layout.addWidget(sys_title)

        status_rows = [
            ("Agents IA", "7 Actifs  ✓", COLORS['green']),
            ("Dataset", "MIMIC-IV / MIT-BIH", COLORS['cyan']),
            ("Échantillonnage", "250 Hz", COLORS['cyan']),
            ("Réseau", "LAN Hôpital  ✓", COLORS['green']),
        ]
        for label, value, color in status_rows:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; border: none; background: transparent;")
            val = QLabel(value)
            val.setStyleSheet(f"color: {color}; font-family: 'Courier New'; font-size: 10px; border: none; background: transparent;")
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val)
            sys_layout.addLayout(row)

        layout.addWidget(sys_widget)
