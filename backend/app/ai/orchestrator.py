"""
app/ai/orchestrator.py
======================
Orchestrateur multi-agent avancé pour moniteur ICU complet.

Pipeline par tick :
  1. Acquisition : échantillon VitalsSample complet
  2. Agents par paramètre : ECG, SpO2+/PI, NIBP, RR, Temp, ETCO2, Ventilation, Hémodynamie, Neuro, Labo
  3. Scoring clinique : SOFA, qSOFA, NEWS2, Braden, CAM-ICU, sepsis surrogate
  4. Décision clinique : diagnostic probable, action prioritaire
  5. Prédiction multi-risque : cardiaque, respiratoire, choc, sepsis, IRA, VAE
  6. Rapports auto : note de progrès, résumé transfert, note nursing, labo, famille, code status

100 % LOCAL — <20 ms/tick.
"""

from __future__ import annotations

from datetime import datetime

from app.ai.schemas import VitalsSample, AISnapshot, Severity, severity_rank, AgentResult, Decision, ClinicalScore, Prediction, Report
from app.ai.agents.base import AgentContext
from app.ai.agents.ecg_agent import ECGAgent
from app.ai.agents.heart_rate_agent import HeartRateAgent
from app.ai.agents.spo2_agent import SpO2Agent
from app.ai.agents.temperature_agent import TemperatureAgent
from app.ai.agents.blood_pressure_agent import BloodPressureAgent
from app.ai.agents.respiratory_agent import RespiratoryAgent
from app.ai.agents.ventilation_agent import VentilationAgent
from app.ai.agents.hemodynamic_agent import HemodynamicAgent
from app.ai.agents.neurological_agent import NeurologicalAgent
from app.ai.agents.lab_agent import LabAgent
from app.ai.agents.etco2_agent import Etco2Agent
from app.ai.agents.clinical_decision_agent import ClinicalDecisionAgent
from app.ai.agents.prediction_agent import PredictionAgent
from app.ai.clinical_scoring import ClinicalScoringEngine
from app.llm.report_generator import ReportGenerator


class AIAgentOrchestrator:
    def __init__(self) -> None:
        self._agents = {
            "ecg": ECGAgent(),
            "heart_rate": HeartRateAgent(),
            "spo2": SpO2Agent(),
            "temperature": TemperatureAgent(),
            "blood_pressure": BloodPressureAgent(),
            "respiratory": RespiratoryAgent(),
            "ventilation": VentilationAgent(),
            "hemodynamic": HemodynamicAgent(),
            "neurological": NeurologicalAgent(),
            "laboratory": LabAgent(),
            "etco2": Etco2Agent(),
        }
        self._decision_agent = ClinicalDecisionAgent()
        self._prediction_agent = PredictionAgent()
        self._scoring_engine = ClinicalScoringEngine()
        self._report_gen = ReportGenerator()
        self._ctx = AgentContext()

    def run(self, sample: VitalsSample) -> AISnapshot:
        # 1) Agents par signal
        agents_out = {key: agent.analyze(sample, self._ctx) for key, agent in self._agents.items()}

        # 2) Scores cliniques
        scores = self._scoring_engine.all_scores(sample)

        # 3) Décision clinique (avec scores)
        all_results = list(agents_out.values())
        decision = self._decision_agent.decide(all_results)
        decision.clinical_scores = scores

        # 4) Prédictions
        prediction = self._prediction_agent.predict(all_results, sample=sample)

        # 5) Rapports médicaux générés automatiquement
        snap_no_ts = AISnapshot(
            patient_id=sample.patient_id,
            ts=sample.ts,
            vitals=sample,
            agents=agents_out,
            decision=decision,
            prediction=prediction,
        )
        reports = self._generate_reports(snap_no_ts, scores)

        snap = AISnapshot(
            patient_id=sample.patient_id,
            ts=sample.ts,
            vitals=sample,
            agents=agents_out,
            decision=decision,
            prediction=prediction,
            reports=reports,
        )

        # 6) MàJ contexte pour tendances tick suivant
        self._ctx.prev = {
            "hr": sample.hr, "spo2": sample.spo2, "temp": sample.temp_core or sample.temp_skin or 37,
            "sbp": sample.nibp_sys, "rr": sample.rr_capno or sample.vent_rr or 16,
            "map_val": sample.map_val, "etco2": sample.etco2, "cvp": sample.cvp,
            "icp": sample.icp, "bis": sample.bis, "gcs": sample.gcs,
            "uo_hour": sample.uo_hour, "lab_k": sample.lab_k, "lab_cr": sample.lab_cr,
            "lab_wbc": sample.lab_wbc, "abg_ph": sample.abg_ph, "coag_inr": sample.coag_inr,
        }

        return snap

    def _generate_reports(self, snap: AISnapshot, scores: list[ClinicalScore]) -> list[Report]:
        reports = []
        now = datetime.now()

        # Rapport principal (progrès)
        progress_md = self._report_gen.generate_progress_note(snap)
        reports.append(Report(
            report_type="progress",
            patient_id=snap.patient_id,
            ts=snap.ts,
            content_md=progress_md,
            summary=f"Note de progrès — {snap.decision.diagnosis[:50]}",
            critical_flags=[a.detected_event for a in snap.agents.values() if a.severity in ("high", "critical")],
        ))

        # Rapport de transfert si gravité élevée
        if snap.decision.overall_severity in ("high", "critical"):
            reports.append(Report(
                report_type="transfer",
                patient_id=snap.patient_id,
                ts=snap.ts,
                content_md=self._report_gen.generate_transfer_summary(snap),
                summary="Résumé de transfert — patient instable",
                critical_flags=["TRANSFERT RECOMMANDÉ"],
            ))

        # Note nursing systématique
        reports.append(Report(
            report_type="nursing",
            patient_id=snap.patient_id,
            ts=snap.ts,
            content_md=self._report_gen.generate_nursing_note(snap),
            summary=f"Surveillance infirmière — {now.strftime('%H:%M')}",
            critical_flags=[],
        ))

        # Résumé famille si gravité
        if snap.decision.overall_severity in ("medium", "high", "critical"):
            reports.append(Report(
                report_type="family",
                patient_id=snap.patient_id,
                ts=snap.ts,
                content_md=self._report_gen.generate_family_summary(snap),
                summary="Résumé pour la famille — version simplifiée",
                critical_flags=[],
            ))

        # Code status (une fois par admission ou si changement)
        reports.append(Report(
            report_type="code_status",
            patient_id=snap.patient_id,
            ts=snap.ts,
            content_md=self._report_gen.generate_code_status(snap),
            summary="Document de code status — à compléter et signer",
            critical_flags=[],
        ))

        # Lab summary (si labs disponibles)
        if any([snap.vitals.lab_hb, snap.vitals.lab_wbc, snap.vitals.lab_cr]):
            reports.append(Report(
                report_type="lab",
                patient_id=snap.patient_id,
                ts=snap.ts,
                content_md=self._report_gen.generate_lab_summary(snap.vitals),
                summary="Résumé de laboratoire — hématologie, biochimie, gaz, coagulation",
                critical_flags=[],
            ))

        return reports
