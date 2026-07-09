"""
ui/history_panel.py
=====================
Panneau Historique & Tendances du Patient.
Sparkline custom-dessiné, léger (pas de dépendance graphique externe).
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QLinearGradient, QBrush
from utils.theme import COLORS, panel_style


METRIC_INFO = {
    'hr':   {'label': 'Fréq. Cardiaque', 'unit': 'bpm', 'color': COLORS['green']},
    'spo2': {'label': 'SpO₂',            'unit': '%',   'color': COLORS['cyan']},
    'rr':   {'label': 'Fréq. Resp.',     'unit': '/min','color': COLORS['blue']},
    'temp': {'label': 'Température',     'unit': '°C',  'color': COLORS['yellow']},
}


class Sparkline(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(100)
        self.data = []
        self.color = QColor(COLORS['green'])

    def set_data(self, data, color_str):
        self.data = data
        self.color = QColor(color_str)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()

        # Lignes de grille
        painter.setPen(QPen(QColor(255, 255, 255, 12), 1))
        for i in range(1, 4):
            y = H * i / 4
            painter.drawLine(0, int(y), W, int(y))

        if len(self.data) < 2:
            painter.end()
            return

        vmin, vmax = min(self.data), max(self.data)
        if vmax == vmin:
            vmax += 1
        span = vmax - vmin
        n = len(self.data)
        step_x = W / max(1, n - 1)

        points = []
        for i, v in enumerate(self.data):
            x = i * step_x
            y = H - ((v - vmin) / span) * (H - 10) - 5
            points.append((x, y))

        # Remplissage en dégradé sous la ligne
        grad = QLinearGradient(0, 0, 0, H)
        fill_color = QColor(self.color)
        fill_color.setAlpha(50)
        grad.setColorAt(0, fill_color)
        fill_color2 = QColor(self.color)
        fill_color2.setAlpha(0)
        grad.setColorAt(1, fill_color2)

        from PyQt5.QtGui import QPainterPath
        path = QPainterPath()
        path.moveTo(*points[0])
        for p in points[1:]:
            path.lineTo(*p)
        path.lineTo(W, H)
        path.lineTo(0, H)
        path.closeSubpath()
        painter.fillPath(path, QBrush(grad))

        # Ligne
        painter.setPen(QPen(self.color, 2))
        for i in range(len(points) - 1):
            painter.drawLine(int(points[i][0]), int(points[i][1]), int(points[i+1][0]), int(points[i+1][1]))

        # Point du dernier échantillon
        last = points[-1]
        painter.setBrush(QBrush(self.color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(last[0]) - 4, int(last[1]) - 4, 8, 8)

        painter.end()


class HistoryPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(panel_style())
        self.current_metric = 'hr'
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(32)
        header.setStyleSheet(f"background: rgba(0,150,255,0.03); border-bottom: 1px solid {COLORS['border']};")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 0, 8, 0)
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {COLORS['blue']}; font-size: 8px; border: none; background: transparent;")
        title = QLabel("HISTORIQUE DES TENDANCES")
        title.setStyleSheet(f"color: {COLORS['blue']}; font-size: 11px; font-weight: bold; letter-spacing: 2px; border: none; background: transparent;")
        h_layout.addWidget(dot)
        h_layout.addSpacing(6)
        h_layout.addWidget(title)
        h_layout.addStretch()

        self.tab_buttons = {}
        for key in ['hr', 'spo2', 'rr', 'temp']:
            btn = QLabel(key.upper())
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(self._tab_style(active=(key == 'hr')))
            btn.mousePressEvent = lambda e, k=key: self._select_metric(k)
            self.tab_buttons[key] = btn
            h_layout.addWidget(btn)
        layout.addWidget(header)

        body = QWidget()
        body.setStyleSheet(f"background: {COLORS['bg_card']};")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(12, 10, 12, 8)
        body_layout.setSpacing(6)

        self.sparkline = Sparkline()
        body_layout.addWidget(self.sparkline, 1)

        stats_row = QHBoxLayout()
        self.current_lbl = self._stat_label("Actuel", "-- bpm", COLORS['green'])
        self.min_lbl = self._stat_label("Min", "--", COLORS['cyan'])
        self.max_lbl = self._stat_label("Max", "--", COLORS['red'])
        self.avg_lbl = self._stat_label("Moy", "--", COLORS['green'])
        for lbl_widget in [self.current_lbl, self.min_lbl, self.max_lbl, self.avg_lbl]:
            stats_row.addWidget(lbl_widget)
        body_layout.addLayout(stats_row)

        layout.addWidget(body, 1)

    def _tab_style(self, active):
        if active:
            return f"""
                color: {COLORS['green']}; background: rgba(0,255,136,0.1);
                border: 1px solid {COLORS['green']}; border-radius: 4px;
                font-size: 9px; font-weight: bold; letter-spacing: 1px;
                padding: 2px 7px; margin-left: 4px;
            """
        return f"""
            color: {COLORS['text_dim']}; background: transparent;
            border: 1px solid {COLORS['border']}; border-radius: 4px;
            font-size: 9px; letter-spacing: 1px;
            padding: 2px 7px; margin-left: 4px;
        """

    def _stat_label(self, label, value, color):
        w = QWidget()
        w.setStyleSheet("border: none; background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(0)
        lab = QLabel(label)
        lab.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 9px; border: none; background: transparent;")
        val = QLabel(value)
        val.setObjectName("val")
        val.setStyleSheet(f"color: {color}; font-family: 'Courier New'; font-size: 13px; font-weight: bold; border: none; background: transparent;")
        l.addWidget(lab)
        l.addWidget(val)
        return w

    def _select_metric(self, key):
        self.current_metric = key
        for k, btn in self.tab_buttons.items():
            btn.setStyleSheet(self._tab_style(active=(k == key)))
        self._refresh()

    def update_history(self, vitals):
        if not hasattr(self, '_history_buffers'):
            self._history_buffers = {'hr': [], 'spo2': [], 'rr': [], 'temp': []}
        for k in self._history_buffers:
            self._history_buffers[k].append(vitals[k])
            if len(self._history_buffers[k]) > 40:
                self._history_buffers[k].pop(0)
        self._refresh()

    def _refresh(self):
        if not hasattr(self, '_history_buffers'):
            return
        data = self._history_buffers.get(self.current_metric, [])
        info = METRIC_INFO[self.current_metric]
        self.sparkline.set_data(data, info['color'])

        if data:
            cur, mn, mx = data[-1], min(data), max(data)
            avg = round(sum(data) / len(data), 1)
            self.current_lbl.findChild(QLabel, "val").setText(f"{cur} {info['unit']}")
            self.min_lbl.findChild(QLabel, "val").setText(str(mn))
            self.max_lbl.findChild(QLabel, "val").setText(str(mx))
            self.avg_lbl.findChild(QLabel, "val").setText(str(avg))
