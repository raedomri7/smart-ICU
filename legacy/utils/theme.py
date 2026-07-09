"""
utils/theme.py
================
Dark futuristic ICU medical theme.
Color palette + reusable Qt stylesheet helpers.
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

COLORS = {
    'bg_primary':    '#050a0f',
    'bg_secondary':  '#080e15',
    'bg_card':       '#0a1520',
    'bg_card2':      '#0c1a28',
    'bg_header':     '#0d2235',
    'green':         '#00ff88',
    'cyan':          '#00e5ff',
    'blue':          '#0096ff',
    'red':           '#ff2244',
    'yellow':        '#ffcc00',
    'orange':        '#ff6600',
    'purple':        '#aa66ff',
    'text':          '#c8e8ff',
    'text_dim':      '#6a9bbf',
    'text_faint':    '#3a5a7a',
    'border':        '#0d2a3e',
    'border_bright': '#1a4060',
}

# Severity levels (Normal / Low / Medium / High / Critical)
SEVERITY_COLORS = {
    'normal':   COLORS['green'],
    'low':      COLORS['blue'],
    'medium':   COLORS['yellow'],
    'high':     COLORS['orange'],
    'critical': COLORS['red'],
}

SEVERITY_ORDER = ['normal', 'low', 'medium', 'high', 'critical']

# Libellés affichés à l'écran (FR) pour chaque niveau de sévérité interne
SEVERITY_LABELS_FR = {
    'normal':   'NORMAL',
    'low':      'FAIBLE',
    'medium':   'MOYEN',
    'high':     'ÉLEVÉ',
    'critical': 'CRITIQUE',
}


def severity_label_fr(severity: str) -> str:
    return SEVERITY_LABELS_FR.get(severity, severity.upper())


def apply_dark_theme(window: QWidget):
    """Apply global dark palette + stylesheet to the main window."""
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(COLORS['bg_primary']))
    palette.setColor(QPalette.WindowText, QColor(COLORS['text']))
    palette.setColor(QPalette.Base, QColor(COLORS['bg_card']))
    palette.setColor(QPalette.Text, QColor(COLORS['text']))
    palette.setColor(QPalette.Button, QColor(COLORS['bg_card']))
    palette.setColor(QPalette.ButtonText, QColor(COLORS['text']))
    palette.setColor(QPalette.Highlight, QColor(COLORS['cyan']))
    window.setPalette(palette)

    window.setStyleSheet(f"""
        QMainWindow {{ background: {COLORS['bg_primary']}; }}
        QWidget {{ color: {COLORS['text']}; }}
        QToolTip {{
            background: {COLORS['bg_card2']};
            color: {COLORS['cyan']};
            border: 1px solid {COLORS['border_bright']};
            padding: 6px 10px;
            border-radius: 4px;
            font-family: 'Courier New';
            font-size: 11px;
        }}
        QScrollBar:vertical {{
            background: {COLORS['bg_card']};
            width: 6px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {COLORS['border_bright']};
            border-radius: 3px;
            min-height: 20px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
    """)


def panel_style():
    return f"""
        QWidget {{
            background: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: 10px;
        }}
    """


def button_style(active=False):
    if active:
        return f"""
            QPushButton {{
                background: rgba(0,229,255,0.12);
                color: {COLORS['cyan']};
                border: 1px solid {COLORS['cyan']};
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                padding: 4px 10px;
            }}
            QPushButton:hover {{ background: rgba(0,229,255,0.2); }}
        """
    return f"""
        QPushButton {{
            background: rgba(0,150,255,0.06);
            color: {COLORS['text_dim']};
            border: 1px solid {COLORS['border_bright']};
            border-radius: 4px;
            font-size: 11px;
            padding: 4px 10px;
        }}
        QPushButton:hover {{
            background: rgba(0,229,255,0.1);
            color: {COLORS['cyan']};
            border-color: {COLORS['cyan']};
        }}
    """


def severity_badge_style(severity: str):
    color = SEVERITY_COLORS.get(severity, COLORS['green'])
    return f"""
        color: {color};
        background: rgba(255,255,255,0.04);
        border: 1px solid {color};
        border-radius: 8px;
        font-size: 10px;
        font-weight: bold;
        letter-spacing: 1px;
        padding: 2px 8px;
    """
