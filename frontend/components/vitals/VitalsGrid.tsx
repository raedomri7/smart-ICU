"use client";

import { motion } from "framer-motion";
import type { Agents, Vitals } from "@/lib/types";
import { VitalCard } from "./VitalCard";

/**
 * components/vitals/VitalsGrid.tsx
 * ================================
 * Grille des 5 cartes vitales (hors ECG) : FC, SpO2, PA, FR, Température.
 * Chaque carte reflète le résultat de son agent IA (couleur, tendance, texte).
 */

/** Couleur température : bleu (froid) / vert (normal) / orange (fièvre) / rouge (forte). */
function tempColor(temp: number): string {
  if (temp < 36.0) return "#0096ff";
  if (temp >= 39.0) return "#ff2244";
  if (temp >= 38.0) return "#ff6600";
  return "#00ff88";
}

export function VitalsGrid({
  agents,
  vitals,
}: {
  agents: Agents;
  vitals: Vitals;
}) {
  const sbp = vitals.nibp_sys ?? vitals.sbp;
  const dbp = vitals.nibp_dia ?? vitals.dbp;
  const mapValue = vitals.nibp_map ?? vitals.map;
  const rr = vitals.rr_capno ?? vitals.vent_rr ?? vitals.rr;
  const temp = vitals.temp_core ?? vitals.temp ?? 0;

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
      <VitalCard
        title="Fréquence Cardiaque"
        value={vitals.ecg_hr || vitals.hr}
        unit="bpm"
        agent={agents.heart_rate}
        pulse
        icon={
          <motion.span
            animate={{ scale: [1, 1.25, 1] }}
            transition={{ duration: Math.max(0.35, 60 / Math.max(vitals.ecg_hr || vitals.hr, 30)), repeat: Infinity }}
          >
            ♥
          </motion.span>
        }
      />
      <VitalCard title="SpO₂" value={vitals.spo2} unit="%" agent={agents.spo2} />
      <VitalCard
        title="Pression Artérielle"
        value={`${sbp}/${dbp}`}
        unit={`PAM ${mapValue}`}
        agent={agents.blood_pressure}
      />
      <VitalCard title="Fréq. Respiratoire" value={rr} unit="/min" agent={agents.respiratory} />
      <VitalCard
        title="Température"
        value={temp.toFixed(1)}
        unit="°C"
        agent={agents.temperature}
        accentColor={tempColor(temp)}
      />
    </div>
  );
}
