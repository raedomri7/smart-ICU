"""
ui/alerts_panel.py
===================
Panneau du Système d'Alertes Intelligentes.

Niveaux de sévérité (selon la spec) : Normal / Faible / Moyen / Élevé / Critique
Couleurs :                            Vert  / Bleu  / Jaune / Orange / Rouge

Les alertes sont générées dynamiquement à partir des résultats des agents IA
à chaque tick (pas depuis une table statique par forme d'onde), donc tout
agent franchissant une sévérité non-normale produit une alerte en direct
avec confiance affichée et explication.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, QDateTime
from utils.theme import COLORS, panel_style, SEVERITY_COLORS

SEVERITY_ICONS = {
    'low': 'ℹ',
    'medium': '⚠',
    'high': '🚨',
    'critical': '🚨',
}

SEVERITY_BG = {
    'low':      'rgba(0,150,255,0.06)',
    'medium':   'rgba(255,204,0,0.06)',
    'high':     'rgba(255,102,0,0.08)',
    'critical': 'rgba(255,34,68,0.08)',
}


class AlertItem(QWidget):
    def __init__(self, severity, signal, text, confidence, time_str):
        super().__init__()
        color = SEVERITY_COLORS.get(severity, COLORS['cyan'])
        bg = SEVERITY_BG.get(severity, 'rgba(0,229,255,0.05)')

        self.setStyleSheet(f"""
            QWidget {{ background: {bg}; border: 1px solid {color}; border-radius: 5px; }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(8)

        icon_lbl = QLabel(SEVERITY_ICONS.get(severity, 'ℹ'))
        icon_lbl.setStyleSheet("font-size: 13px; border: none; background: transparent;")

        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        header_row = QHBoxLayout()
        sig_lbl = QLabel(signal.upper())
        sig_lbl.setStyleSheet(f"color: {color}; font-size: 9px; font-weight: bold; letter-spacing: 1px; border: none; background: transparent;")
        conf_lbl = QLabel(f"{confidence}%")
        conf_lbl.setStyleSheet(f"color: {color}; font-family: 'Courier New'; font-size: 9px; border: none; background: transparent;")
        header_row.addWidget(sig_lbl)
        header_row.addStretch()
        header_row.addWidget(conf_lbl)

        text_lbl = QLabel(text)
        text_lbl.setWordWrap(True)
        text_lbl.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: 500; border: none; background: transparent;")

        text_col.addLayout(header_row)
        text_col.addWidget(text_lbl)

        time_lbl = QLabel(time_str)
        time_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-family: 'Courier New'; font-size: 9px; border: none; background: transparent;")

        layout.addWidget(icon_lbl)
        layout.addLayout(text_col, 1)
        layout.addWidget(time_lbl)

        if severity == 'critical':
            self._blink_state = True
            self._timer = QTimer()
            self._timer.timeout.connect(self._blink)
            self._timer.start(650)

    def _blink(self):
        self._blink_state = not self._blink_state
        self.setWindowOpacity(1.0 if self._blink_state else 0.55)


class AlertsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(panel_style())
        self._last_signature = None
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
        dot.setStyleSheet(f"color: {COLORS['red']}; font-size: 8px; border: none; background: transparent;")
        title = QLabel("ALERTES INTELLIGENTES")
        title.setStyleSheet(f"color: {COLORS['red']}; font-size: 11px; font-weight: bold; letter-spacing: 2px; border: none; background: transparent;")
        self.count_lbl = QLabel("0 ACTIVE(S)")
        self.count_lbl.setStyleSheet(f"color: {COLORS['green']}; font-family: 'Courier New'; font-size: 11px; border: none; background: transparent;")
        h_layout.addWidget(dot)
        h_layout.addSpacing(6)
        h_layout.addWidget(title)
        h_layout.addStretch()
        h_layout.addWidget(self.count_lbl)
        layout.addWidget(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ background: {COLORS['bg_card']}; border: none; }}
            QScrollBar:vertical {{ background: {COLORS['bg_card']}; width: 4px; }}
            QScrollBar::handle:vertical {{ background: {COLORS['border_bright']}; border-radius: 2px; }}
        """)

        self.alerts_container = QWidget()
        self.alerts_container.setStyleSheet(f"background: {COLORS['bg_card']};")
        self.alerts_layout = QVBoxLayout(self.alerts_container)
        self.alerts_layout.setContentsMargins(8, 8, 8, 8)
        self.alerts_layout.setSpacing(5)

        self.empty_lbl = QLabel("✓  Aucune alerte active — patient stable")
        self.empty_lbl.setStyleSheet(f"color: {COLORS['green']}; font-size: 11px; border: none; background: transparent; padding: 6px;")
        self.alerts_layout.addWidget(self.empty_lbl)
        self.alerts_layout.addStretch()

        self.scroll.setWidget(self.alerts_container)
        layout.addWidget(self.scroll, 1)

    def update_alerts(self, ai_prediction, vitals):
        """
        ai_prediction provient de PatientSimulator.get_ai_prediction(), qui
        transporte 'agents' (dict de AgentResult) issu de l'orchestrateur.
        On construit une alerte par résultat d'agent non-normal.
        """
        agents = ai_prediction.get('agents', {})
        active = [r for r in agents.values() if r.severity != 'normal']
        # Trie par sévérité décroissante
        rank = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        active.sort(key=lambda r: rank.get(r.severity, 0), reverse=True)

        signature = tuple((r.signal, r.detected_event, r.severity) for r in active)
        if signature == self._last_signature:
            return
        self._last_signature = signature

        # Vide
        while self.alerts_layout.count():
            item = self.alerts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        now = QDateTime.currentDateTime()

        if not active:
            self.empty_lbl = QLabel("✓  Aucune alerte active — patient stable")
            self.empty_lbl.setStyleSheet(f"color: {COLORS['green']}; font-size: 11px; border: none; background: transparent; padding: 6px;")
            self.alerts_layout.addWidget(self.empty_lbl)
            self.count_lbl.setText("0 ACTIVE(S)")
            self.count_lbl.setStyleSheet(f"color: {COLORS['green']}; font-family: 'Courier New'; font-size: 11px; border: none; background: transparent;")
        else:
            for r in active:
                item = AlertItem(r.severity, r.signal, f"{r.detected_event} — {r.explanation}", r.confidence, now.toString("hh:mm"))
                self.alerts_layout.addWidget(item)

            crit_count = sum(1 for r in active if r.severity == 'critical')
            color = COLORS['red'] if crit_count > 0 else COLORS['orange'] if any(r.severity == 'high' for r in active) else COLORS['yellow']
            self.count_lbl.setText(f"{len(active)} ACTIVE(S)")
            self.count_lbl.setStyleSheet(f"color: {color}; font-family: 'Courier New'; font-size: 11px; border: none; background: transparent;")

        self.alerts_layout.addStretch()
