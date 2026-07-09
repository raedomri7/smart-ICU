"""
ui/decision_panel.py
======================
Panneau d'Aide à la Décision Clinique.

Agrège les sorties du ClinicalDecisionAgent et du PredictionAgent :
    - Diagnostic possible
    - Niveau de risque global
    - Action recommandée
    - Prédictions de détérioration multi-horizon (5/15/30/60 min)
    - Détail des agents contributeurs par signal
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt
from utils.theme import COLORS, panel_style, SEVERITY_COLORS, severity_badge_style, severity_label_fr


class RiskHorizonBox(QWidget):
    """Petite boîte affichant le % de risque à un horizon temporel donné."""

    def __init__(self, horizon_label):
        super().__init__()
        self.setStyleSheet(f"""
            QWidget {{
                background: rgba(255,255,255,0.03);
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignCenter)

        self.horizon_lbl = QLabel(horizon_label)
        self.horizon_lbl.setAlignment(Qt.AlignCenter)
        self.horizon_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 9px; border: none; background: transparent;")

        self.value_lbl = QLabel("--%")
        self.value_lbl.setAlignment(Qt.AlignCenter)
        self.value_lbl.setStyleSheet(f"color: {COLORS['green']}; font-family: 'Courier New'; font-size: 16px; font-weight: bold; border: none; background: transparent;")

        layout.addWidget(self.horizon_lbl)
        layout.addWidget(self.value_lbl)

    def set_value(self, pct):
        self.value_lbl.setText(f"{pct}%")
        if pct >= 70:
            color = COLORS['red']
        elif pct >= 45:
            color = COLORS['orange']
        elif pct >= 20:
            color = COLORS['yellow']
        else:
            color = COLORS['green']
        self.value_lbl.setStyleSheet(f"color: {color}; font-family: 'Courier New'; font-size: 16px; font-weight: bold; border: none; background: transparent;")


class RiskMeter(QWidget):
    """Jauge horizontale étiquetée (arrêt cardiaque / défaillance resp. / choc)."""

    def __init__(self, label):
        super().__init__()
        self.setStyleSheet("border: none; background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.label_lbl = QLabel(label)
        self.label_lbl.setFixedWidth(130)
        self.label_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; border: none; background: transparent;")

        from PyQt5.QtWidgets import QProgressBar
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(6)
        self.bar.setStyleSheet(f"""
            QProgressBar {{ background: rgba(255,255,255,0.05); border: none; border-radius: 3px; }}
            QProgressBar::chunk {{ background: {COLORS['green']}; border-radius: 3px; }}
        """)

        self.val_lbl = QLabel("0%")
        self.val_lbl.setFixedWidth(36)
        self.val_lbl.setStyleSheet(f"color: {COLORS['green']}; font-family: 'Courier New'; font-size: 10px; border: none; background: transparent;")

        layout.addWidget(self.label_lbl)
        layout.addWidget(self.bar, 1)
        layout.addWidget(self.val_lbl)

    def set_value(self, pct):
        self.bar.setValue(pct)
        if pct >= 70:
            color = COLORS['red']
        elif pct >= 45:
            color = COLORS['orange']
        elif pct >= 20:
            color = COLORS['yellow']
        else:
            color = COLORS['green']
        self.bar.setStyleSheet(f"""
            QProgressBar {{ background: rgba(255,255,255,0.05); border: none; border-radius: 3px; }}
            QProgressBar::chunk {{ background: {color}; border-radius: 3px; }}
        """)
        self.val_lbl.setText(f"{pct}%")
        self.val_lbl.setStyleSheet(f"color: {color}; font-family: 'Courier New'; font-size: 10px; border: none; background: transparent;")


class DecisionPanel(QWidget):
    """Panneau d'Aide à la Décision Clinique + Module de Prédiction."""

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
        header.setStyleSheet(f"background: rgba(170,102,255,0.05); border-bottom: 1px solid {COLORS['border']};")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 0, 12, 0)
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {COLORS['purple']}; font-size: 8px; border: none; background: transparent;")
        title = QLabel("⚕  AIDE À LA DÉCISION CLINIQUE")
        title.setStyleSheet(f"color: {COLORS['purple']}; font-size: 11px; font-weight: bold; letter-spacing: 2px; border: none; background: transparent;")
        h_layout.addWidget(dot)
        h_layout.addSpacing(6)
        h_layout.addWidget(title)
        h_layout.addStretch()
        layout.addWidget(header)

        body = QWidget()
        body.setStyleSheet(f"background: {COLORS['bg_card']};")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(14, 10, 14, 10)
        body_layout.setSpacing(8)

        # Diagnostic possible
        diag_title = QLabel("DIAGNOSTIC POSSIBLE")
        diag_title.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 9px; letter-spacing: 2px; border: none; background: transparent;")
        self.diagnosis_lbl = QLabel("Aucune anomalie aiguë détectée. Patient stable.")
        self.diagnosis_lbl.setWordWrap(True)
        self.diagnosis_lbl.setStyleSheet(f"""
            color: {COLORS['text']};
            background: rgba(0,0,0,0.25);
            border-left: 3px solid {COLORS['green']};
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            padding: 8px 10px;
        """)

        # Badge de niveau de risque + action recommandée
        risk_row = QHBoxLayout()
        risk_label = QLabel("NIVEAU DE RISQUE :")
        risk_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; border: none; background: transparent;")
        self.risk_badge = QLabel("NORMAL")
        self.risk_badge.setStyleSheet(severity_badge_style('normal'))
        risk_row.addWidget(risk_label)
        risk_row.addWidget(self.risk_badge)
        risk_row.addStretch()

        action_title = QLabel("ACTION RECOMMANDÉE")
        action_title.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 9px; letter-spacing: 2px; border: none; background: transparent;")
        self.action_lbl = QLabel("Poursuivre la surveillance de routine.")
        self.action_lbl.setWordWrap(True)
        self.action_lbl.setStyleSheet(f"color: {COLORS['cyan']}; font-size: 12px; font-weight: 500; border: none; background: transparent;")

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {COLORS['border']}; max-height: 1px; border: none;")

        # Horizons de prédiction
        pred_title = QLabel("RISQUE DE DÉTÉRIORATION — HORIZON DE PRÉDICTION")
        pred_title.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 9px; letter-spacing: 1.5px; border: none; background: transparent;")

        horizon_row = QHBoxLayout()
        horizon_row.setSpacing(8)
        self.horizon_boxes = {}
        for h in [5, 15, 30, 60]:
            box = RiskHorizonBox(f"{h} MIN")
            self.horizon_boxes[h] = box
            horizon_row.addWidget(box)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"background: {COLORS['border']}; max-height: 1px; border: none;")

        # Jauges de risque spécifiques
        risks_title = QLabel("ESTIMATIONS DE RISQUE SPÉCIFIQUES")
        risks_title.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 9px; letter-spacing: 1.5px; border: none; background: transparent;")

        self.cardiac_arrest_meter = RiskMeter("Arrêt Cardiaque")
        self.resp_failure_meter = RiskMeter("Défaillance Respiratoire")
        self.shock_meter = RiskMeter("Choc")

        body_layout.addWidget(diag_title)
        body_layout.addWidget(self.diagnosis_lbl)
        body_layout.addLayout(risk_row)
        body_layout.addWidget(action_title)
        body_layout.addWidget(self.action_lbl)
        body_layout.addWidget(sep)
        body_layout.addWidget(pred_title)
        body_layout.addLayout(horizon_row)
        body_layout.addWidget(sep2)
        body_layout.addWidget(risks_title)
        body_layout.addWidget(self.cardiac_arrest_meter)
        body_layout.addWidget(self.resp_failure_meter)
        body_layout.addWidget(self.shock_meter)
        body_layout.addStretch()

        layout.addWidget(body, 1)

    def update_decision(self, ai_summary):
        decision = ai_summary.get('decision')
        prediction = ai_summary.get('prediction')
        if not decision or not prediction:
            return

        severity = decision['overall_severity']
        color = SEVERITY_COLORS.get(severity, COLORS['green'])

        self.diagnosis_lbl.setText(decision['diagnosis'])
        self.diagnosis_lbl.setStyleSheet(f"""
            color: {COLORS['text']};
            background: rgba(0,0,0,0.25);
            border-left: 3px solid {color};
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            padding: 8px 10px;
        """)

        self.risk_badge.setText(severity_label_fr(severity))
        self.risk_badge.setStyleSheet(severity_badge_style(severity))

        self.action_lbl.setText(decision['recommended_action'])

        for h, box in self.horizon_boxes.items():
            box.set_value(prediction['horizons'].get(h, 0))

        self.cardiac_arrest_meter.set_value(prediction['cardiac_arrest_risk'])
        self.resp_failure_meter.set_value(prediction['respiratory_failure_risk'])
        self.shock_meter.set_value(prediction['shock_risk'])
