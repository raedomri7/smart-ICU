"use client";

/**
 * components/alerts/AlertsPanel.tsx
 * =================================
 * Alertes cliniques temps réel (issues des agents), triées par gravité, avec
 * acquittement. Générées dynamiquement — aucune table statique.
 */

import { AnimatePresence, motion } from "framer-motion";
import type { Alert } from "@/lib/types";
import { severityColor, severityLabel } from "@/lib/format";
import { Card } from "@/components/ui/Card";

export function AlertsPanel({
  alerts,
  onAck,
}: {
  alerts: Alert[];
  onAck: (id: string) => void;
}) {
  const active = alerts.filter((a) => a.status !== "resolved");

  return (
    <Card
      title="Alertes Actives"
      right={
        <span className="rounded-full bg-icu-red/15 px-2 py-0.5 text-[10px] font-bold text-icu-red">
          {active.length}
        </span>
      }
    >
      <div className="flex max-h-72 flex-col gap-2 overflow-y-auto pr-1">
        {active.length === 0 && (
          <div className="py-8 text-center text-xs text-txt-faint">
            Aucune alerte active — patient stable.
          </div>
        )}
        <AnimatePresence initial={false}>
          {active.map((a) => {
            const color = severityColor(a.severity);
            return (
              <motion.div
                key={a.id}
                layout
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="rounded-lg border p-2.5"
                style={{ borderColor: `${color}55`, background: `${color}0d` }}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold" style={{ color }}>
                    {a.signal} · {a.event}
                  </span>
                  <span
                    className="rounded px-1.5 py-0.5 text-[9px] font-bold"
                    style={{ color, borderColor: color, border: "1px solid" }}
                  >
                    {severityLabel(a.severity)}
                  </span>
                </div>
                <p className="mt-1 text-[11px] leading-snug text-txt-dim">{a.message}</p>
                <div className="mt-1.5 flex items-center justify-between">
                  <span className="text-[9px] text-txt-faint">Confiance {a.confidence}%</span>
                  {a.status === "acknowledged" ? (
                    <span className="text-[9px] uppercase tracking-widest text-icu-green">
                      ✓ acquittée
                    </span>
                  ) : (
                    <button
                      onClick={() => onAck(a.id)}
                      className="rounded border border-border-bright px-2 py-0.5 text-[9px] text-txt-dim transition hover:border-icu-cyan hover:text-icu-cyan"
                    >
                      Acquitter
                    </button>
                  )}
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </Card>
  );
}
