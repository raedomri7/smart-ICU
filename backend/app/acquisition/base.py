"""
app/acquisition/base.py
=======================
Interface abstraite d'une source de données patient.

Toute source (simulateur, CSV, moniteur réel, API médicale, WebSocket entrant)
implémente `DataSource` et produit des `VitalsSample` unifiés. Le reste du
système ne connaît QUE cette interface → intégration future de vrais capteurs
sans modifier l'IA, le transport ni l'affichage (adapter pattern).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.ai.schemas import VitalsSample


class DataSource(ABC):
    """Contrat commun de toutes les sources d'acquisition."""

    mode: str = "base"

    @abstractmethod
    def read(self) -> VitalsSample:
        """Retourne le prochain échantillon vital (bloquant/synchrone léger)."""
        raise NotImplementedError

    def configure(self, **kwargs) -> None:
        """Reconfiguration à chaud optionnelle (ex: changer de scénario)."""
        return None

    def close(self) -> None:
        """Libère les ressources éventuelles (fichiers, sockets)."""
        return None
