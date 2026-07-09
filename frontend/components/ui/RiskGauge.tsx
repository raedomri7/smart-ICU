"use client";

import { motion } from "framer-motion";

/** Jauge circulaire de risque (0-100) avec couleur dynamique. */
export function RiskGauge({
  value,
  label,
  size = 120,
}: {
  value: number;
  label: string;
  size?: number;
}) {
  const r = size / 2 - 10;
  const circ = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, value));
  const color =
    pct >= 75 ? "#ff2244" : pct >= 50 ? "#ff6600" : pct >= 25 ? "#ffcc00" : "#00ff88";

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#0d2a3e" strokeWidth={8} />
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={color}
            strokeWidth={8}
            strokeLinecap="round"
            strokeDasharray={circ}
            initial={false}
            animate={{ strokeDashoffset: circ * (1 - pct / 100) }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            style={{ filter: `drop-shadow(0 0 6px ${color}88)` }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span
            className="font-bold tabular-nums"
            style={{ color, fontSize: size * 0.22 }}
          >
            {Math.round(pct)}%
          </span>
        </div>
      </div>
      {label && (
        <span className="mt-1 text-center text-[10px] uppercase tracking-widest text-txt-dim">
          {label}
        </span>
      )}
    </div>
  );
}
