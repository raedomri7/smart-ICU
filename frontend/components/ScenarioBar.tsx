"use client";

/**
 * components/ScenarioBar.tsx
 * ==========================
 * Barre de contrôle du scénario clinique (simulateur) + statut de connexion WS.
 * En production, cette barre serait remplacée par la sélection de la source
 * réelle (moniteur patient / dataset).
 */

import { SCENARIOS } from "@/lib/types";
import { SCENARIO_LABEL_FR } from "@/lib/format";
import type { ConnState } from "@/lib/useIcuStream";

export function ScenarioBar({
  current,
  onChange,
  state,
}: {
  current: string;
  onChange: (s: string) => void;
  state: ConnState;
}) {
  const dot =
    state === "open" ? "#00ff88" : state === "connecting" ? "#ffcc00" : "#ff2244";
  const label =
    state === "open" ? "Temps réel actif" : state === "connecting" ? "Connexion…" : "Déconnecté";

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-xl border border-border bg-bg-card px-3 py-2">
      <span className="mr-1 text-[10px] uppercase tracking-widest text-txt-dim">Scénario</span>
      {SCENARIOS.map((s) => (
        <button
          key={s}
          onClick={() => onChange(s)}
          className={`rounded-md border px-2.5 py-1 text-[11px] transition ${
            current === s
              ? "border-icu-cyan bg-icu-cyan/15 text-icu-cyan"
              : "border-border-bright text-txt-dim hover:border-icu-cyan hover:text-icu-cyan"
          }`}
        >
          {SCENARIO_LABEL_FR[s] ?? s}
        </button>
      ))}
      <div className="ml-auto flex items-center gap-2">
        <span
          className="h-2 w-2 rounded-full"
          style={{ background: dot, boxShadow: `0 0 6px ${dot}` }}
        />
        <span className="text-[11px] text-txt-dim">{label}</span>
      </div>
    </div>
  );
}
