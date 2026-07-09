"""
ui/vitals_panel.py
===================
Panneau des Signes Vitaux - 5 cartes médicales animées avec ligne
d'interprétation IA par signe (pilotée par les agents IA dédiés).

Logique de couleur :
    Fréquence Cardiaque : vert (normal) -> jaune (alerte) -> rouge (critique)
    SpO2 :        vert / jaune (90-94) / rouge (<90)
    Respiration :  vert / jaune / rouge
    Température : bleu (hypothermie) / vert (normal) / orange (fièvre) / rouge (forte fièvre)
    Pression Artérielle : vert / jaune / rouge
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QGraphicsOpacityEffect
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation
from utils.theme import COLORS, panel_style, SEVERITY_COLORS, severity_label_fr


class VitalCard(QWidget):
    """Carte unique pour un signe vital avec icône animée + ligne d'interprétation IA."""

    def __init__(self, icon, label, unit, color, animated_icon=False):
        super().__init__()
        self.base_color = color
        self.animated_icon = animated_icon
        self.blink_state = True
        self._anim_speed_ms = 800
        self._build_ui(icon, label, unit, color)

        self._blink_timer = QTimer()
        self._blink_timer.timeout.connect(self._blink)

        if animated_icon:
            self._icon_timer = QTimer()
            self._icon_timer.timeout.connect(self._pulse_icon)
            self._icon_timer.start(self._anim_speed_ms)
            self._pulse_state = False

    def _build_ui(self, icon, label, unit, color):
        self.setStyleSheet(f"""
            QWidget {{
                background: {COLORS['bg_card']};
                border-right: 1px solid {COLORS['border']};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignCenter)

        self.icon_lbl = QLabel(icon)
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setStyleSheet("font-size: 18px; border: none; background: transparent;")

        lbl = QLabel(label)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 9px; letter-spacing: 1px; border: none; background: transparent;")

        self.value_lbl = QLabel("--")
        self.value_lbl.setAlignment(Qt.AlignCenter)
        self.value_lbl.setStyleSheet(f"""
            color: {color}; font-family: 'Courier New'; font-size: 26px;
            font-weight: bold; border: none; background: transparent;
        """)

        unit_lbl = QLabel(unit)
        unit_lbl.setAlignment(Qt.AlignCenter)
        unit_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 9px; border: none; background: transparent;")

        self.status_lbl = QLabel("NORMAL")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setFixedHeight(18)
        self.status_lbl.setStyleSheet(self._badge_style('normal'))

        # Ligne d'interprétation IA
        self.ai_line_lbl = QLabel("IA : stable")
        self.ai_line_lbl.setAlignment(Qt.AlignCenter)
        self.ai_line_lbl.setWordWrap(True)
        self.ai_line_lbl.setStyleSheet(f"color: {COLORS['text_faint']}; font-size: 8px; border: none; background: transparent; margin-top: 2px;")

        layout.addWidget(self.icon_lbl)
        layout.addWidget(lbl)
        layout.addWidget(self.value_lbl)
        layout.addWidget(unit_lbl)
        layout.addWidget(self.status_lbl)
        layout.addWidget(self.ai_line_lbl)

    def _badge_style(self, severity):
        color = SEVERITY_COLORS.get(severity, COLORS['green'])
        return f"""
            color: {color}; background: rgba(255,255,255,0.04);
            border: 1px solid {color}; border-radius: 8px;
            font-size: 9px; font-weight: bold; letter-spacing: 1px; padding: 1px 6px;
        """

    def set_value(self, value, severity='normal', ai_text="", override_color=None, trend="stable"):
        self.value_lbl.setText(str(value))
        color = override_color or SEVERITY_COLORS.get(severity, self.base_color)

        trend_arrow = {'rising': ' ↑', 'falling': ' ↓', 'stable': ''}.get(trend, '')
        self.value_lbl.setStyleSheet(f"""
            color: {color}; font-family: 'Courier New'; font-size: 26px;
            font-weight: bold; border: none; background: transparent;
        """)
        self.status_lbl.setText(severity_label_fr(severity) + trend_arrow)
        self.status_lbl.setStyleSheet(self._badge_style(severity))
        if ai_text:
            self.ai_line_lbl.setText(f"IA : {ai_text}")

        if severity == 'critical':
            if not self._blink_timer.isActive():
                self._blink_timer.start(550)
        else:
            self._blink_timer.stop()
            self.status_lbl.setVisible(True)

        # Ajuste la vitesse de pulsation de l'icône selon la sévérité (carte FC uniquement)
        if self.animated_icon and hasattr(self, '_icon_timer'):
            if severity == 'critical':
                interval = 250
            elif severity in ('high', 'medium'):
                interval = 450
            else:
                interval = 800
            self._icon_timer.setInterval(interval)

    def _blink(self):
        self.blink_state = not self.blink_state
        self.status_lbl.setVisible(self.blink_state)

    def _pulse_icon(self):
        self._pulse_state = not self._pulse_state
        scale = "font-size: 22px;" if self._pulse_state else "font-size: 18px;"
        self.icon_lbl.setStyleSheet(f"{scale} border: none; background: transparent;")


class VitalsPanel(QWidget):
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
        dot.setStyleSheet(f"color: {COLORS['cyan']}; font-size: 8px; border: none; background: transparent;")
        title = QLabel("MONITEUR DES SIGNES VITAUX")
        title.setStyleSheet(f"color: {COLORS['cyan']}; font-size: 11px; font-weight: bold; letter-spacing: 2px; border: none; background: transparent;")
        self.updated_lbl = QLabel("Dernière mise à jour : --")
        self.updated_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; font-family: 'Courier New'; border: none; background: transparent;")
        h_layout.addWidget(dot)
        h_layout.addSpacing(6)
        h_layout.addWidget(title)
        h_layout.addStretch()
        h_layout.addWidget(self.updated_lbl)
        layout.addWidget(header)

        cards_widget = QWidget()
        cards_widget.setStyleSheet(f"background: {COLORS['bg_card']};")
        cards_layout = QHBoxLayout(cards_widget)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(0)

        self.hr_card = VitalCard("❤️", "FRÉQ. CARDIAQUE", "bpm", COLORS['green'], animated_icon=True)
        self.spo2_card = VitalCard("🩸", "SpO₂", "%", COLORS['cyan'])
        self.rr_card = VitalCard("🫁", "RESPIRATION", "resp/min", COLORS['blue'])
        self.temp_card = VitalCard("🌡️", "TEMPÉRATURE", "°C", COLORS['cyan'])
        self.bp_card = VitalCard("💉", "PRESSION ARTÉRIELLE", "mmHg", COLORS['cyan'])

        for card in [self.hr_card, self.spo2_card, self.rr_card, self.temp_card, self.bp_card]:
            cards_layout.addWidget(card, 1)

        layout.addWidget(cards_widget)

    def update_vitals(self, vitals, agents=None):
        """
        vitals: dict avec hr, spo2, rr, temp, sbp, dbp
        agents: dict optionnel de AgentResult issu de
                ai_agents.AIAgentOrchestrator (heart_rate, spo2, respiratory,
                temperature, blood_pressure)
        """
        from PyQt5.QtCore import QDateTime
        self.updated_lbl.setText(f"Mis à jour : {QDateTime.currentDateTime().toString('hh:mm:ss')}")

        hr, spo2, rr, temp, sbp, dbp = (
            vitals['hr'], vitals['spo2'], vitals['rr'],
            vitals['temp'], vitals['sbp'], vitals['dbp']
        )

        if agents:
            hr_r = agents['heart_rate']
            self.hr_card.set_value(hr, hr_r.severity, hr_r.explanation.split('—')[-1].strip()[:45], trend=hr_r.trend)

            spo2_r = agents['spo2']
            self.spo2_card.set_value(spo2, spo2_r.severity, spo2_r.explanation.split('—')[-1].strip()[:45], trend=spo2_r.trend)

            rr_r = agents['respiratory']
            self.rr_card.set_value(rr, rr_r.severity, rr_r.explanation.split('—')[-1].strip()[:45], trend=rr_r.trend)

            temp_r = agents['temperature']
            # Logique de couleur spéciale Température : hypothermie = bleu, fièvre = orange, forte fièvre = rouge
            if temp_r.detected_event in ('Hypothermie', 'Hypothermie Sévère'):
                override = COLORS['blue']
            elif temp_r.detected_event == 'Fièvre':
                override = COLORS['orange']
            elif temp_r.detected_event in ('Forte Fièvre', 'Hyperpyrexie'):
                override = COLORS['red']
            else:
                override = None
            self.temp_card.set_value(f"{temp:.1f}", temp_r.severity, temp_r.explanation.split('—')[-1].strip()[:45],
                                       override_color=override, trend=temp_r.trend)

            bp_r = agents['blood_pressure']
            self.bp_card.set_value(f"{sbp}/{dbp}", bp_r.severity, bp_r.explanation.split('—')[-1].strip()[:45], trend=bp_r.trend)
            self.bp_card.value_lbl.setStyleSheet(
                self.bp_card.value_lbl.styleSheet().replace("font-size: 26px", "font-size: 19px")
            )
        else:
            # Repli sur seuils simples si les agents ne sont pas fournis
            self.hr_card.set_value(hr, 'critical' if hr > 120 or hr < 45 else ('medium' if hr > 100 or hr < 60 else 'normal'))
            self.spo2_card.set_value(spo2, 'critical' if spo2 < 90 else ('medium' if spo2 < 95 else 'normal'))
            self.rr_card.set_value(rr, 'critical' if rr < 8 or rr > 28 else ('medium' if rr < 12 or rr > 20 else 'normal'))
            self.temp_card.set_value(f"{temp:.1f}", 'normal')
            self.bp_card.set_value(f"{sbp}/{dbp}", 'normal')
