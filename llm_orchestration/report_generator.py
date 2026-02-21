"""LLM orchestration — Gemini 1.5 Flash report generation and Q&A."""

import logging
from typing import Any
from google import genai
from google.genai import types

from api_services.core.config import settings

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates DD reports and answers questions using Gemini Flash."""

    def __init__(self):
        self._client = None

    def _get_client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    async def generate(
        self, siren: str, sections: list[dict], report_type: str = "standard"
    ) -> dict[str, Any]:
        """Generate a structured DD report from collected sections."""
        sections_text = self._format_sections(sections)

        depth_instruction = {
            "quick": "Rédige un résumé exécutif en 3 paragraphes.",
            "standard": "Rédige un rapport de due diligence structuré (4-6 pages équivalent) avec : Identité, Santé financière, Réputation & Risques, Conclusion.",
            "full": "Rédige un rapport complet et détaillé (8-10 pages équivalent) incluant analyse des dirigeants, concurrence sectorielle, risques ESG.",
        }.get(report_type, "Rédige un rapport de due diligence structuré.")

        prompt = f"""Tu es un expert en due diligence pour des entreprises françaises.
{depth_instruction}
Identifie clairement les ⚠️ Red Flags. Cite tes sources (DINUM, Infogreffe, BODACC, Presse).

=== DONNÉES COLLECTÉES ===
{sections_text}
===========================

FORMAT DE RÉPONSE (JSON strict) :
{{
  "executive_summary": "...",
  "sections": {{
    "identite": "...",
    "finances": "...",
    "reputation": "...",
    "conclusion": "..."
  }},
  "red_flags": ["⚠️ ...", "⚠️ ..."],
  "recommendation": "Favorable | Prudence | Défavorable",
  "confidence_score": 0.0
}}"""

        try:
            client = self._get_client()
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
            import json
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return {
                "executive_summary": f"Erreur de génération: {e}",
                "sections": {},
                "red_flags": [],
                "recommendation": "Indéterminé",
                "confidence_score": 0.0,
            }

    async def answer_question(self, question: str, context_chunks: list[str]) -> str:
        """Answer a question using only the provided context chunks (RAG)."""
        context = "\n\n---\n\n".join(context_chunks)
        prompt = f"""Tu es un assistant expert en due diligence. Réponds à la question UNIQUEMENT à partir du contexte fourni.
Si la réponse n'est pas dans le contexte, dis-le clairement.

CONTEXTE :
{context}

QUESTION : {question}

RÉPONSE :"""

        try:
            client = self._get_client()
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1),
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini Q&A failed: {e}")
            return f"Erreur lors de la génération de la réponse: {e}"

    def _format_sections(self, sections: list[dict]) -> str:
        parts = []
        for s in sections:
            section_type = s.get("type", "unknown").upper()
            data = s.get("data", {})
            parts.append(f"[{section_type}]\n{data}")
        return "\n\n".join(parts)
