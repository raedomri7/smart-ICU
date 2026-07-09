# Système de Monitoring ICU Intelligent par IA v4.3.0

Plateforme de monitoring ICU avec architecture multi-agents IA.
Application desktop Python / PyQt5 — interface entièrement en français.

## 🚀 Installation

```bash
# 1. Créer un environnement virtuel (recommandé)
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer l'application
python main.py
```

## 📁 Structure du projet

```
icu_project_fr/
├── main.py                      # Point d'entrée
├── requirements.txt
├── ui/
│   ├── main_window.py           # Fenêtre principale — assemble tous les panneaux
│   ├── ecg_widget.py            # ECG temps réel — surlignage SEGMENT anormal uniquement
│   ├── vitals_panel.py          # 5 cartes vitales animées + interprétation IA
│   ├── ai_panel.py              # Panneau Insights IA — jauge de risque global
│   ├── decision_panel.py        # Aide à la Décision Clinique + Prédiction multi-horizon
│   ├── alerts_panel.py          # Alertes 5 niveaux (Normal/Faible/Moyen/Élevé/Critique)
│   ├── patient_panel.py         # Liste patients classés par IA + statut système
│   └── timeline_panel.py        # Timeline événements cliniques
└── utils/
    ├── theme.py                 # Palette de couleurs + styles Qt + libellés FR
    ├── ecg_generator.py         # Générateur de formes d'onde ECG synthétiques
    ├── ai_agents.py             # ★ Architecture multi-agents IA (cœur du système)
    ├── patient_simulator.py     # Orchestre simulation + agents IA à chaque tick
    ├── report_generator.py      # Export PDF (reportlab)
    └── data_manager.py          # Sauvegarde JSON de l'historique patient
```

## 🤖 Architecture des agents IA (utils/ai_agents.py)

Chaque signal physiologique a son propre agent indépendant :

| Agent | Détecte |
|---|---|
| `ECGAgent` | Tachycardie, Bradycardie, Fibrillation Auriculaire, ESV, Sus/Sous-décalage ST, Tachycardie Ventriculaire |
| `HeartRateAgent` | Anomalies de fréquence cardiaque |
| `SpO2Agent` | Hypoxémie légère/sévère |
| `TemperatureAgent` | Fièvre, hyperpyrexie, hypothermie |
| `BloodPressureAgent` | Hypotension, hypertension, risque de choc |
| `RespiratoryAgent` | Tachypnée, bradypnée, détresse respiratoire |

Chaque agent retourne un `AgentResult` : événement détecté, confiance (%),
sévérité (normal/low/medium/high/critical — affichée en FR via
`severity_label_fr()`), explication clinique, action recommandée, et
tendance (rising/falling/stable).

Deux agents d'agrégation :

- **`ClinicalDecisionAgent`** — combine tous les résultats → diagnostic
  probable (ex: "Possible Choc Septique", "Possible STEMI") + action prioritaire.
- **`PredictionAgent`** — estime le risque de détérioration à 5/15/30/60 min,
  ainsi que les risques spécifiques (arrêt cardiaque, défaillance respiratoire, choc).

> Note technique : les clés de sévérité internes (`normal`, `low`, `medium`,
> `high`, `critical`) restent en anglais dans le code (logique, dictionnaires,
> comparaisons) — seul ce qui s'affiche à l'écran est traduit en français,
> via `utils/theme.py::severity_label_fr()`.

## 🎨 Fonctionnalités clés

- **ECG intelligent** : la trace reste VERTE en permanence. Seul le segment
  anormal devient ROUGE (avec glow + marqueur + tooltip), jamais toute la ligne.
- **Cartes vitales** avec ligne d'interprétation IA et code couleur
  spécifique (température : bleu hypothermie / vert normal / orange fièvre / rouge forte fièvre).
- **Alertes dynamiques** générées en temps réel à partir des agents (pas de
  table statique) avec confiance affichée.
- **Aide à la Décision Clinique** : diagnostic inféré, niveau de risque,
  action recommandée, fenêtres de prédiction 5/15/30/60 min.
- **Timeline patient** : historique chronologique des événements significatifs.
- **Export PDF** et **sauvegarde JSON** de l'historique.

## 🧪 Tester la logique IA sans interface graphique

```bash
python3 -c "
from utils.ai_agents import AIAgentOrchestrator
orch = AIAgentOrchestrator()
vitals = {'hr': 130, 'spo2': 91, 'rr': 26, 'temp': 39.2, 'sbp': 145, 'dbp': 92}
result = orch.run(vitals, 'tachy', 'Tachycardie')
print(result['decision']['diagnosis'])
print(result['prediction']['horizons'])
"
```

## 📊 Datasets de référence (production)

Le système est conçu pour être branché sur de vraies données :
- **PhysioNet**
- **MIMIC-IV**
- **MIT-BIH Arrhythmia Database**

Actuellement, `utils/patient_simulator.py` génère des données synthétiques
réalistes. Pour brancher un vrai dataset, remplacer `PatientSimulator.step()`
par une lecture de fichiers WFDB (`pip install wfdb`) — l'interface des
agents IA reste identique.

## ⚠️ Avertissement

Ce système est un **outil d'aide à la décision clinique** et ne remplace
en aucun cas le jugement médical professionnel.
