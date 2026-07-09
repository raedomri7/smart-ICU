"use client";

/**
 * components/clinical/PredictionPanel.tsx
 * =======================================
 * Prédiction multi-horizon : risque de dégradation à 5/15/30/60 min (Recharts)
 * + jauges des risques spécifiques (arrêt cardiaque, détresse resp., choc).
 */

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip,
  CartesianGrid,
} from "recharts";
import type { Prediction } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { RiskGauge } from "@/components/ui/RiskGauge";

export function PredictionPanel({ prediction }: { prediction: Prediction }) {
  const data = ["5", "15", "30", "60"].map((h) => ({
    horizon: `${h} min`,
    risk: prediction.horizons[h] ?? 0,
  }));

  return (
    <Card title="Prédiction de Dégradation">
      <div className="h-40 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#ff6600" stopOpacity={0.5} />
                <stop offset="100%" stopColor="#ff6600" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#0d2a3e" vertical={false} />
            <XAxis dataKey="horizon" stroke="#3a5a7a" fontSize={11} />
            <YAxis domain={[0, 100]} stroke="#3a5a7a" fontSize={11} />
            <Tooltip
              contentStyle={{
                background: "#0c1a28",
                border: "1px solid #1a4060",
                borderRadius: 6,
                fontSize: 12,
              }}
              labelStyle={{ color: "#00e5ff" }}
              formatter={(v: number) => [`${v}%`, "Risque"]}
            />
            <Area
              type="monotone"
              dataKey="risk"
              stroke="#ff6600"
              strokeWidth={2}
              fill="url(#riskGrad)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-2">
        <RiskGauge value={prediction.cardiac_arrest_risk} label="Arrêt cardiaque" size={96} />
        <RiskGauge value={prediction.respiratory_failure_risk} label="Détresse resp." size={96} />
        <RiskGauge value={prediction.shock_risk} label="Choc" size={96} />
      </div>
    </Card>
  );
}
