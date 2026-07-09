"use client";

/**
 * components/vitals/VitalCard.tsx
 * ===============================
 * Carte vitale générique animée : valeur courante, unité, tendance, badge de
 * gravité, ligne d'interprétation IA, barre d'accent colorée par gravité.
 */

import { motion } from "framer-motion";
import type { AgentResult, Severity } from "@/lib/types";
import { severityColor, trendArrow, trendColor } from "@/lib/format";

export function VitalCard({
  title,
  value,
  unit,
  agent,
  accentColor,
  icon,
  pulse = false,
}: {
  title: string;
  value: string | number;
  unit?: string;
  agent: AgentResult;
  accentColor?: string;
  icon?: React.ReactNode;
  pulse?: boolean;
}) {
  const color = accentColor ?? severityColor(agent.severity as Severity);

  return (
    <div className="relative overflow-hidden rounded-xl border border-border bg-bg-card p-4">
      <div className="absolute left-0 top-0 h-full w-1" style={{ background: color }} />
      <div className="mb-1 flex items-center justify-between">
        <span className="text-[11px] uppercase tracking-widest text-txt-dim">{title}</span>
        <span
          className="rounded border px-1.5 py-0.5 text-[9px] font-bold"
          style={{ color, borderColor: color }}
        >
          {agent.detected_event}
        </span>
      </div>

      <div className="flex items-end gap-2">
        <motion.span
          key={String(value)}
          initial={{ opacity: 0.4, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className={`text-4xl font-bold tabular-nums ${pulse ? "animate-pulse-glow" : ""}`}
          style={{ color }}
        >
          {value}
        </motion.span>
        {unit && <span className="mb-1 text-sm text-txt-dim">{unit}</span>}
        <span className="mb-1 ml-auto text-sm" style={{ color: trendColor(agent.trend) }}>
          {trendArrow(agent.trend)} {icon}
        </span>
      </div>

      <p className="mt-2 line-clamp-2 text-[11px] leading-snug text-txt-dim">
        {agent.explanation}
      </p>
      <div className="mt-1 text-[10px] text-txt-faint">Confiance IA : {agent.confidence}%</div>
    </div>
  );
}
