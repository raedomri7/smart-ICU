"""
app/ai/schemas.py
=================
Schémas étendus pour simulateur de moniteur de réanimation innovant.

Paramètres réels d'un moniteur ICU (Philips/GE/Dräger) :
- ECG avancé : HR, rythme, ST, QT, PVCs, arythmies
- SpO2+ : SpO2, PR, indice de perfusion (PI), pléthysmographe
- NIBP : SYS, DIA, MAP, Pulsée, mesure cycle/temps
- Température : Core (œsophagien/vésical), peau, gradient
- Capnométrie : ETCO2, RR (capno), FiO2, SpO2 (déjà)
- Ventilation : Mode, FiO2, PEEP, Vt, RR vent., PIP, MV, I:E, Pplat
- Hémodynamie : PAP (PAS/PAD/MAP), PCWP, CVP, CO, CI, SV, SVR
- Neurologie : ICP, CPP, BIS, GCS
- Diurèse : UO mL/h, cumul 6h/24h
- Labs : BMP (Na,K,Cr,BUN,Glu), CBC (Hb,Hct,WBC,Plt), ABG (pH,PaO2,PaCO2,HCO3,Sat,O2), Coag (PT/INR, aPTT, Plt)
- Scores cliniques : SOFA, qSOFA, NEWS2, Braden, Morse, Braden Q, CAM-ICU

Gravité : normal/low/medium/high/critical
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time


class Severity(str, Enum):
    NORMAL = "normal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

SEVERITY_RANK: dict[str, int] = {
    Severity.NORMAL: 0,
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}


def severity_rank(sev: str) -> int:
    return SEVERITY_RANK.get(Severity(sev) if not isinstance(sev, Severity) else sev, 0)


@dataclass
class VitalsSample:
    """Échantillon physiologique complet d'un moniteur ICU réel."""
    # Métadonnées
    patient_id: str
    ts: float  # epoch seconds
    scenario: str = "normal"

    # ECG avancé
    ecg_hr: int = 0  # bpm (source ECG)
    ecg_rhythm: str = "normal"
    ecg_st: float = 0.0  # mm décalage ST (positif = elevation, négatif = depression)
    ecg_qt: int = 0  # ms
    ecg_pvcs: int = 0  # extrasystoles ventriculaires / min
    ecg_qual: float = 0.0  # 0-100% qualité signal

    # SpO2 amélioré
    hr: int = 0  # bpm (source pléth)
    spo2: int = 98  # %
    pi: float = 0.0  # perfusion index 0-10%
    pleth_amp: float = 0.0  # amplitude pléth % 0-100

    # NIBP (Non-Invasive Blood Pressure)
    nibp_sys: int = 0
    nibp_dia: int = 0
    nibp_map: int = 0
    nibp_pulse: int = 0
    nibp_cycle: int = 15  # minutes entre mesures
    nibp_mode: str = "auto"  # auto / manual

    # Température
    temp_core: float = 0.0  # °C (œsophagien/vésical)
    temp_skin: float = 0.0  # °C
    temp_gradient: float = 0.0  # °C core-skin

    # Capnométrie (ETCO2)
    etco2: int = 0  # mmHg 35-45 normal
    rr_capno: int = 0  # /min depuis ETCO2
    fio2: int = 21  # % O2 inspiré

    # Ventilation mécanique
    vent_mode: str = "VCV"  # VCV, PCV, PSV, CPAP, SIMV, APRV, PRVC
    vent_fio2: int = 21
    vent_peep: float = 5.0  # cmH2O
    vent_vt: int = 500  # mL
    vent_rr: int = 12  # /min
    vent_pip: float = 20.0  # cmH2O
    vent_mv: float = 6.0  # L/min (minute volume)
    vent_ie: str = "1:2"  # ratio I:E
    vent_pplat: float = 15.0  # cmH2O pression plateau
    vent_trigger: str = "flow"  # flow / pressure

    # Hémodynamie avancée (PAC/ Swan-Ganz )
    pap_sys: int = 0  # mmHg
    pap_dia: int = 0
    pap_map: int = 0
    pcwp: float = 0.0  # mmHg (wedge)
    cvp: float = 0.0  # mmHg (central venous pressure)
    co: float = 0.0  # L/min (cardiac output)
    ci: float = 0.0  # L/min/m2 (cardiac index)
    sv: float = 0.0  # mL (stroke volume)
    svr: int = 0  # dyn.s.cm-5 (systemic vascular resistance)

    # Neurologie
    icp: float = 0.0  # mmHg (intracranial pressure) 0-15 normal
    cpp: float = 0.0  # mmHg (cerebral perfusion pressure = MAP - ICP)
    bis: int = 0  # 0-100 (bispectral index, sédation)
    gcs: int = 15  # Glasgow Coma Scale 3-15

    # Diurèse
    uo_hour: int = 0  # mL/h (urine output)
    uo_6h: int = 0  # mL/6h
    uo_24h: int = 0  # mL/24h

    # Labs (point-of-care / laboratoire)
    lab_na: float = 0.0  # mEq/L sodium
    lab_k: float = 0.0  # mEq/L potassium
    lab_cr: float = 0.0  # mg/dL creatinine
    lab_bun: float = 0.0  # mg/dL BUN
    lab_glu: float = 0.0  # mg/dL glucose
    lab_hb: float = 0.0  # g/dL hémoglobine
    lab_hct: float = 0.0  # % hématocrite
    lab_wbc: float = 0.0  # K/µL leucocytes
    lab_plt: float = 0.0  # K/µL plaquettes
    abg_ph: float = 0.0  # pH artériel 7.35-7.45
    abg_pao2: float = 0.0  # mmHg
    abg_paco2: float = 0.0  # mmHg
    abg_hco3: float = 0.0  # mEq/L
    abg_sat: float = 0.0  # % saturation O2 art.
    abg_be: float = 0.0  # base excess mEq/L
    coag_pt: float = 0.0  # sec
    coag_inr: float = 0.0
    coag_aptt: float = 0.0  # sec

    # ECG waveform samples (rolling buffer)
    ecg_samples: list[float] = field(default_factory=list)
    ecg_anomaly_flags: list[bool] = field(default_factory=list)
    ecg_anomaly_type: Optional[str] = None
    ecg_waveform_type: str = "II"  # Dérivation : II, V1, V5, aVR

    @property
    def abg_lactate_surrogate(self) -> float:
        """Surrogate lactate approximation via base excess (convention clinique)."""
        if self.abg_be:
            return max(0.0, -self.abg_be + 2.0)
        return 0.0

    def mobility_score(self) -> int:
        """Placeholder mobility score (0-4): 0=complète, 4=totalement dépendant."""
        if self.gcs and self.gcs <= 8:
            return 4
        if self.icp and self.icp > 20:
            return 3
        return 0

    @property
    def shock_risk_level(self) -> str:
        if self.nibp_sys > 0 and self.nibp_sys < 80:
            return "critical"
        if self.nibp_sys > 0 and self.nibp_sys < 90:
            return "high"
        return "normal"

    @property
    def map_val(self) -> int:
        return self.nibp_map if self.nibp_map > 0 else round(self.nibp_dia + (self.nibp_sys - self.nibp_dia) / 3)

    @property
    def spo2_percent(self) -> int:
        return self.spo2

    @property
    def hr_source(self) -> str:
        return "ECG" if self.ecg_hr > 0 else "PLETH"

    @property
    def cpp_val(self) -> float:
        if self.cpp and self.cpp > 0:
            return self.cpp
        if self.map_val > 0 and self.icp > 0:
            return max(0.0, self.map_val - self.icp)
        return 0.0


