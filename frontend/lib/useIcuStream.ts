/**
 * lib/useIcuStream.ts
 * ===================
 * Hook WebSocket temps réel : abonnement à un patient, réception des ticks IA
 * et des alertes, reconnexion automatique. Expose aussi `setScenario` (envoi
 * d'un message de contrôle) sur le même canal.
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Tick, Alert, ServerMessage } from "./types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000/ws";

export type ConnState = "connecting" | "open" | "closed";

export function useIcuStream(patientId: string) {
  const [tick, setTick] = useState<Tick | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [state, setState] = useState<ConnState>("connecting");
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    setState("connecting");
    const ws = new WebSocket(`${WS_URL}?patient_id=${encodeURIComponent(patientId)}`);
    wsRef.current = ws;

    ws.onopen = () => setState("open");

    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data) as ServerMessage;
      if (msg.type === "tick") {
        setTick(msg);
      } else if (msg.type === "alert") {
        setAlerts((prev) => [msg.alert, ...prev.filter((a) => a.id !== msg.alert.id)].slice(0, 30));
      } else if (msg.type === "alert_resolved") {
        setAlerts((prev) => prev.filter((a) => a.id !== msg.alert.id));
      }
    };

    ws.onclose = () => {
      setState("closed");
      // reconnexion automatique après 1.5s
      retryRef.current = setTimeout(connect, 1500);
    };

    ws.onerror = () => ws.close();
  }, [patientId]);

  useEffect(() => {
    connect();
    return () => {
      if (retryRef.current) clearTimeout(retryRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const setScenario = useCallback((scenario: string) => {
    wsRef.current?.send(JSON.stringify({ type: "set_scenario", scenario }));
  }, []);

  const ackAlert = useCallback((alertId: string) => {
    wsRef.current?.send(JSON.stringify({ type: "ack_alert", alert_id: alertId }));
    setAlerts((prev) =>
      prev.map((a) => (a.id === alertId ? { ...a, status: "acknowledged" } : a))
    );
  }, []);

  return { tick, alerts, state, setScenario, ackAlert };
}
