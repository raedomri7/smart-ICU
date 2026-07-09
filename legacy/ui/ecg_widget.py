"""
ui/ecg_widget.py
=================
Widget d'affichage ECG temps réel utilisant PyQtGraph.

Innovation clé (selon la spec) :
  - L'ECG normal reste toujours VERT.
  - SEUL le segment anormal du battement est rendu en ROUGE lumineux —
    le reste du tracé reste vert, jamais la ligne entière.
  - Un marqueur rouge lumineux + tooltip apparaît sur le segment anormal.
  - Sous l'ECG : Événement Détecté / Confiance / Sévérité / Signification Clinique.
"""

import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QComboBox, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QFont, QColor

try:
    import pyqtgraph as pg
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False

from utils.theme import COLORS, panel_style, button_style, SEVERITY_COLORS, severity_badge_style, severity_label_fr
from utils.ecg_generator import ECGGenerator, ECG_CLINICAL_INFO


WAVEFORM_OPTIONS = [
    ("Rythme Sinusal Normal (RSN)", 'normal'),
    ("Tachycardie", 'tachy'),
    ("Bradycardie", 'brady'),
    ("Fibrillation Auriculaire", 'afib'),
    ("ESV (Extrasystole Ventriculaire)", 'pvc'),
    ("Sus-décalage ST", 'st_elevation'),
    ("Sous-décalage ST", 'st_depression'),
    ("Tachycardie Ventriculaire", 'vtach'),
]