@dataclass
class AgentResult:
    agent_name: str
    signal: str
    value: str
    detected_event: str
    confidence: int  # 0-100
    severity: str
    explanation: str
    recommendation: str
    trend: str = "stable"  # rising / falling / stable
    details: dict = field(default_factory=dict)


@dataclass
class ClinicalScore:
    name: str
    score: int
    max_score: int
    severity: str
    interpretation: str


@dataclass
class Decision:
    overall_severity: str
    diagnosis: str
    recommended_action: str
    top_signal: str
    contributing: list[str]
    clinical_scores: list[ClinicalScore] = field(default_factory=list)


@dataclass
class Prediction:
    cardiac_arrest_risk: int
    respiratory_failure_risk: int
    shock_risk: int
    deterioration_risk: int
    sepsis_risk: int
    aki_risk: int
    vae_risk: int
    horizons: dict[str, int] = field(default_factory=dict)


@dataclass
class Report:
    report_type: str
    patient_id: str
    ts: float
    content_md: str
    summary: str
    critical_flags: list[str] = field(default_factory=list)


@dataclass
class AISnapshot:
    patient_id: str
    ts: float
    vitals: VitalsSample
    agents: dict[str, AgentResult]
    decision: Decision
    prediction: Prediction
    reports: list[Report] = field(default_factory=list)

    def to_public_dict(self) -> dict:
        return {
            "patient_id": self.patient_id,
            "ts": self.ts,
            "vitals": _serialize_vitals(self.vitals),
            "ecg": {
                "samples": self.vitals.ecg_samples,
                "anomaly": self.vitals.ecg_anomaly_flags,
                "anomaly_type": self.vitals.ecg_anomaly_type,
            },
            "agents": {k: _serialize_agent(v) for k, v in self.agents.items()},
            "decision": _serialize_decision(self.decision),
            "prediction": _serialize_prediction(self.prediction),
            "reports": [_serialize_report(r) for r in self.reports],
        }


