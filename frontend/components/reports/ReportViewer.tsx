"use client";

/**
 * components/reports/ReportViewer.tsx
 * ====================================
 * Visionneuse de rapports médicaux générés automatiquement par le backend.
 * Permet de consulter les notes de progrès, résumés transfert, notes nursing,
 * résumés famille, documents code status et comptes-rendus de laboratoire.
 */

import { useState } from "react";
import { motion } from "framer-motion";
import type { Report } from "@/lib/types";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/Card";

const REPORT_LABELS: Record<string, string> = {
  progress: "Note de progrès",
  transfer: "Résumé de transfert",
  nursing: "Note infirmière",
  family: "Résumé famille",
  code_status: "Code status",
  lab: "Compte rendu laboratoire",
};

const REPORT_COLORS: Record<string, string> = {
  progress: "#00ff88",
  transfer: "#ffcc00",
  nursing: "#00e5ff",
  family: "#aa66ff",
  code_status: "#ff6600",
  lab: "#ff2244",
};

function MarkdownLikeRenderer({ text, flags }: { text: string; flags?: string[] }) {
  return (
    <div className="space-y-3">
      {flags && flags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {flags.map((f) => (
            <span key={f} className="rounded border border-icu-red bg-icu-red/10 px-2 py-1 text-[10px] font-bold text-icu-red">
              ⚠ {f}
            </span>
          ))}
        </div>
      )}
      {text.split("\n").map((line, i) => {
        if (line.startsWith("# ")) {
          return <h1 key={i} className="text-lg font-bold text-txt">{line.slice(2)}</h1>;
        }
        if (line.startsWith("## ")) {
          return <h2 key={i} className="text-base font-semibold text-txt">{line.slice(3)}</h2>;
        }
        if (line.startsWith("### ")) {
          return <h3 key={i} className="text-sm font-semibold text-txt mt-2">{line.slice(4)}</h3>;
        }
        if (line.startsWith("- ")) {
          return <li key={i} className="ml-4 text-xs text-txt-dim">{line.slice(2)}</li>;
        }
        if (line.startsWith("| ")) {
          return <pre key={i} className="text-[10px] text-txt-dim font-mono overflow-x-auto">{line}</pre>;
        }
        if (line.startsWith("> ")) {
          return <blockquote key={i} className="border-l-2 border-icu-cyan pl-2 text-xs text-txt-dim italic">{line.slice(2)}</blockquote>;
        }
        if (line.startsWith("---")) {
          return <hr key={i} className="border-border my-2" />;
        }
        if (line.trim() === "") return <br key={i} />;
        return <p key={i} className="text-xs text-txt">{line}</p>;
      })}
    </div>
  );
}

export function ReportViewer({ patientId }: { patientId: string }) {
  const [reports, setReports] = useState<Report[]>([]);
  const [selected, setSelected] = useState<Report | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadReports(force = false) {
    if (!force && reports.length > 0) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.reportsLatest(patientId);
      setReports(data);
      if (!selected && data.length > 0) setSelected(data[0]);
    } catch {
      setError("Impossible de charger les rapports.");
    } finally {
      setLoading(false);
    }
  }

  function handleSelect(type: string) {
    const found = reports.find((r) => r.report_type === type) || null;
    setSelected(found);
  }

  return (
    <Card
      title="Rapports Médicaux"
      right={
        <button
          onClick={() => loadReports(true)}
          disabled={loading}
          className="rounded border border-border-bright bg-icu-cyan/5 px-3 py-1.5 text-[11px] text-icu-cyan transition hover:bg-icu-cyan/15 disabled:opacity-50"
        >
          {loading ? "Génération…" : "Actualiser rapports"}
        </button>
      }
    >
      <div className="flex gap-2 overflow-x-auto pb-1">
        {Object.entries(REPORT_LABELS).map(([key, label]) => {
          const color = REPORT_COLORS[key] || "#00ff88";
          const active = selected?.report_type === key;
          return (
            <button
              key={key}
              onClick={() => handleSelect(key)}
              className={`whitespace-nowrap rounded border px-3 py-1.5 text-[11px] transition ${
                active ? "border-current bg-current/5" : "border-border text-txt-dim hover:border-icu-cyan hover:text-icu-cyan"
              }`}
              style={active ? { color, borderColor: color } : {}}
            >
              {label}
            </button>
          );
        })}
      </div>

      {error && <p className="mt-3 text-xs text-icu-red">{error}</p>}

      {!error && !selected && !loading && (
        <div className="mt-6 py-8 text-center text-xs text-txt-faint">
          Cliquez sur “Actualiser rapports” pour générer les notes médicales.
        </div>
      )}

      {selected && (
        <motion.div
          key={selected.report_type}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-3 rounded-lg border border-border bg-bg-card2 p-4"
        >
          <div className="mb-2 flex items-center justify-between">
            <span
              className="rounded px-2 py-0.5 text-[10px] font-bold"
              style={{ color: REPORT_COLORS[selected.report_type] || "#fff", border: "1px solid" }}
            >
              {REPORT_LABELS[selected.report_type] || selected.report_type}
            </span>
            <span className="text-[10px] text-txt-faint">
              {new Date(selected.ts * 1000).toLocaleString("fr-FR")}
            </span>
          </div>
          <MarkdownLikeRenderer text={selected.content_md} flags={selected.critical_flags} />
        </motion.div>
      )}
    </Card>
  );
}
