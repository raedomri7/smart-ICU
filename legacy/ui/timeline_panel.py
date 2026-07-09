"""
ui/timeline_panel.py
======================
Panneau Historique & Événements du Patient.
Affiche un journal chronologique des événements cliniquement
significatifs détectés par les agents IA (changements de rythme,
escalades de sévérité).
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea
)
from PyQt5.QtCore import Qt
from utils.theme import COLORS, panel_style, SEVERITY_COLORS


class TimelineEventItem(QWidget):
    def __init__(self, time_str, event_text, severity):
        super().__init__()
        color = SEVERITY_COLORS.get(severity, COLORS['cyan']) if severity != 'info' else COLORS['text_dim']

        self.setStyleSheet("border: none; background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(10)

        # Point + ligne de la timeline
        dot_col = QWidget()
        dot_col.setFixedWidth(14)
        dot_col.setStyleSheet("border: none; background: transparent;")
        dot_layout = QVBoxLayout(dot_col)
        dot_layout.setContentsMargins(0, 2, 0, 0)
        dot_lbl = QLabel("●")
        dot_lbl.setStyleSheet(f"color: {color}; font-size: 11px; border: none; background: transparent;")
        dot_layout.addWidget(dot_lbl)
        dot_layout.addStretch()

        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        time_lbl = QLabel(time_str)
        time_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-family: 'Courier New'; font-size: 10px; border: none; background: transparent;")
        event_lbl = QLabel(event_text)
        event_lbl.setWordWrap(True)
        event_lbl.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: 500; border: none; background: transparent;")
        text_col.addWidget(time_lbl)
        text_col.addWidget(event_lbl)

        layout.addWidget(dot_col)
        layout.addLayout(text_col, 1)


class TimelinePanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(panel_style())
        self._last_count = 0
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
        dot.setStyleSheet(f"color: {COLORS['cyan']}; font-size: 8px; border: none; background: transparent;")
        title = QLabel("TIMELINE PATIENT")
        title.setStyleSheet(f"color: {COLORS['cyan']}; font-size: 11px; font-weight: bold; letter-spacing: 2px; border: none; background: transparent;")
        h_layout.addWidget(dot)
        h_layout.addSpacing(6)
        h_layout.addWidget(title)
        h_layout.addStretch()
        layout.addWidget(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ background: {COLORS['bg_card']}; border: none; }}
            QScrollBar:vertical {{ background: {COLORS['bg_card']}; width: 4px; }}
            QScrollBar::handle:vertical {{ background: {COLORS['border_bright']}; border-radius: 2px; }}
        """)

        self.container = QWidget()
        self.container.setStyleSheet(f"background: {COLORS['bg_card']};")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(12, 8, 12, 8)
        self.container_layout.setSpacing(2)

        empty_lbl = QLabel("Aucun événement enregistré pour le moment.")
        empty_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none; background: transparent;")
        self.container_layout.addWidget(empty_lbl)
        self.container_layout.addStretch()

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)

    def update_timeline(self, events):
        if len(events) == self._last_count:
            return
        self._last_count = len(events)

        # Vide
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not events:
            empty_lbl = QLabel("Aucun événement enregistré pour le moment.")
            empty_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none; background: transparent;")
            self.container_layout.addWidget(empty_lbl)
        else:
            for ev in events[:30]:
                item = TimelineEventItem(ev['time'], ev['event'], ev['severity'])
                self.container_layout.addWidget(item)

        self.container_layout.addStretch()
