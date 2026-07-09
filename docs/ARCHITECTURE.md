# ICU Smart Monitoring — Architecture Générale

> Plateforme IA de surveillance intelligente pour unités de réanimation.
> Acquisition temps réel → traitement IA multi-agent local → décision clinique → alertes → visualisation.

---

## 1. Vue d'ensemble

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              SOURCES DE DONNÉES                            │
│   Moniteur patient réel │ Simulateur │ Fichiers CSV │ API médicales        │
└───────────────────────────────────┬──────────────────────────────────────┘
                                     │  (adapter pattern — interface unique)
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        BACKEND — FastAPI (Python)                         │
│                                                                            │
│  ┌────────────┐   ┌────────────────┐   ┌───────────────┐   ┌───────────┐  │
│  │ ACQUISITION│──▶│ TRAITEMENT IA  │──▶│   DÉCISION    │──▶│  ALERTES  │  │
│  │  Pipeline  │   │ (multi-agent)  │   │  CLINIQUE     │   │  Manager  │  │
│  │            │   │ local, <5ms    │   │  + Prédiction │   │           │  │
│  └────────────┘   └────────────────┘   └───────────────┘   └─────┬─────┘  │
│         │                  │                    │                 │        │
│         ▼                  ▼                    ▼                 ▼        │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │              PERSISTENCE — PostgreSQL (SQLAlchemy async)            │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                     │                                      │
│         REST API  ◀──────────────── │ ──────────────▶  WebSocket /ws       │
│    (CRUD, historique, auth)         │            (flux vitals + IA temps réel)
│                                     ▼                                      │
│                       Gemini API (OPTIONNEL, asynchrone)                   │
│          résumés cliniques / explications texte — JAMAIS temps réel        │
└───────────────────────────────────┬──────────────────────────────────────┘
                                     │  REST (HTTP) + WebSocket (WSS)
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    FRONTEND — Next.js (TypeScript)                         │
│  TailwindCSS · Framer Motion · Recharts · WebSocket client                 │
│                                                                            │
│  Dashboard ICU : ECG temps réel · Cartes vitales · Alertes · Décision      │
│  clinique · Prédiction multi-horizon · Timeline                            │
└──────────────────────────────────────────────────────────────────────────┘
```

**Principe directeur** : la détection d'anomalies et les calculs de gravité sont
**100 % locaux et synchrones** (NumPy / règles / ML léger) pour garantir une latence
faible. Gemini n'intervient **jamais** dans la boucle temps réel — uniquement en
tâche de fond pour enrichir les explications textuelles.

---

## 2. Séparation des responsabilités (couches)

| Couche | Responsabilité | Ne fait PAS |
|---|---|---|
| **Acquisition** | Normaliser toute source en un `VitalsSample` unifié | Détection, décision |
| **Traitement IA** | Agents par signal → anomalie, confiance, gravité, explication | Persistence, transport |
| **Décision clinique** | Fusionner les résultats → diagnostic, risque global | Acquisition |
| **Prédiction** | Estimer la dégradation à 5/15/30/60 min | Décision instantanée |
| **Alertes** | Dédupliquer, prioriser, router, acquitter | Calcul de gravité |
| **Transport** | REST (CRUD/historique) + WebSocket (flux) | Logique métier |
| **Persistence** | PostgreSQL : patients, samples, alertes, users | Logique métier |
| **Affichage** | Rendu React, animations, graphes | Aucune logique clinique |

---

## 3. Structure des dossiers

```
icu_project_fr/
├── docs/
│   ├── ARCHITECTURE.md          # ce document
│   ├── DATABASE.md              # schéma PostgreSQL détaillé
│   └── ROADMAP.md               # phases de développement
│
├── backend/
│   ├── app/
│   │   ├── main.py              # entrée FastAPI (routers + lifespan)
│   │   ├── config.py           # settings (pydantic-settings, .env)
│   │   │
│   │   ├── core/               # infra transverse
│   │   │   ├── logging.py
│   │   │   └── security.py     # JWT, hash password
│   │   │
│   │   ├── acquisition/        # PIPELINE D'ACQUISITION
│   │   │   ├── base.py         # DataSource (interface abstraite)
│   │   │   ├── simulator.py    # source simulée (migre patient_simulator)
│   │   │   ├── csv_source.py   # rejoue un CSV
│   │   │   └── manager.py      # sélection + boucle d'acquisition async
│   │   │
│   │   ├── ai/                 # PIPELINE DE TRAITEMENT IA (multi-agent)
│   │   │   ├── schemas.py      # AgentResult, Severity (dataclasses/enums)
│   │   │   ├── ecg_generator.py# formes d'onde ECG (migré)
│   │   │   ├── ecg_analysis.py # détection pics R + anomalies (NumPy)
│   │   │   ├── agents/
│   │   │   │   ├── base.py
│   │   │   │   ├── ecg_agent.py
│   │   │   │   ├── heart_rate_agent.py
│   │   │   │   ├── spo2_agent.py
│   │   │   │   ├── blood_pressure_agent.py
│   │   │   │   ├── respiratory_agent.py
│   │   │   │   ├── temperature_agent.py
│   │   │   │   ├── clinical_decision_agent.py
│   │   │   │   └── prediction_agent.py
│   │   │   └── orchestrator.py # exécute tous les agents / tick
│   │   │
│   │   ├── alerts/             # GESTION DES ALERTES
│   │   │   └── manager.py      # dédup, priorité, acquittement
│   │   │
│   │   ├── llm/                # Gemini (OPTIONNEL, hors temps réel)
│   │   │   └── gemini.py       # résumés / explications async, cache
│   │   │
│   │   ├── db/                 # PERSISTENCE
│   │   │   ├── session.py      # engine async SQLAlchemy
│   │   │   ├── models.py       # tables ORM
│   │   │   └── repositories.py # accès data
│   │   │
│   │   ├── schemas/            # DTO Pydantic (I/O API)
│   │   │   ├── vitals.py
│   │   │   ├── ai.py
│   │   │   ├── alert.py
│   │   │   └── auth.py
│   │   │
│   │   ├── api/                # TRANSPORT REST
│   │   │   ├── deps.py
│   │   │   └── routes/
│   │   │       ├── patients.py
│   │   │       ├── vitals.py
│   │   │       ├── alerts.py
│   │   │       ├── ai.py
│   │   │       └── auth.py
│   │   │
│   │   ├── realtime/           # TRANSPORT WEBSOCKET
│   │   │   ├── connection.py   # ConnectionManager (broadcast par patient)
│   │   │   └── stream.py       # boucle: acquisition→IA→broadcast+persist
│   │   │
│   │   └── services/           # orchestration métier
│   │       └── monitoring.py
│   │
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
└── frontend/
    ├── app/                    # Next.js App Router
    │   ├── layout.tsx
    │   ├── page.tsx            # redirection → /dashboard
    │   ├── globals.css
    │   └── dashboard/
    │       └── page.tsx        # dashboard principal
    ├── components/
    │   ├── ecg/EcgChart.tsx        # ECG temps réel + segment anormal
    │   ├── vitals/
    │   │   ├── HeartRateCard.tsx
    │   │   ├── Spo2Card.tsx
    │   │   ├── BloodPressureCard.tsx
    │   │   ├── RespiratoryCard.tsx
    │   │   └── TemperatureCard.tsx
    │   ├── clinical/
    │   │   ├── DecisionPanel.tsx
    │   │   └── PredictionPanel.tsx
    │   ├── alerts/AlertsPanel.tsx
    │   ├── timeline/TimelinePanel.tsx
    │   └── ui/                  # primitives (Card, Badge, Gauge, Trend)
    ├── lib/
    │   ├── types.ts            # types TS partagés (miroir des DTO)
    │   ├── api.ts              # client REST
    │   ├── useWebSocket.ts     # hook flux temps réel
    │   └── format.ts
    ├── package.json
    ├── tailwind.config.ts
    ├── tsconfig.json
    └── next.config.mjs
