# Schéma Base de Données — PostgreSQL

Moteur : PostgreSQL 15+ · ORM : SQLAlchemy 2.x (async) · Migrations : Alembic.

## Diagramme relationnel

```
┌──────────────┐        ┌────────────────────┐        ┌──────────────────┐
│    users     │        │      patients      │        │  vitals_samples  │
├──────────────┤        ├────────────────────┤        ├──────────────────┤
│ id (PK)      │        │ id (PK)            │◀──┐    │ id (PK)          │
│ email UNIQUE │        │ external_id UNIQUE │   │    │ patient_id (FK)  │──┐
│ full_name    │        │ full_name         │   └────│ ts (indexed)     │  │
│ hashed_pw    │        │ bed               │        │ hr, spo2, rr     │  │
│ role         │        │ age, sex          │        │ temp             │  │
│ is_active    │        │ admitted_at       │        │ sbp, dbp, map    │  │
│ created_at   │        │ status            │        │ rhythm           │  │
└──────────────┘        │ created_at        │        │ overall_severity │  │
                        └─────────┬──────────┘        │ risk_score       │  │
                                  │                   └──────────────────┘  │
                                  │                                          │
                                  │        ┌──────────────────┐             │
                                  ├───────▶│      alerts      │             │
                                  │        ├──────────────────┤             │
                                  │        │ id (PK)          │             │
                                  │        │ patient_id (FK)  │             │
                                  │        │ signal           │             │
                                  │        │ event            │             │
                                  │        │ severity         │             │
                                  │        │ confidence       │             │
                                  │        │ message          │             │
                                  │        │ status           │ (active/ack/resolved)
                                  │        │ acknowledged_by  │──▶ users.id │
                                  │        │ created_at       │             │
                                  │        │ resolved_at      │             │
                                  │        └──────────────────┘             │
                                  │                                          │
                                  │        ┌──────────────────────┐         │
                                  └───────▶│  ai_snapshots        │         │
                                           ├──────────────────────┤         │
                                           │ id (PK)              │         │
                                           │ patient_id (FK)      │         │
                                           │ sample_id (FK)       │─────────┘
                                           │ ts                   │
                                           │ decision (JSONB)     │
                                           │ prediction (JSONB)   │
                                           │ agents (JSONB)       │
                                           │ clinical_summary     │ (texte Gemini, nullable)
                                           └──────────────────────┘
```

## Tables

### users
| Colonne | Type | Notes |
|---|---|---|
| id | UUID PK | |
| email | text UNIQUE NOT NULL | login |
| full_name | text | |
| hashed_password | text NOT NULL | bcrypt |
| role | text NOT NULL DEFAULT 'clinician' | admin / clinician / viewer |
| is_active | bool DEFAULT true | |
| created_at | timestamptz DEFAULT now() | |

### patients
| Colonne | Type | Notes |
|---|---|---|
| id | UUID PK | |
| external_id | text UNIQUE | ex: "ICU-204" |
| full_name | text | |
| bed | text | |
| age | int | |
| sex | text | M/F/O |
| status | text DEFAULT 'monitored' | monitored / discharged |
| admitted_at | timestamptz | |
| created_at | timestamptz DEFAULT now() | |

### vitals_samples  (série temporelle — table la plus volumineuse)
| Colonne | Type | Notes |
|---|---|---|
| id | bigserial PK | |
| patient_id | UUID FK → patients | |
| ts | timestamptz NOT NULL | **index (patient_id, ts DESC)** |
| hr | int | |
| spo2 | int | |
| rr | int | |
| temp | numeric(3,1) | |
| sbp | int | |
| dbp | int | |
| map | int | calculé |
| rhythm | text | scénario ECG courant |
| overall_severity | text | résultat décision |
| risk_score | int | 0-100 |

> Partitionnement par `ts` (mensuel) recommandé en production. ECG brut non stocké
> par tick (volumineux) : conservé en buffer mémoire, échantillonné à la demande.

### alerts
| Colonne | Type | Notes |
|---|---|---|
| id | UUID PK | |
| patient_id | UUID FK | |
| signal | text | ECG / SpO2 / ... |
| event | text | ex: "Hypoxémie Sévère" |
| severity | text | low/medium/high/critical |
| confidence | int | 0-100 |
| message | text | |
| status | text DEFAULT 'active' | active / acknowledged / resolved |
| acknowledged_by | UUID FK → users NULL | |
| created_at | timestamptz DEFAULT now() | index |
| resolved_at | timestamptz NULL | |

### ai_snapshots
| Colonne | Type | Notes |
|---|---|---|
| id | UUID PK | |
| patient_id | UUID FK | |
| sample_id | bigint FK → vitals_samples NULL | |
| ts | timestamptz | |
| decision | JSONB | diagnostic, action, risque |
| prediction | JSONB | horizons + risques spécifiques |
| agents | JSONB | snapshot des AgentResult |
| clinical_summary | text NULL | enrichissement Gemini (async) |

## Index clés
- `vitals_samples (patient_id, ts DESC)` — historique/graphes.
- `alerts (patient_id, status, created_at DESC)` — panneau alertes actives.
- `ai_snapshots (patient_id, ts DESC)`.

## Rétention
- `vitals_samples` : haute résolution 72 h, puis downsampling (1/min) au-delà.
- `ai_snapshots` : conserver les snapshots avec `overall_severity >= high`.
