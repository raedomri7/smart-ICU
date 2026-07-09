"""
utils/data_manager.py
========================
Couche de persistance légère pour sauvegarder l'historique patient.

En production (selon la spec d'architecture), ce module serait remplacé
par des écritures PostgreSQL via le backend FastAPI ; ici il persiste en
JSON local pour que l'application desktop reste totalement autonome.
"""

import json
import os
from datetime import datetime


def save_patient_history(patient_id, history_dict, output_dir=None):
    if output_dir is None:
        output_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.isdir(output_dir):
            output_dir = os.getcwd()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"Historique_ICU_{patient_id}_{timestamp}.json")

    serializable = {k: list(v) for k, v in history_dict.items()}
    payload = {
        'patient_id': patient_id,
        'exporte_le': datetime.now().isoformat(),
        'historique': serializable,
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    from PyQt5.QtWidgets import QMessageBox
    QMessageBox.information(None, "Historique Sauvegardé", f"Historique patient enregistré dans :\n{filename}")
    return filename


def load_patient_history(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)