def _serialize_vitals(v: VitalsSample) -> dict:
    d = {
        "ecg_hr": v.ecg_hr,
        "ecg_rhythm": v.ecg_rhythm,
        "ecg_st": v.ecg_st,
        "hr": v.hr,
        "spo2": v.spo2,
        "pi": v.pi,
        "nibp_sys": v.nibp_sys,
        "nibp_dia": v.nibp_dia,
        "nibp_map": v.nibp_map,
        "temp_core": v.temp_core,
        "temp_skin": v.temp_skin,
        "etco2": v.etco2,
        "rr_capno": v.rr_capno,
        "fio2": v.fio2,
        "vent_mode": v.vent_mode,
        "vent_peep": v.vent_peep,
        "vent_vt": v.vent_vt,
        "vent_rr": v.vent_rr,
        "vent_mv": v.vent_mv,
        "vent_pplat": v.vent_pplat,
        "cvp": v.cvp,
        "co": v.co,
        "ci": v.ci,
        "icp": v.icp,
        "cpp": v.cpp,
        "bis": v.bis,
        "gcs": v.gcs,
        "uo_hour": v.uo_hour,
        "lab_k": v.lab_k,
        "lab_cr": v.lab_cr,
        "lab_hb": v.lab_hb,
        "lab_wbc": v.lab_wbc,
        "abg_ph": v.abg_ph,
        "abg_pao2": v.abg_pao2,
        "abg_paco2": v.abg_paco2,
        "coag_inr": v.coag_inr,
        "scenario": v.scenario,
    }
    d["map_val"] = v.map_val
    d["cpp_val"] = v.cpp_val
    d["ecg_samples"] = v.ecg_samples
    d["ecg_anomaly_flags"] = v.ecg_anomaly_flags
    d["ecg_anomaly_type"] = v.ecg_anomaly_type
    return d


def _serialize_agent(a: AgentResult) -> dict:
    return {
        "agent_name": a.agent_name,
        "signal": a.signal,
        "value": a.value,
        "detected_event": a.detected_event,
        "confidence": a.confidence,
        "severity": a.severity,
        "explanation": a.explanation,
        "recommendation": a.recommendation,
        "trend": a.trend,
        "details": a.details,
    }


def _serialize_decision(d: Decision) -> dict:
    return {
        "overall_severity": d.overall_severity,
        "diagnosis": d.diagnosis,
        "recommended_action": d.recommended_action,
        "top_signal": d.top_signal,
        "contributing": d.contributing,
        "clinical_scores": [
            {"name": s.name, "score": s.score, "max_score": s.max_score,
             "severity": s.severity, "interpretation": s.interpretation}
            for s in d.clinical_scores
        ],
    }


def _serialize_prediction(p: Prediction) -> dict:
    return {
        "cardiac_arrest_risk": p.cardiac_arrest_risk,
        "respiratory_failure_risk": p.respiratory_failure_risk,
        "shock_risk": p.shock_risk,
        "deterioration_risk": p.deterioration_risk,
        "sepsis_risk": p.sepsis_risk,
        "aki_risk": p.aki_risk,
        "vae_risk": p.vae_risk,
        "horizons": p.horizons,
    }


def _serialize_report(r: Report) -> dict:
    return {
        "report_type": r.report_type,
        "patient_id": r.patient_id,
        "ts": r.ts,
        "content_md": r.content_md,
        "summary": r.summary,
        "critical_flags": r.critical_flags,
    }
