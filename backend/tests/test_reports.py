"""
tests/test_reports.py
=====================
Tests du moteur de rapports et des scores cliniques.
"""

import time

from app.ai.schemas import VitalsSample
from app.ai.orchestrator import AIAgentOrchestrator
from app.llm.report_generator import ReportGenerator


def make_sample(**overrides) -> VitalsSample:
    base = dict(
        patient_id="ICU-204", ts=time.time(), scenario="normal",
        ecg_hr=72, spo2=98, rr_capno=16, nibp_sys=120, nibp_dia=80,
        temp_core=37.2, ecg_rhythm="normal", etco2=40, vent_mode="VCV",
        vent_fio2=21, vent_peep=5.0, vent_vt=500, vent_rr=12, vent_pip=20.0,
        vent_mv=6.0, vent_pplat=15.0, cvp=5.0, co=5.0, ci=2.8,
        icp=8.0, bis=85, gcs=15, uo_hour=50, lab_k=4.0, lab_cr=1.0,
        lab_hb=11.0, lab_wbc=9.0, lab_plt=200, abg_ph=7.38, abg_pao2=90,
        abg_paco2=40, abg_hco3=24, abg_sat=97, abg_be=0, coag_inr=1.1,
        lab_na=140, lab_glu=100, fio2=21, nibp_map=90, nibp_pulse=72,
        nibp_cycle=15, temp_skin=34.5, temp_gradient=2.7, pi=2.5,
        pleth_amp=10.0, ecg_qual=0.95, ecg_st=0.0, ecg_qt=400,
        ecg_pvcs=0, ecg_waveform_type="II",
    )
    base.update(overrides)
    return VitalsSample(**base)


def test_clinical_scores_are_computed():
    orch = AIAgentOrchestrator()
    snap = orch.run(make_sample())
    score_names = [s.name for s in snap.decision.clinical_scores]
    assert "SOFA" in score_names
    assert "qSOFA" in score_names
    assert "NEWS2" in score_names


def test_reports_generated():
    orch = AIAgentOrchestrator()
    snap = orch.run(make_sample())
    types = [r.report_type for r in snap.reports]
    assert "progress" in types
    assert "nursing" in types


def test_report_generator_progress_markdown():
    gen = ReportGenerator()
    orch = AIAgentOrchestrator()
    snap = orch.run(make_sample())
    md = gen.generate_progress_note(snap)
    assert "# NOTE DE PROGRÈS" in md
    assert "SOFA" in md
    assert "NEWS2" in md


def test_report_family_summary_markdown():
    gen = ReportGenerator()
    orch = AIAgentOrchestrator()
    snap = orch.run(make_sample(scenario="sepsis", nibp_sys=80, temp_core=39.5, lab_wbc=3.5))
    md = gen.generate_family_summary(snap)
    assert "RÉSUMÉ POUR LA FAMILLE" in md
    assert "sepsis" in md.lower() or "sepsis" in md or "infection" in md.lower()
