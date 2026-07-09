"""
app/llm/gemini.py
=================
Intégration OPTIONNELLE de Gemini — UNIQUEMENT pour enrichir des explications
médicales, résumés cliniques et recommandations TEXTUELLES.

RÈGLES STRICTES :
  - JAMAIS appelé dans la boucle temps réel.
  - JAMAIS utilisé pour la détection d'anomalies ou les calculs de gravité.
  - Entièrement désactivable (GEMINI_ENABLED=false) : le système fonctionne à 100 %
    sans lui. En cas d'erreur/quota, on renvoie None silencieusement.

Appelé à la demande (REST) ou en tâche de fond découplée du flux WS.
"""

from __future__ import annotations

import logging

from app.config import settings

logger = logging.getLogger("icu.gemini")


class GeminiClient:
    def __init__(self) -> None:
        self.enabled = settings.gemini_enabled and bool(settings.gemini_api_key)
        self._model = None
        if self.enabled:
            try:
                import google.generativeai as genai  # import paresseux
                genai.configure(api_key=settings.gemini_api_key)
                self._model = genai.GenerativeModel(settings.gemini_model)
            except Exception as exc:  # dépendance absente ou clé invalide
                logger.warning("Gemini désactivé (init échouée) : %s", exc)
                self.enabled = False

    def clinical_summary(self, context: dict) -> str | None:
        """
        Produit un court résumé clinique en français à partir de l'état IA courant.
        `context` : { diagnosis, overall_severity, contributing, prediction }.
        Retourne None si Gemini est désactivé ou en erreur.
        """
        if not self.enabled or self._model is None:
            return None

        prompt = self._build_prompt(context)
        try:
            resp = self._model.generate_content(prompt)
            return (resp.text or "").strip() or None
        except Exception as exc:
            logger.warning("Appel Gemini échoué : %s", exc)
            return None

    @staticmethod
    def _build_prompt(context: dict) -> str:
        contributing = ", ".join(context.get("contributing", [])) or "aucun signal anormal"
        return (
            "Tu es un assistant clinique. Rédige en français un résumé concis "
            "(3 phrases max) de la situation d'un patient en réanimation, à "
            "destination d'un soignant. Reste factuel, prudent, et rappelle que "
            "c'est une aide à la décision.\n\n"
            f"Diagnostic possible : {context.get('diagnosis')}\n"
            f"Gravité globale : {context.get('overall_severity')}\n"
            f"Signaux contributifs : {contributing}\n"
            f"Risque de dégradation : {context.get('deterioration_risk')}%\n"
        )


# Singleton léger
gemini_client = GeminiClient()
