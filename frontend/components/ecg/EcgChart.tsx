"use client";

/**
 * components/ecg/EcgChart.tsx
 * ===========================
 * ECG temps réel sur canvas, avec buffer glissant.
 *
 * Règle clé : la trace reste VERTE en permanence ; SEUL le segment marqué
 * anormal (flags) est redessiné en ROUGE avec un léger glow — jamais toute la
 * courbe. Le type d'anomalie est affiché en surimpression.
 */

import { useCallback, useEffect, useRef } from "react";
import type { EcgChunk } from "@/lib/types";

const BUFFER = 1500; // échantillons visibles

export function EcgChart({ ecg, height = 220 }: { ecg: EcgChunk | null; height?: number }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const bufRef = useRef<number[]>([]);
  const flagRef = useRef<boolean[]>([]);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const w = canvas.clientWidth;
    const h = height;
    if (canvas.width !== w * dpr || canvas.height !== h * dpr) {
      canvas.width = w * dpr;
      canvas.height = h * dpr;
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);

    // Grille médicale
    ctx.strokeStyle = "#0d2a3e";
    ctx.lineWidth = 1;
    for (let x = 0; x < w; x += 25) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }
    for (let y = 0; y < h; y += 25) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    const buf = bufRef.current;
    const flags = flagRef.current;
    if (buf.length < 2) return;

    const midY = h / 2;
    const amp = h * 0.32;
    const step = w / BUFFER;
    const xOf = (i: number) => i * step;
    const yOf = (v: number) => midY - v * amp;

    // 1) trace normale (verte) en continu
    ctx.lineWidth = 1.6;
    ctx.strokeStyle = "#00ff88";
    ctx.shadowBlur = 4;
    ctx.shadowColor = "#00ff8855";
    ctx.beginPath();
    for (let i = 0; i < buf.length; i++) {
      const x = xOf(i);
      const y = yOf(buf[i]);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // 2) redessine UNIQUEMENT les segments anormaux (rouge + glow fort)
    ctx.lineWidth = 2.2;
    ctx.strokeStyle = "#ff2244";
    ctx.shadowBlur = 10;
    ctx.shadowColor = "#ff2244aa";
    let drawing = false;
    for (let i = 0; i < buf.length; i++) {
      if (flags[i]) {
        const x = xOf(i);
        const y = yOf(buf[i]);
        if (!drawing) {
          ctx.beginPath();
          ctx.moveTo(x, y);
          drawing = true;
        } else {
          ctx.lineTo(x, y);
        }
      } else if (drawing) {
        ctx.stroke();
        drawing = false;
      }
    }
    if (drawing) ctx.stroke();
    ctx.shadowBlur = 0;
  }, [height]);

  // Accumule les nouveaux échantillons dans le buffer glissant
  useEffect(() => {
    if (!ecg?.samples?.length) return;
    bufRef.current.push(...ecg.samples);
    flagRef.current.push(...(ecg.anomaly ?? ecg.samples.map(() => false)));
    if (bufRef.current.length > BUFFER) {
      bufRef.current = bufRef.current.slice(-BUFFER);
      flagRef.current = flagRef.current.slice(-BUFFER);
    }
    draw();
  }, [ecg, draw]);

  const hasAnomaly = ecg?.anomaly_type != null;

  return (
    <div className="relative w-full overflow-hidden rounded-lg bg-[#04080c]" style={{ height }}>
      <canvas ref={canvasRef} className="block h-full w-full" />
      {hasAnomaly && (
        <div className="absolute right-3 top-3 rounded-md border border-icu-red bg-icu-red/10 px-2 py-1 text-[11px] font-bold text-icu-red animate-pulse-glow">
          ⚠ {ecg?.anomaly_type}
        </div>
      )}
      <div className="absolute left-3 top-3 text-[10px] uppercase tracking-widest text-txt-faint">
        ECG · Dérivation II
      </div>
    </div>
  );
}
