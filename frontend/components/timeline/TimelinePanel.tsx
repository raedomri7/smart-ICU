"use client";

/**
 * components/timeline/TimelinePanel.tsx
 * =====================================
 * Timeline chronologique des événements cliniques significatifs (dérivée des
 * changements de diagnostic / gravité élevée reçus en temps réel).
 */

import { motion } from "framer-motion";
import { severityColor } from "@/lib/format";
import type { Severity } from "@/lib/types";
import { Card } from "@/components/ui/Card";

export interface TimelineEvent {
  time: string;
  label: string;
  severity: Severity;
}

export function TimelinePanel({ events }: { events: TimelineEvent[] }) {
  return (
    <Card title="Timeline Clinique">
      <div className="flex max-h-72 flex-col gap-0 overflow-y-auto pr-1">
        {events.length === 0 && (
          <div className="py-8 text-center text-xs text-txt-faint">
            Aucun événement enregistré.
          </div>
        )}
        {events.map((e, i) => {
          const color = severityColor(e.severity);
          return (
            <motion.div
              key={`${e.time}-${i}`}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className="relative flex gap-3 pb-3 pl-1"
            >
              <div className="flex flex-col items-center">
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: color }} />
                {i < events.length - 1 && <span className="w-px flex-1 bg-border" />}
              </div>
              <div className="pb-1">
                <div className="text-[10px] tabular-nums text-txt-faint">{e.time}</div>
                <div className="text-[12px] leading-snug text-txt">{e.label}</div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </Card>
  );
}
