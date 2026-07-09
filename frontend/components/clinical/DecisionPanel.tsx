"use client";

/**
 * components/clinical/DecisionPanel.tsx
 * =====================================
 * Aide à la décision clinique : diagnostic inféré, niveau de risque global,
 * action recommandée prioritaire, signaux contributifs. Optionnellement,
 * résumé clinique textuel (Gemini ou repli local) sur demande.
 */

import { useState } from "react";
import { motion } from "framer-motion";
import type { Decision } from "@/lib/types";
import { severityColor, severityLabel } from "@/lib/format";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { SeverityBadge } from "@/components/ui/SeverityBadge";

export function DecisionPanel({
  decision,
  patientId,
}: {
  decision: Decision;
  patientId: string;
}) {
  const color = severityColor(decision.overall_severity);
  const [summary, setSummary] = useState<{ source: string; text: string } | null>(null);
  const [loading, setLoading] = useState(false);

  async function loadSummary() {
    setLoading(true);
    try {
      setSummary(await api.clinicalSummary(patientId));
    } catch {
      setSummary({ source: "error", text: "Résumé indisponible." });
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card
      title="Aide à la Décision Clinique"
      right={<SeverityBadge severity={decision.overall_severity} />}
    >
      <div
        className="rounded-lg border p-3"
        style={{ borderColor: `${color}55`, background: `${color}0d` }}
      >
        <div className="text-[10px] uppercase tracking-widest text-txt-dim">Diagnostic possible</div>
        <motion.p
          key={decision.diagnosis}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-1 text-sm font-semibold"
          style={{ color }}
        >
          {decision.diagnosis}
        </motion.p>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-3">
        <div className="rounded-lg border border-border bg-bg-card2 p-3">
          <div className="text-[10px] uppercase tracking-widest text-txt-dim">Niveau de risque</div>
          <div className="mt-1 text-lg font-bold" style={{ color }}>
            {severityLabel(decision.overall_severity)}
          </div>
        </div>
        <div className="rounded-lg border border-border bg-bg-card2 p-3">
          <div className="text-[10px] uppercase tracking-widest text-txt-dim">Signal prioritaire</div>
          <div className="mt-1 text-lg font-bold text-txt">{decision.top_signal}</div>
        </div>
      </div>

      <div className="mt-3 rounded-lg border border-border bg-bg-card2 p-3">
        <div className="text-[10px] uppercase tracking-widest text-txt-dim">Action recommandée</div>
        <p className="mt-1 text-sm text-txt">{decision.recommended_action}</p>
      </div>

      {decision.contributing.length > 0 && (
        <div className="mt-3">
          <div className="mb-1 text-[10px] uppercase tracking-widest text-txt-dim">
            Signaux contributifs
          </div>
          <div className="flex flex-wrap gap-1.5">
            {decision.contributing.map((c) => (
              <span
                key={c}
                className="rounded border border-border-bright bg-bg-card2 px-2 py-0.5 text-[10px] text-txt-dim"
              >
                {c}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="mt-3">
        <button
          onClick={loadSummary}
          disabled={loading}
          className="rounded-md border border-border-bright bg-icu-cyan/5 px-3 py-1.5 text-[11px] text-icu-cyan transition hover:bg-icu-cyan/15 disabled:opacity-50"
        >
          {loading ? "Génération…" : "Générer un résumé clinique"}
        </button>
        {summary && (
          <p className="mt-2 rounded-lg border border-border bg-bg-card2 p-3 text-[12px] leading-snug text-txt-dim">
            {summary.text}
            <span className="ml-1 text-[9px] uppercase text-txt-faint">
              · source : {summary.source}
            </span>
          </p>
        )}
      </div>
    </Card>
  );
}
