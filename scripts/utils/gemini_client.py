"""
PRAVA — Gemini 1.5 Flash API client.
Generates exam questions from article content.

Requires:
    pip install google-generativeai
    GEMINI_API_KEY in .env
"""
import json
import logging
import os
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Gemini Free tier limits
RATE_LIMIT_RPM = 15           # requests per minute
RATE_LIMIT_DELAY = 60 / RATE_LIMIT_RPM   # seconds between requests (~4s)

SYSTEM_PROMPT = """\
Tu es un expert du code de la route belge (AR du 1er décembre 1975).
À partir de l'article fourni, génère exactement 5 questions d'examen :
  - 2 questions THÉORIQUES (définition, signification d'un terme ou d'un signal)
  - 3 questions PRATIQUES (application du règle dans une situation de conduite réelle)

Pour chaque question, fournis STRICTEMENT ce format JSON :
{
  "type": "theoretical" | "practical",
  "difficulty": 1 | 2 | 3,
  "text_fr": "...",
  "text_nl": "...",
  "text_ru": "...",
  "image": {"sign_code": null | "F5", "generation_prompt": "..."},
  "options": [
    {"letter": "A", "text_fr": "...", "text_nl": "...", "text_ru": "...", "is_correct": false},
    {"letter": "B", "text_fr": "...", "text_nl": "...", "text_ru": "...", "is_correct": true},
    {"letter": "C", "text_fr": "...", "text_nl": "...", "text_ru": "...", "is_correct": false}
  ],
  "explanation_fr": "...",
  "explanation_nl": "...",
  "explanation_ru": "..."
}

Retourne UNIQUEMENT un tableau JSON de 5 objets question. Aucun texte avant ou après.
"""


class GeminiClient:
    """
    Wrapper around the Gemini 1.5 Flash API for question generation.
    Respects the free tier rate limit of 15 requests/minute.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the client.

        Args:
            api_key: Gemini API key. Defaults to GEMINI_API_KEY env variable.

        Raises:
            ValueError: If no API key is found.
            ImportError: If 'google-generativeai' package is not installed.
        """
        try:
            import google.generativeai as genai
            self._genai = genai
        except ImportError:
            raise ImportError(
                "Install the Gemini package: pip install google-generativeai"
            )

        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set. Add it to your .env file.")

        self._genai.configure(api_key=self.api_key)
        self.model = self._genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM_PROMPT,
        )
        self._last_request_time: float = 0

    def _rate_limit(self) -> None:
        """Pause to respect the 15 req/min rate limit."""
        elapsed = time.time() - self._last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            wait = RATE_LIMIT_DELAY - elapsed
            logger.debug(f"Rate limit: waiting {wait:.1f}s")
            time.sleep(wait)

    def generate_questions(self, article: dict) -> list[dict]:
        """
        Generate 5 exam questions for a given article.

        Args:
            article: Article dict with at minimum:
                     - article_number, title_fr, content_text_fr,
                       content_text_nl (optional), content_text_ru (optional)

        Returns:
            List of 5 question dicts (see DATA_SCHEMA.md §4), or [] on failure.
        """
        self._rate_limit()

        # Build the prompt context from available article content
        context_parts = [
            f"Article: {article.get('article_number', '')} — {article.get('title_fr', '')}",
            f"\n[FR]\n{article.get('content_text_fr', '')}",
        ]
        if article.get("content_text_nl"):
            context_parts.append(f"\n[NL]\n{article.get('content_text_nl', '')}")
        if article.get("content_text_ru"):
            context_parts.append(f"\n[RU]\n{article.get('content_text_ru', '')}")

        prompt = "\n".join(context_parts)

        logger.info(
            f"Generating questions for article {article.get('article_number', '?')} "
            f"({len(prompt)} chars)"
        )

        try:
            response = self.model.generate_content(prompt)
            self._last_request_time = time.time()

            raw_text = response.text.strip()

            # Strip markdown code fences if present
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]

            questions = json.loads(raw_text)

            if not isinstance(questions, list):
                logger.error(f"Gemini returned non-list: {type(questions)}")
                return []

            logger.info(f"Generated {len(questions)} questions")
            return questions

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return []
