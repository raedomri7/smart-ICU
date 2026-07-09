/**
 * lib/api.ts
 * ==========
 * Client REST minimal (canal froid) : login, scénarios, changement de scénario,
 * alertes, résumé clinique. Le flux temps réel passe par le WebSocket.
 */

import type { Report } from "./types";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) =>
    req<{ access_token: string; role: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  scenarios: () => req<string[]>("/ai/scenarios"),

  setScenario: (patient_id: string, scenario: string) =>
    req<{ ok: boolean }>("/ai/scenario", {
      method: "POST",
      body: JSON.stringify({ patient_id, scenario }),
    }),

  clinicalSummary: (patient_id: string) =>
    req<{ source: string; text: string }>(`/ai/summary/${patient_id}`, {
      method: "POST",
    }),

  reportsLatest: (patient_id: string) =>
    req<Report[]>(`/reports/${patient_id}/latest`),
};
