/**
 * lib/format.ts
 * =============
 * Helpers d'affichage : traduction des niveaux de gravité en français et
 * mappage vers les couleurs du thème ICU. Les clés internes restent en anglais.
 */

import type { Severity, Trend } from "./types";

export const SEVERITY_LABEL_FR: Record<Severity, string> = {
  normal: "NORMAL",
  low: "FAIBLE",
  medium: "MOYEN",
  high: "ÉLEVÉ",
  critical: "CRITIQUE",
};

export const SEVERITY_COLOR: Record<Severity, string> = {
  normal: "#00ff88",
  low: "#0096ff",
  medium: "#ffcc00",
  high: "#ff6600",
  critical: "#ff2244",
};

export const SCENARIO_LABEL_FR: Record<string, string> = {
  normal: "Normal",
  tachy: "Tachycardie",
  brady: "Bradycardie",
  afib: "Fibrillation Auriculaire",
  pvc: "ESV",
  st_elevation: "Sus-décalage ST",
  st_depression: "Sous-décalage ST",
  vtach: "Tach. Ventriculaire",
};

export function severityLabel(s: Severity): string {
  return SEVERITY_LABEL_FR[s] ?? s.toUpperCase();
}

export function severityColor(s: Severity): string {
  return SEVERITY_COLOR[s] ?? "#00ff88";
}

export function trendArrow(t: Trend): string {
  return t === "rising" ? "▲" : t === "falling" ? "▼" : "▬";
}

export function trendColor(t: Trend): string {
  return t === "rising" ? "#ff6600" : t === "falling" ? "#00e5ff" : "#6a9bbf";
}
