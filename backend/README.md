# Backend — ICU Smart Monitoring (FastAPI)

## Lancement

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Structure

```
app/
├── main.py            entrée FastAPI (routers + lifespan)
├── config.py          settings (.env)
├── core/              logging, sécurité (JWT, bcrypt)
├── acquisition/       sources de données (base, simulator, csv, manager)
├── ai/                pipeline IA
│   ├── schemas.py     VitalsSample, AgentResult, AISnapshot, Severity
│   ├── ecg_generator.py / ecg_analysis.py
│   ├── agents/        6 agents signal + décision + prédiction
│   └── orchestrator.py
├── alerts/            gestion des alertes (dédup, priorité, ack)
├── llm/gemini.py      résumés textuels OPTIONNELS (hors temps réel)
├── db/                modèles + session PostgreSQL (optionnel)
├── schemas/           DTO Pydantic (I/O API)
├── api/routes/        REST : auth, patients, alerts, ai + WebSocket /ws
├── realtime/          ConnectionManager + boucle de streaming
└── services/          MonitoringService (registre par patient)
```

## Endpoints principaux

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/health` | statut système |
| POST | `/api/auth/login` | JWT (admin seed) |
| GET | `/api/auth/me` | utilisateur courant |
| GET | `/api/ai/scenarios` | scénarios cliniques |
| POST | `/api/ai/scenario` | changer de scénario |
| POST | `/api/ai/summary/{id}` | résumé clinique (Gemini/local) |
| GET | `/api/patients` | patients monitorés |
| GET | `/api/patients/{id}/latest` | dernier snapshot IA |
| GET | `/api/alerts/{id}` | alertes actives |
| POST | `/api/alerts/ack` | acquitter une alerte |
| WS | `/ws?patient_id=…` | flux temps réel |

## Tests

```powershell
pytest
```

## Persistance & Gemini

Les deux sont **désactivés par défaut** : le backend tourne entièrement en
mémoire. Activer via `.env` (`DATABASE_URL`, `GEMINI_ENABLED=true`).
