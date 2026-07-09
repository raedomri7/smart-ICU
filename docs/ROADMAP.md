# Roadmap de développement — ICU Smart Monitoring

## Phase 0 — Fondations (fait)
- Architecture générale, structure de dossiers.
- Migration de la logique clinique validée (agents, générateur ECG, ranges).

## Phase 1 — MVP temps réel (CIBLE ACTUELLE)
- [x] Backend FastAPI : agents multi-agent + orchestrateur.
- [x] Pipeline d'acquisition (interface + simulateur + CSV).
- [x] Générateur ECG + détection pics R (NumPy) + segment anormal.
- [x] Gestion des alertes (dédup, priorité, acquittement).
- [x] WebSocket temps réel `/ws` (broadcast par patient) + REST.
- [x] Frontend Next.js : dashboard ECG temps réel, cartes vitales,
      décision clinique, prédiction, alertes, timeline.
- [x] Gemini optionnel désactivable ; auth JWT de base ; schéma PostgreSQL.

**Critère de sortie** : dashboard live de bout en bout en local, changement de
scénario clinique en direct, ECG qui surligne uniquement le segment anormal.

## Phase 2 — Persistance & robustesse
- Brancher PostgreSQL réel + migrations Alembic + repositories complets.
- Historique paginé (REST) et rejeu.
- Reconnexion WS automatique, backpressure, file de persistance.
- Tests unitaires agents (fixtures scénarios) + tests d'intégration API.
- CI (lint, types, tests) + Docker Compose (backend + db + frontend).

## Phase 3 — IA avancée (ML réel)
- Classifieur ECG CNN 1D (PyTorch) sur fenêtres de battements (MIT-BIH).
- Prédiction de dégradation par modèle (Scikit-Learn / gradient boosting)
  entraîné sur MIMIC-IV, remplaçant les règles derrière la même interface.
- Calibration des scores de confiance ; évaluation (AUROC, sensibilité).

## Phase 4 — Intégration matériel réel
- Adaptateurs de sources : moniteurs patients (HL7 / protocoles constructeurs),
  lecture WFDB (PhysioNet), passerelles API hospitalières.
- Multi-patient temps réel à l'échelle (une boucle par lit, supervision globale).

## Phase 5 — Produit clinique
- RBAC complet, audit trail, gestion des équipes/services.
- Notifications (push, escalade), règles d'alerte configurables par service.
- Rapports PDF, export, tableau de bord superviseur multi-lits.
- Conformité (traçabilité, sécurité des données de santé).
