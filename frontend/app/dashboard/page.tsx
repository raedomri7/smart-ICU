"use client";

/**
 * app/dashboard/page.tsx
 * ======================
 * Dashboard ICU principal — assemble tous les panneaux autour du flux temps
 * réel (WebSocket) : ECG, cartes vitales, décision clinique, prédiction,
 * alertes et timeline. Layout clair, professionnel, non surchargé.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import { useIcuStream } from "@/lib/useIcuStream";
import { ScenarioBar } from "@/components/ScenarioBar";
import { EcgChart } from "@/components/ecg/EcgChart";
import { VitalsGrid } from "@/components/vitals/VitalsGrid";
import { DecisionPanel } from "@/components/clinical/DecisionPanel";
import { PredictionPanel } from "@/components/clinical/PredictionPanel";
import { AlertsPanel } from "@/components/alerts/AlertsPanel";
import { TimelinePanel, type TimelineEvent } from "@/components/timeline/TimelinePanel";
import { ReportViewer } from "@/components/reports/ReportViewer";
import { Card } from "@/components/ui/Card";
import { RiskGauge } from "@/components/ui/RiskGauge";

const PATIENT_ID = "ICU-204";

export default function DashboardPage() {
  const { tick, alerts, state, setScenario, ackAlert } = useIcuStream(PATIENT_ID);
  const [scenario, setScenarioLocal] = useState("normal");
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const lastDiagRef = useRef<string>("");

  // Dérive la timeline des changements de diagnostic à gravité élevée/critique
  useEffect(() => {
    if (!tick) return;
    const d = tick.decision;
    if (
      (d.overall_severity === "high" || d.overall_severity === "critical") &&
      d.diagnosis !== lastDiagRef.current
    ) {
      lastDiagRef.current = d.diagnosis;
      setEvents((prev) =>
        [
          {
            time: new Date(tick.ts * 1000).toLocaleTimeString("fr-FR"),
            label: d.diagnosis,
            severity: d.overall_severity,
          },
          ...prev,
        ].slice(0, 30)
      );
    }
  }, [tick]);

  function handleScenario(s: string) {
    setScenarioLocal(s);
    setScenario(s);
  }

  const header = useMemo(
    () => (
      <header className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-lg font-bold tracking-wide text-txt">
            ICU Smart Monitoring
            <span className="ml-2 text-[11px] font-normal text-txt-faint">
              Surveillance intelligente · Réanimation
            </span>
          </h1>
          <div className="text-[12px] text-txt-dim">
            Patient <span className="font-mono text-icu-cyan">{PATIENT_ID}</span> · Lit 04 ·
            Monitoring continu
          </div>
        </div>
      </header>
    ),
    []
  );

  if (!tick) {
    return (
      <main className="min-h-screen p-5">
        {header}
        <div className="flex h-64 items-center justify-center text-txt-dim">
          <span className="animate-pulse-glow">Connexion au flux temps réel…</span>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen p-5">
      {header}

      <ScenarioBar current={scenario} onChange={handleScenario} state={state} />

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-3">
        {/* Colonne principale : ECG + vitales + prédiction */}
        <div className="flex flex-col gap-4 xl:col-span-2">
          <Card
            title="Électrocardiogramme"
            right={
              <div className="flex items-center gap-3">
                <span className="text-[11px] text-txt-dim">
                  Risque global de dégradation
                </span>
                <RiskGauge
                  value={tick.prediction.deterioration_risk}
                  label=""
                  size={64}
                />
              </div>
            }
          >
            <EcgChart ecg={tick.ecg} />
          </Card>

          <VitalsGrid agents={tick.agents} vitals={tick.vitals} />

          <PredictionPanel prediction={tick.prediction} />
        </div>

        {/* Colonne latérale : décision + alertes + timeline + rapports */}
        <div className="flex flex-col gap-4">
          <DecisionPanel decision={tick.decision} patientId={PATIENT_ID} />
          <ReportViewer patientId={PATIENT_ID} />
          <AlertsPanel alerts={alerts} onAck={ackAlert} />
          <TimelinePanel events={events} />
        </div>
      </div>

      <footer className="mt-6 text-center text-[10px] text-txt-faint">
        Outil d’aide à la décision clinique — ne remplace pas le jugement médical professionnel.
      </footer>
    </main>
  );
}
