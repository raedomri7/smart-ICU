"""
utils/report_generator.py
============================
Génère un rapport PDF médical résumant l'état actuel du patient, les
signes vitaux, les résultats des agents IA et la sortie de l'aide à
la décision clinique.

Utilise reportlab. Affiche un message si la librairie n'est pas installée.
"""

import os
from datetime import datetime


def generate_pdf_report(patient_id, vitals, ai_summary=None, output_dir=None):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.pdfgen import canvas
    except ImportError:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.warning(None, "Dépendance manquante",
                             "reportlab n'est pas installé.\nExécutez : pip install reportlab")
        return None

    if output_dir is None:
        output_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.isdir(output_dir):
            output_dir = os.getcwd()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"Rapport_ICU_{patient_id}_{timestamp}.pdf")

    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # En-tête
    c.setFillColorRGB(0.0, 0.05, 0.08)
    c.rect(0, height - 90, width, 90, fill=1, stroke=0)
    c.setFillColorRGB(0, 0.9, 1)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(20 * mm, height - 35 * mm, "SYSTÈME DE MONITORING ICU INTELLIGENT PAR IA")
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.6, 0.8, 0.9)
    c.drawString(20 * mm, height - 42 * mm, "Plateforme d'Intelligence Biomédicale — Rapport Clinique")

    y = height - 100 * mm + 10 * mm

    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, f"ID Patient : {patient_id}")
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y - 6 * mm, f"Rapport généré le : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    y -= 18 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "Aperçu des Signes Vitaux")
    y -= 8 * mm

    c.setFont("Helvetica", 10)
    rows = [
        ("Fréquence Cardiaque", f"{vitals.get('hr', '--')} bpm"),
        ("SpO2", f"{vitals.get('spo2', '--')} %"),
        ("Fréquence Respiratoire", f"{vitals.get('rr', '--')} /min"),
        ("Température", f"{vitals.get('temp', '--')} °C"),
        ("Pression Artérielle", f"{vitals.get('sbp', '--')}/{vitals.get('dbp', '--')} mmHg"),
    ]
    for label, val in rows:
        c.drawString(22 * mm, y, f"{label} :")
        c.drawString(80 * mm, y, val)
        y -= 6 * mm

    if ai_summary:
        decision = ai_summary.get('decision', {})
        prediction = ai_summary.get('prediction', {})

        y -= 10 * mm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20 * mm, y, "Aide à la Décision Clinique (IA)")
        y -= 8 * mm
        c.setFont("Helvetica", 10)
        c.drawString(22 * mm, y, f"Sévérité Globale : {decision.get('overall_severity', '--').upper()}")
        y -= 6 * mm
        c.drawString(22 * mm, y, f"Diagnostic : {decision.get('diagnosis', '--')[:90]}")
        y -= 6 * mm
        c.drawString(22 * mm, y, f"Action Recommandée : {decision.get('recommended_action', '--')[:90]}")
        y -= 10 * mm

        c.setFont("Helvetica-Bold", 11)
        c.drawString(20 * mm, y, "Prédiction (Risque de Détérioration par Horizon)")
        y -= 7 * mm
        c.setFont("Helvetica", 10)
        for h, val in prediction.get('horizons', {}).items():
            c.drawString(22 * mm, y, f"{h} min : {val}%")
            y -= 6 * mm

    c.setFont("Helvetica-Oblique", 8)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(20 * mm, 15 * mm, "Outil d'aide à la décision clinique uniquement. Ne remplace pas le jugement médical professionnel.")

    c.save()

    from PyQt5.QtWidgets import QMessageBox
    QMessageBox.information(None, "Rapport Exporté", f"Rapport PDF enregistré dans :\n{filename}")
    return filename
