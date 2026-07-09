"""
app/ai/agents/base.py
======================
Contrat commun étendu des agents IA pour moniteur ICU complet.

Chaque agent analyse un sous-ensemble des paramètres, retourne AgentResult
avec confiance, gravité, explication, recommandation, tendance et détails.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from app.ai.schemas import VitalsSample, AgentResult


@dataclass
class AgentContext:
    prev: dict = field(default_factory=dict)
    thresholds: dict = field(default_factory=dict)

    def previous(self, key: str):
        return self.prev.get(key)

    def threshold(self, key: str, default: float) -> float:
        return self.thresholds.get(key, default)


class Agent(Protocol):
    name: str

    def analyze(self, sample: VitalsSample, ctx: AgentContext) -> AgentResult:
        ...


def trend_from(current: float, previous: float | None, threshold: float = 0.0) -> str:
    if previous is None or threshold == 0:
        return "stable"
    if threshold > 0:
        if current > previous + threshold:
            return "rising"
        if current < previous - threshold:
            return "falling"
    return "stable"