```

---

## 4. Architecture IA multi-agent

```
                         VitalsSample (tick ~1s)
                                  │
        ┌───────────┬───────────┬─┴─────────┬───────────┬───────────┐
        ▼           ▼           ▼           ▼           ▼           ▼
   ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
   │  ECG   │  │  Heart │  │  SpO2  │  │ Blood  │  │ Resp.  │  │  Temp  │
   │ Agent  │  │  Rate  │  │ Agent  │  │Pressure│  │ Agent  │  │ Agent  │
   └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘
       │           │           │           │           │           │
       └───────────┴─────┬─────┴───────────┴───────────┴───────────┘
                         ▼   List[AgentResult]
              ┌────────────────────────┐
              │ Clinical Decision Agent│  diagnostic, risque global, action
              └───────────┬────────────┘
                          ▼
              ┌────────────────────────┐
              │    Prediction Agent    │  arrêt cardiaque / détresse resp. /
              │                        │  choc / dégradation — 5/15/30/60 min
              └───────────┬────────────┘
                          ▼
                 AISnapshot (broadcast WS + persist)
```

**Contrat commun d'un agent** (`ai/agents/base.py`) :

```python
class Agent(Protocol):
    name: str
    def analyze(self, sample: VitalsSample, ctx: AgentContext) -> AgentResult: ...
