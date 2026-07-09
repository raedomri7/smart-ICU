"""
ui/ai_panel.py
===============
Panneau Insights IA — jauge de risque global + barres de confiance +
facteurs d'analyse. Alimenté par PatientSimulator.get_ai_prediction()
(résumé compatible construit au-dessus de l'orchestrateur multi-agents).
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QFrame
)
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from utils.theme import COLORS, panel_style


class RiskGauge(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(130, 130)
        self._risk = 0
        self._target_risk = 0
        self._color = QColor(COLORS['green'])
        self._anim_timer = QTimer()
        self._anim_timer.timeout.connect(self._animate)
        self._anim_timer.start(30)

    def set_risk(self, value, color_str):
        self._target_risk = value
        self._color = QColor(color_str)

    def _animate(self):
        diff = self._target_risk - self._risk
        if abs(diff) > 0.5:
            self._risk += diff * 0.08
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        cx, cy = W // 2, H // 2
        r = min(W, H) // 2 - 14

        painter.setPen(QPen(QColor(30, 50, 70), 10, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(cx - r, cy - r, r * 2, r * 2, 16 * 30, -16 * 300)

        angle_span = int(-300 * self._risk / 100 * 16)
        if angle_span != 0:
            painter.setPen(QPen(self._color, 10, Qt.SolidLine, Qt.RoundCap))
            painter.drawArc(cx - r, cy - r, r * 2, r * 2, 16 * (90 + 150), angle_span)

        painter.setPen(QPen(self._color))
        painter.setFont(QFont('Courier New', 20, QFont.Bold))
        painter.drawText(QRectF(0, cy - 22, W, 30), Qt.AlignCenter, f"{int(self._risk)}%")

        painter.setFont(QFont('Segoe UI', 8))
        painter.setPen(QPen(QColor(COLORS['text_dim'])))
        painter.drawText(QRectF(0, cy + 10, W, 16), Qt.AlignCenter, "SCORE DE RISQUE")
        painter.end()


class AIPredictionPanel(QWidget):
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
        dot.setStyleSheet(f"color: {COLORS['green']}; font-size: 8px; border: none; background: transparent;")
        title = QLabel("🤖  PANNEAU INSIGHTS IA")
        title.setStyleSheet(f"color: {COLORS['green']}; font-size: 11px; font-weight: bold; letter-spacing: 2px; border: none; background: transparent;")
        model_lbl = QLabel("Orchestrateur Multi-Agents")
        model_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; border: none; background: transparent;")
        h_layout.addWidget(dot)
        h_layout.addSpacing(4)
        h_layout.addWidget(title)
        h_layout.addStretch()
        h_layout.addWidget(model_lbl)
        layout.addWidget(header)

        body = QWidget()
        body.setStyleSheet(f"background: {COLORS['bg_card']};")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(12, 10, 12, 10)
        body_layout.setSpacing(8)

        top_row = QHBoxLayout()
        top_row.setSpacing(14)

        self.gauge = RiskGauge()
        top_row.addWidget(self.gauge)

        right_side = QVBoxLayout()
        right_side.setSpacing(6)

        self.pred_status = QLabel("🟢  État Stable")
        self.pred_status.setWordWrap(True)
        self.pred_status.setStyleSheet(f"""
            color: {COLORS['green']}; background: rgba(0,255,136,0.08);
            border: none; border-left: 3px solid {COLORS['green']};
            border-radius: 4px; font-size: 13px; font-weight: bold; padding: 6px 10px;
        """)

        conf_title = QLabel("CONFIANCE IA")
        conf_title.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 9px; letter-spacing: 2px; border: none; background: transparent;")

        self.conf_arrhythmia = self._conf_bar("Arythmie / ECG", 12, COLORS['green'])
        self.conf_deter = self._conf_bar("Détérioration", 8, COLORS['cyan'])
        self.conf_cardiac = self._conf_bar("Arrêt Cardiaque", 5, COLORS['yellow'])

        right_side.addWidget(self.pred_status)
        right_side.addWidget(conf_title)
        right_side.addLayout(self.conf_arrhythmia['layout'])
        right_side.addLayout(self.conf_deter['layout'])
        right_side.addLayout(self.conf_cardiac['layout'])

        top_row.addLayout(right_side, 1)
        body_layout.addLayout(top_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']}; background: {COLORS['border']}; max-height: 1px;")
        body_layout.addWidget(sep)

        factors_title = QLabel("FACTEURS D'ANALYSE IA")
        factors_title.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 9px; letter-spacing: 2px; border: none; background: transparent;")
        body_layout.addWidget(factors_title)

        self.factors = []
        for i in range(4):
            row = QHBoxLayout()
            row.setSpacing(8)
            dot_lbl = QLabel("●")
            dot_lbl.setFixedWidth(12)
            dot_lbl.setStyleSheet(f"color: {COLORS['green']}; font-size: 8px; border: none; background: transparent;")
            text_lbl = QLabel(f"Facteur {i+1}")
            text_lbl.setWordWrap(True)
            text_lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: 11px; border: none; background: transparent;")
            row.addWidget(dot_lbl)
            row.addWidget(text_lbl, 1)
            self.factors.append({'dot': dot_lbl, 'text': text_lbl})
            body_layout.addLayout(row)

        body_layout.addStretch()
        layout.addWidget(body, 1)

    def _conf_bar(self, label, value, color):
        layout = QHBoxLayout()
        layout.setSpacing(6)
        lbl = QLabel(label)
        lbl.setFixedWidth(95)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; border: none; background: transparent;")

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(value)
        bar.setFixedHeight(5)
        bar.setTextVisible(False)
        bar.setStyleSheet(f"""
            QProgressBar {{ background: rgba(255,255,255,0.05); border: none; border-radius: 2px; }}
            QProgressBar::chunk {{ background: {color}; border-radius: 2px; }}
        """)

        val_lbl = QLabel(f"{value}%")
        val_lbl.setFixedWidth(34)
        val_lbl.setStyleSheet(f"color: {color}; font-family: 'Courier New'; font-size: 10px; border: none; background: transparent;")

        layout.addWidget(lbl)
        layout.addWidget(bar, 1)
        layout.addWidget(val_lbl)
        return {'layout': layout, 'bar': bar, 'val': val_lbl}

    def update_prediction(self, prediction, vitals):
        risk = prediction['risk']
        status = prediction['status']
        conf = prediction['confidence']
        factors = prediction['factors']
        color = prediction['color']

        self.gauge.set_risk(risk, color)
        self.pred_status.setText(status)
        self.pred_status.setStyleSheet(f"""
            color: {color}; background: rgba(0,0,0,0.3);
            border: none; border-left: 3px solid {color};
            border-radius: 4px; font-size: 13px; font-weight: bold; padding: 6px 10px;
        """)

        conf_items = [self.conf_arrhythmia, self.conf_deter, self.conf_cardiac]
        conf_colors = [color, COLORS['cyan'], COLORS['yellow']]
        for i, item in enumerate(conf_items):
            v = max(0, min(100, conf[i]))
            item['bar'].setValue(v)
            item['val'].setText(f"{v}%")
            item['bar'].setStyleSheet(f"""
                QProgressBar {{ background: rgba(255,255,255,0.05); border: none; border-radius: 2px; }}
                QProgressBar::chunk {{ background: {conf_colors[i]}; border-radius: 2px; }}
            """)
            item['val'].setStyleSheet(f"color: {conf_colors[i]}; font-family: 'Courier New'; font-size: 10px; border: none; background: transparent;")

        dot_colors = {'green': COLORS['green'], 'yellow': COLORS['yellow'], 'red': COLORS['red']}
        for i, f in enumerate(factors[:4]):
            fc, ft = f
            self.factors[i]['dot'].setStyleSheet(f"color: {dot_colors.get(fc, COLORS['green'])}; font-size: 8px; border: none; background: transparent;")
            self.factors[i]['text'].setText(ft)
