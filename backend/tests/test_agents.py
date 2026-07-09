"""
tests/test_agents.py
====================
Tests unitaires des agents IA — sans DB ni réseau.
Lancer : pytest
"""

import time

from app.ai.schemas import VitalsSample, Severity
from app.ai.orchestrator import AIAgentOrchestrator


def make_sample(**overrides) -> VitalsSample:
    base = dict(
        patient_id="TEST",
        ts=time.time(),
        scenario="normal",
        ecg_hr=72,
        spo2=98,
        rr_capno=16,
        nibp_sys=120,
        nibp_dia=80,
        temp_core=37.2,
        ecg_rhythm="normal",
        etco2=40,
        vent_mode="VCV",
        vent_fio2=21,
        vent_peep=5.0,
        vent_vt=500,
        vent_rr=12,
        vent_pip=20.0,
        vent_mv=6.0,
        vent_pplat=15.0,
        cvp=5.0,
        co=5.0,
        ci=2.8,
        icp=8.0,
        bis=85,
        gcs=15,
        uo_hour=50,
        lab_k=4.0,
        lab_cr=1.0,
        lab_hb=11.0,
        lab_wbc=9.0,
        lab_plt=200,
        abg_ph=7.38,
        abg_pao2=90,
        abg_paco2=40,
        abg_hco3=24,
        abg_sat=97,
        abg_be=0,
        coag_inr=1.1,
        lab_na=140,
        lab_glu=100,
        fio2=21,
        nibp_map=90,
        nibp_pulse=72,
        nibp_cycle=15,
        temp_skin=34.5,
        temp_gradient=2.7,
        pi=2.5,
        pleth_amp=10.0,
        ecg_qual=0.95,
        ecg_st=0.0,
        ecg_qt=400,
        ecg_pvcs=0,
        ecg_waveform_type="II",
    )
    base.update(overrides)
    return VitalsSample(**base)


def test_normal_patient_is_stable():
    orch = AIAgentOrchestrator()
    snap = orch.run(make_sample())
    assert snap.decision.overall_severity == Severity.NORMAL.value


def test_septic_shock_pattern():
    orch = AIAgentOrchestrator()
    snap = orch.run(make_sample(
        ecg_hr=130, spo2=91, rr_capno=26, temp_core=39.2,
        nibp_sys=78, nibp_dia=48, scenario="sepsis", lab_wbc=3.0, lab_cr=2.5
    ))
    assert snap.decision.overall_severity == Severity.CRITICAL.value
    assert any("Choc" in c for c in snap.decision.contributing)


def test_vtach_is_critical_and_predicts_high_cardiac_risk():
    orch = AIAgentOrchestrator()
    snap = orch.run(make_sample(
        ecg_hr=190, spo2=86, nibp_sys=70, nibp_dia=45,
        scenario="vtach"
    ))
    assert snap.decision.overall_severity == Severity.CRITICAL.value
    assert snap.prediction.cardiac_arrest_risk > 40
    for h in ("5", "15", "30", "60"):
        assert h in snap.prediction.horizons


def test_prediction_horizons_are_monotonic_nondecreasing():
    orch = AIAgentOrchestrator()
    snap = orch.run(make_sample(ecg_hr=125, spo2=93, rr_capno=22, scenario="tachy"))
    h = snap.prediction.horizons
    assert h["5"] <= h["15"] <= h["30"] <= h["60"]