class ECGWidget(QWidget):
    def __init__(self, simulator):
        super().__init__()
        self.simulator = simulator
        self.ecg_gen = ECGGenerator()
        self.paused = False
        self.speed = 1.0
        self.current_waveform = "normal"
        self.buffer_size = 1000
        self.ecg_buffer = np.zeros(self.buffer_size)
        self.flag_buffer = np.zeros(self.buffer_size, dtype=bool)
        self._build_ui()
        self._start_animation()

    def _build_ui(self):
        self.setStyleSheet(panel_style())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ---------------- En-tête ----------------
        header = QWidget()
        header.setStyleSheet(f"background: rgba(0,150,255,0.03); border-bottom: 1px solid {COLORS['border']};")
        header.setFixedHeight(36)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 0, 12, 0)

        dot = QLabel("●")
        dot.setStyleSheet(f"color: {COLORS['cyan']}; font-size: 8px; border: none; background: transparent;")
        title = QLabel("ECG TEMPS RÉEL  —  DÉRIVATION II")
        title.setStyleSheet(f"color: {COLORS['cyan']}; font-size: 11px; font-weight: bold; letter-spacing: 2px; border: none; background: transparent;")

        self.rhythm_label = QLabel("Rythme : Sinusal Normal")
        self.rhythm_label.setStyleSheet(f"color: {COLORS['green']}; font-family: 'Courier New'; font-size: 11px; border: none; background: transparent;")

        self.hr_live = QLabel("FC : 72 bpm")
        self.hr_live.setStyleSheet(f"color: {COLORS['green']}; font-family: 'Courier New'; font-size: 13px; font-weight: bold; border: none; background: transparent;")

        h_layout.addWidget(dot)
        h_layout.addSpacing(6)
        h_layout.addWidget(title)
        h_layout.addStretch()
        h_layout.addWidget(self.rhythm_label)
        h_layout.addSpacing(20)
        h_layout.addWidget(self.hr_live)
        layout.addWidget(header)

        # ---------------- Tracé ECG ----------------
        if PYQTGRAPH_AVAILABLE:
            pg.setConfigOption('background', '#020810')
            pg.setConfigOption('foreground', '#00ff88')

            self.plot_widget = pg.PlotWidget()
            self.plot_widget.setBackground('#020810')
            self.plot_widget.showGrid(x=True, y=True, alpha=0.15)
            self.plot_widget.setYRange(-1.5, 2.0)
            self.plot_widget.getAxis('left').setStyle(tickFont=QFont('Courier New', 8))
            self.plot_widget.getAxis('bottom').setStyle(tickFont=QFont('Courier New', 8))
            self.plot_widget.getAxis('left').setPen(pg.mkPen(color='#1a4060'))
            self.plot_widget.getAxis('bottom').setPen(pg.mkPen(color='#1a4060'))
            self.plot_widget.setMinimumHeight(160)
            self.plot_widget.setMouseEnabled(x=False, y=False)

            # Courbe verte de base (tracé complet, toujours couleur normale)
            self.ecg_curve_normal = self.plot_widget.plot(
                pen=pg.mkPen(color='#00ff88', width=2)
            )

            # Courbe overlay : SEULEMENT le segment anormal, tracé en rouge avec glow
            self.ecg_curve_anomaly = self.plot_widget.plot(
                pen=pg.mkPen(color='#ff2244', width=3)
            )

            # Marqueur lumineux sur l'anomalie
            self.anomaly_marker = pg.ScatterPlotItem(
                size=14, brush=pg.mkBrush(255, 34, 68, 200),
                pen=pg.mkPen(color='#ff6680', width=2)
            )
            self.plot_widget.addItem(self.anomaly_marker)
            self.anomaly_marker.setData([], [])

            # Tooltip texte près de l'anomalie
            self.tooltip_item = pg.TextItem(
                "", color='#ff6680', anchor=(0, 1.4),
                fill=pg.mkBrush(10, 5, 8, 220)
            )
            self.tooltip_item.setFont(QFont('Courier New', 8))
            self.plot_widget.addItem(self.tooltip_item)
            self.tooltip_item.setVisible(False)

            layout.addWidget(self.plot_widget, 1)
        else:
            placeholder = QLabel("PyQtGraph non installé\nExécuter : pip install pyqtgraph")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 14px; min-height: 160px;")
            layout.addWidget(placeholder, 1)

        # ---------------- Bandeau d'info anomalie (sous l'ECG) ----------------
        self.info_strip = QWidget()
        self.info_strip.setFixedHeight(54)
        self.info_strip.setStyleSheet(f"background: rgba(0,0,0,0.25); border-top: 1px solid {COLORS['border']};")
        info_layout = QHBoxLayout(self.info_strip)
        info_layout.setContentsMargins(14, 6, 14, 6)
        info_layout.setSpacing(20)

        self.event_box = self._info_box("ÉVÉNEMENT DÉTECTÉ", "Normal", COLORS['green'])
        self.confidence_box = self._info_box("CONFIANCE", "98%", COLORS['green'])
        self.severity_box = self._info_box("SÉVÉRITÉ", "NORMAL", COLORS['green'])

        meaning_col = QVBoxLayout()
        meaning_title = QLabel("SIGNIFICATION CLINIQUE")
        meaning_title.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 9px; letter-spacing: 1.5px; border: none; background: transparent;")
        self.meaning_lbl = QLabel("Morphologie P-QRS-T régulière, axe normal.")
        self.meaning_lbl.setWordWrap(True)
        self.meaning_lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: 11px; border: none; background: transparent;")
        meaning_col.addWidget(meaning_title)
        meaning_col.addWidget(self.meaning_lbl)

        info_layout.addWidget(self.event_box)
        info_layout.addWidget(self.confidence_box)
        info_layout.addWidget(self.severity_box)
        info_layout.addLayout(meaning_col, 1)
        layout.addWidget(self.info_strip)

        # ---------------- Barre de contrôles ----------------
        controls = QWidget()
        controls.setStyleSheet(f"background: rgba(0,0,0,0.3); border-top: 1px solid {COLORS['border']};")
        controls.setFixedHeight(42)
        c_layout = QHBoxLayout(controls)
        c_layout.setContentsMargins(10, 4, 10, 4)
        c_layout.setSpacing(8)

        self.btn_pause = QPushButton("⏸  Pause")
        self.btn_pause.setStyleSheet(button_style(active=True))
        self.btn_pause.clicked.connect(self._toggle_pause)
        self.btn_pause.setFixedWidth(90)

        btn_reset = QPushButton("↺  Réinitialiser")
        btn_reset.setStyleSheet(button_style())
        btn_reset.clicked.connect(self._reset)
        btn_reset.setFixedWidth(110)

        wf_label = QLabel("Rythme :")
        wf_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none; background: transparent;")
        self.wf_combo = QComboBox()
        self.wf_combo.addItems([label for label, _ in WAVEFORM_OPTIONS])
        self.wf_combo.setStyleSheet(f"""
            QComboBox {{
                background: {COLORS['bg_card']};
                color: {COLORS['cyan']};
                border: 1px solid {COLORS['border_bright']};
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{
                background: {COLORS['bg_card']};
                color: {COLORS['text']};
                selection-background-color: {COLORS['bg_header']};
            }}
        """)
        self.wf_combo.currentIndexChanged.connect(self._change_waveform)
        self.wf_combo.setFixedWidth(220)

        speed_label = QLabel("Vitesse :")
        speed_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none; background: transparent;")

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(3, 20)
        self.speed_slider.setValue(10)
        self.speed_slider.setFixedWidth(80)
        self.speed_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{ height: 4px; background: {COLORS['border']}; border-radius: 2px; }}
            QSlider::handle:horizontal {{ width: 12px; height: 12px; background: {COLORS['cyan']}; border-radius: 6px; margin: -4px 0; }}
            QSlider::sub-page:horizontal {{ background: {COLORS['cyan']}; border-radius: 2px; }}
        """)
        self.speed_slider.valueChanged.connect(lambda v: setattr(self, 'speed', v / 10.0))

        self.speed_val_lbl = QLabel("1.0×")
        self.speed_val_lbl.setStyleSheet(f"color: {COLORS['text']}; font-family: 'Courier New'; font-size: 11px; border: none; background: transparent;")
        self.speed_slider.valueChanged.connect(lambda v: self.speed_val_lbl.setText(f"{v/10:.1f}×"))

        c_layout.addWidget(self.btn_pause)
        c_layout.addWidget(btn_reset)
        c_layout.addSpacing(10)
        c_layout.addWidget(wf_label)
        c_layout.addWidget(self.wf_combo)
        c_layout.addSpacing(10)
        c_layout.addWidget(speed_label)
        c_layout.addWidget(self.speed_slider)
        c_layout.addWidget(self.speed_val_lbl)
        c_layout.addStretch()

        layout.addWidget(controls)

    def _info_box(self, title, value, color):
        w = QWidget()
        w.setStyleSheet("border: none; background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(1)
        t = QLabel(title)
        t.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 9px; letter-spacing: 1.5px; border: none; background: transparent;")
        v = QLabel(value)
        v.setObjectName("value")
        v.setStyleSheet(f"color: {color}; font-family: 'Courier New'; font-size: 15px; font-weight: bold; border: none; background: transparent;")
        l.addWidget(t)
        l.addWidget(v)
        return w

    # ----------------------------------------------------------------
    def _start_animation(self):
        wave = self.ecg_gen.generate_waveform(self.current_waveform, self.buffer_size)
        self.ecg_buffer = wave
        self.flag_buffer = np.zeros(self.buffer_size, dtype=bool)

        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self._animate)
        self.anim_timer.start(33)  # ~30 fps

    def _animate(self):
        if self.paused or not PYQTGRAPH_AVAILABLE:
            return

        step = max(1, int(self.speed * 5))
        new_samples = self.ecg_gen.get_next_samples(self.current_waveform, step)
        new_flags = np.array(self.ecg_gen.get_last_anomaly_flags(), dtype=bool)

        self.ecg_buffer = np.roll(self.ecg_buffer, -step)
        self.ecg_buffer[-step:] = new_samples

        self.flag_buffer = np.roll(self.flag_buffer, -step)
        self.flag_buffer[-step:] = new_flags

        # Courbe de base : tracé complet toujours dessiné en vert
        x = np.arange(self.buffer_size)
        self.ecg_curve_normal.setData(x, self.ecg_buffer)

        # Overlay anomalie : SEULEMENT les échantillons anormaux, reste = NaN
        # pour que PyQtGraph coupe la ligne et ne relie pas les segments normaux
        if self.flag_buffer.any():
            anomaly_y = np.where(self.flag_buffer, self.ecg_buffer, np.nan)
            self.ecg_curve_anomaly.setData(x, anomaly_y, connect='finite')

            # Marqueur + tooltip sur le point anormal le plus récent
            anom_indices = np.where(self.flag_buffer)[0]
            if len(anom_indices) > 0:
                last_idx = anom_indices[-1]
                marker_x = [last_idx]
                marker_y = [self.ecg_buffer[last_idx]]
                self.anomaly_marker.setData(marker_x, marker_y)

                anomaly_type = self.ecg_gen.get_last_anomaly_type()
                info = ECG_CLINICAL_INFO.get(anomaly_type, {})
                tip_text = f"{anomaly_type}\nConf: {info.get('base_confidence', '--')}%"
                self.tooltip_item.setText(tip_text)
                self.tooltip_item.setPos(last_idx, self.ecg_buffer[last_idx])
                self.tooltip_item.setVisible(True)
            else:
                self.anomaly_marker.setData([], [])
                self.tooltip_item.setVisible(False)
        else:
            self.ecg_curve_anomaly.setData([], [])
            self.anomaly_marker.setData([], [])
            self.tooltip_item.setVisible(False)

    def _toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.btn_pause.setText("▶  Lecture")
            self.btn_pause.setStyleSheet(button_style(active=False))
        else:
            self.btn_pause.setText("⏸  Pause")
            self.btn_pause.setStyleSheet(button_style(active=True))

    def _reset(self):
        self.ecg_buffer = np.zeros(self.buffer_size)
        self.flag_buffer = np.zeros(self.buffer_size, dtype=bool)

    def _change_waveform(self, index):
        label, key = WAVEFORM_OPTIONS[index]
        self.current_waveform = key
        self.simulator.set_waveform(key)

        is_normal = (key == 'normal')
        rhythm_color = COLORS['green'] if is_normal else (
            COLORS['red'] if key in ('vtach', 'st_elevation') else COLORS['yellow']
        )
        self.rhythm_label.setText(f"Rythme : {label}")
        self.rhythm_label.setStyleSheet(f"color: {rhythm_color}; font-family: 'Courier New'; font-size: 11px; border: none; background: transparent;")

    # ----------------------------------------------------------------
    def update_from_agent(self, ecg_agent_result):
        """Appelé à chaque tick depuis main_window avec le résultat de l'ECGAgent."""
        severity = ecg_agent_result.severity
        color = SEVERITY_COLORS.get(severity, COLORS['green'])

        event_val = self.event_box.findChild(QLabel, "value")
        event_val.setText(ecg_agent_result.detected_event)
        event_val.setStyleSheet(f"color: {color}; font-family: 'Courier New'; font-size: 15px; font-weight: bold; border: none; background: transparent;")

        conf_val = self.confidence_box.findChild(QLabel, "value")
        conf_val.setText(f"{ecg_agent_result.confidence}%")
        conf_val.setStyleSheet(f"color: {color}; font-family: 'Courier New'; font-size: 15px; font-weight: bold; border: none; background: transparent;")

        sev_val = self.severity_box.findChild(QLabel, "value")
        sev_val.setText(severity_label_fr(severity))
        sev_val.setStyleSheet(f"color: {color}; font-family: 'Courier New'; font-size: 15px; font-weight: bold; border: none; background: transparent;")

        self.meaning_lbl.setText(ecg_agent_result.explanation)

        hr_color = COLORS['green'] if severity == 'normal' else color
        self.hr_live.setStyleSheet(f"color: {hr_color}; font-family: 'Courier New'; font-size: 13px; font-weight: bold; border: none; background: transparent;")

    def update_hr(self, hr):
        self.hr_live.setText(f"FC : {hr} bpm")
