/**
 * lib/types.ts
 * ============
 * Types partagés miroir des DTO Pydantic du backend (source de vérité unique
 * conceptuelle, dupliquée volontairement pour découpler les déploiements).
 */

export type Severity = "normal" | "low" | "medium" | "high" | "critical";
export type Trend = "rising" | "falling" | "stable";

export interface Vitals {
  // Cœur / SpO2
  hr: number;
  ecg_hr: number;
  spo2: number;
  // Pression artérielle (NIBP + champs legacy)
  sbp: number;
  dbp: number;
  map: number;
  nibp_sys: number;
  nibp_dia: number;
  nibp_map: number;
  map_val?: number;
  // Respiratoire
  rr: number;
  rr_capno: number;
  vent_rr: number;
  etco2?: number;
  fio2?: number;
  vent_mode?: string;
  vent_peep?: number;
  vent_vt?: number;
  vent_mv?: number;
  vent_pplat?: number;
  // Température
  temp: number;
  temp_core: number;
  temp_skin?: number;
  // Autres paramètres moniteur (optionnels)
  ecg_rhythm?: string;
  ecg_st?: number;
  pi?: number;
  cvp?: number;
  co?: number;
  ci?: number;
  icp?: number;
  cpp?: number;
  cpp_val?: number;
  bis?: number;
  gcs?: number;
  uo_hour?: number;
  lab_k?: number;
  lab_cr?: number;
  lab_hb?: number;
  lab_wbc?: number;
  abg_ph?: number;
  abg_pao2?: number;
  abg_paco2?: number;
  coag_inr?: number;
  scenario?: string;
  // ECG waveform
  ecg_samples?: number[];
  ecg_anomaly_flags?: boolean[];
  ecg_anomaly_type?: string | null;
}

export interface EcgChunk {
  samples: number[];
  anomaly: boolean[];
  anomaly_type: string | null;
}

export interface AgentResult {
  agent_name: string;
  signal: string;
  value: string;
  detected_event: string;
  confidence: number;
  severity: Severity;
  explanation: string;
  recommendation: string;
  trend: Trend;
}

export interface Decision {
  overall_severity: Severity;
  diagnosis: string;
  recommended_action: string;
  top_signal: string;
  contributing: string[];
}

export interface Prediction {
  cardiac_arrest_risk: number;
  respiratory_failure_risk: number;
  shock_risk: number;
  deterioration_risk: number;
  horizons: Record<string, number>; // "5" | "15" | "30" | "60" -> risk
}

export interface Agents {
  ecg: AgentResult;
  heart_rate: AgentResult;
  spo2: AgentResult;
  temperature: AgentResult;
  blood_pressure: AgentResult;
  respiratory: AgentResult;
}

export interface Tick {
  type: "tick";
  patient_id: string;
  ts: number;
  vitals: Vitals;
  ecg: EcgChunk;
  agents: Agents;
  decision: Decision;
  prediction: Prediction;
}

export interface Alert {
  id: string;
  patient_id: string;
  signal: string;
  event: string;
  severity: Severity;
  confidence: number;
  message: string;
  status: "active" | "acknowledged" | "resolved";
  created_at: number;
  resolved_at: number | null;
}

export type ServerMessage =
  | Tick
  | { type: "alert"; alert: Alert }
  | { type: "alert_resolved"; alert: Alert }
  | { type: "clinical_summary"; text: string; source: string };

export interface Report {
  report_type: string;
  patient_id: string;
  ts: number;
  content_md: string;
  summary: string;
  critical_flags: string[];
}

export const SCENARIOS = [
  "normal",
  "tachy",
  "brady",
  "afib",
  "pvc",
  "st_elevation",
  "st_depression",
  "vtach",
] as const;