```

`AgentResult` : `signal, detected_event, value, confidence(0-100), severity
(normal|low|medium|high|critical), explanation, recommendation, trend`.

Les agents sont **purs et déterministes** (mêmes entrées → mêmes sorties, hors
bruit contrôlé), testables unitairement sans I/O. `AgentContext` porte les valeurs
précédentes (pour la tendance) et une courte fenêtre glissante.

**Extensibilité** : ajouter un signal = 1 nouvelle classe `XAgent(base.Agent)` +
enregistrement dans l'orchestrateur. Aucun autre fichier à toucher.

**Évolution ML** : chaque agent expose `analyze()` par règles aujourd'hui ; demain
un agent peut charger un modèle Scikit-Learn/PyTorch (`.pkl`/`.pt`) derrière la même
signature. L'ECG en particulier migrera vers un classifieur CNN 1D (PyTorch) sur
fenêtres de battements, l'interface restant identique.

---

## 5. Flux temps réel

```
 boucle async (par patient monitoré), période T ≈ 1s
 ───────────────────────────────────────────────────
 1. source.read()                → VitalsSample (+ fenêtre ECG)
 2. orchestrator.run(sample)     → AISnapshot   (LOCAL, synchrone, <5ms)
 3. alerts.evaluate(snapshot)    → nouvelles alertes / résolutions
 4. ws.broadcast(patient_id, …)  → tous les clients abonnés
 5. repo.persist(sample, snap)   → PostgreSQL (batch/async, non bloquant)
 6. (async, découplé) gemini.enrich() si activé → texte enrichi, push différé
```

- **WebSocket** = canal chaud : chaque tick pousse `{vitals, ecg_chunk, agents,
  decision, prediction, alerts}`.
- **REST** = canal froid : login, liste patients, historique paginé, acquittement
  d'alerte, déclenchement d'un résumé Gemini.
- La persistence n'est jamais sur le chemin critique du broadcast (fire-and-forget
  avec file interne).

---

## 6. Schéma de communication (messages WS)

```
Client ──▶ Server   { "type": "subscribe",   "patient_id": "ICU-204" }
Client ──▶ Server   { "type": "set_source",  "mode": "simulator", "scenario": "vtach" }
Client ──▶ Server   { "type": "ack_alert",   "alert_id": "..." }

Server ──▶ Client   { "type": "tick", "ts": ..., "patient_id": ...,
                      "vitals": {...}, "ecg": {"samples":[...],"anomaly":[...]},
                      "agents": {...}, "decision": {...}, "prediction": {...} }
Server ──▶ Client   { "type": "alert",  "alert": {...} }
Server ──▶ Client   { "type": "clinical_summary", "text": "...", "source":"gemini" }
```

Tous les payloads sont typés côté backend (Pydantic) et côté frontend (`lib/types.ts`).

---

## 7. Gestion des utilisateurs (auth)

- JWT (access token) via `/api/auth/login`, mot de passe hashé (bcrypt).
- Rôles : `admin`, `clinician`, `viewer` (RBAC simple sur les routes).
- WebSocket authentifié par token en query param, vérifié à la connexion.
- MVP : un utilisateur seed `admin` ; extensible vers gestion complète.

---

## 8. Bonnes pratiques production

- **Config par environnement** via `.env` (pydantic-settings), jamais de secret en dur.
- **Gemini désactivable** (`GEMINI_ENABLED=false`) — le système fonctionne 100 % sans.
- **Sécurité clinique** : bandeau « aide à la décision, ne remplace pas le jugement médical ».
- **Observabilité** : logs structurés, `/health`, latence par tick mesurée.
- **Tests** : agents IA testables sans DB ni réseau ; fixtures de scénarios cliniques.
- **Migrations** : Alembic pour PostgreSQL.
- **Découplage** : acquisition ↔ IA ↔ transport communiquent par DTO, pas d'import croisé.
- **Résilience** : reconnexion WS auto côté client, backpressure côté serveur.
