"""
PRAVA — Gemini API client.
Generates exam questions from article content.

Model: gemini-2.5-flash-lite (free tier: separate quota from 2.0-flash)
Requires:
    pip install google-genai
    GEMINI_API_KEY in .env
"""
import json
import logging
import os
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Gemini Free tier limits — gemini-2.5-flash-lite: ~30 RPM free tier
# Use 10 RPM (6s delay) to stay safely under the burst limit
RATE_LIMIT_RPM = 10
RATE_LIMIT_DELAY = 60 / RATE_LIMIT_RPM   # 6s between requests

MAX_RETRIES = 4          # retry on 429
RETRY_BASE_DELAY = 35    # seconds flat wait on 429 (API resets each minute)

MODEL_NAME = "gemini-2.5-flash-lite"

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
    Wrapper around the Gemini 2.0 Flash API for question generation.
    Uses the new google.genai SDK (google-genai package).
    Respects the free tier rate limit of 15 requests/minute.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the client.

        Args:
            api_key: Gemini API key. Defaults to GEMINI_API_KEY env variable.

        Raises:
            ValueError: If no API key is found.
            ImportError: If 'google-genai' package is not installed.
        """
        try:
            from google import genai
            from google.genai import types as genai_types
            self._genai = genai
            self._types = genai_types
        except ImportError:
            raise ImportError(
                "Install the Gemini package: pip install google-genai"
            )

        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set. Add it to your .env file.")

        self._client = self._genai.Client(api_key=self.api_key)
        self._last_request_time: float = 0

    def _rate_limit(self) -> None:
        """Pause to respect the 15 req/min rate limit."""
        elapsed = time.time() - self._last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            wait = RATE_LIMIT_DELAY - elapsed
            logger.debug(f"Rate limit: waiting {wait:.1f}s")
            time.sleep(wait)

    def generate_questions(
        self,
        article: dict,
        prompt_override: Optional[str] = None,
    ) -> list[dict]:
        """
        Generate 5 exam questions for a given article.

        Args:
            article: Processed article dict (output of 03_process.py).
                     Expected fields: article_number, title_fr,
                     full_text_fr, full_text_nl, full_text_ru,
                     content_md_fr, sign_codes.
            prompt_override: If given, use this string as the full prompt
                             instead of building one from the article fields.
                             (Used by 04_questions.py for richer context.)

        Returns:
            List of question dicts (see TECHNICAL_ARCHITECTURE.md §questions),
            or [] on failure.
        """
        self._rate_limit()

        if prompt_override:
            prompt = prompt_override
        else:
            # Fallback: build a simple prompt from available fields
            content_fr = (
                article.get("content_md_fr")
                or article.get("full_text_fr")
                or article.get("content_text_fr", "")
            )
            context_parts = [
                f"Article: {article.get('article_number', '')} — {article.get('title_fr', '')}",
                f"\n[FR]\n{content_fr[:3000]}",
            ]
            content_nl = article.get("full_text_nl") or article.get("content_text_nl", "")
            if content_nl:
                context_parts.append(f"\n[NL]\n{content_nl[:1500]}")
            prompt = "\n".join(context_parts)

        logger.debug(
            f"Generating questions for article {article.get('article_number', '?')} "
            f"({len(prompt)} chars)"
        )

        for attempt in range(MAX_RETRIES):
            try:
                response = self._client.models.generate_content(
                    model=MODEL_NAME,
                    contents=prompt,
                    config=self._types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                    ),
                )
                self._last_request_time = time.time()
                break  # success — exit retry loop
            except Exception as exc:
                err_str = str(exc)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    wait = RETRY_BASE_DELAY  # flat wait — API resets every minute
                    logger.warning(
                        f"429 rate limit hit (attempt {attempt + 1}/{MAX_RETRIES}), "
                        f"waiting {wait}s before retry…"
                    )
                    time.sleep(wait)
                    self._last_request_time = time.time()
                    if attempt == MAX_RETRIES - 1:
                        logger.error(f"Gemini API error after {MAX_RETRIES} retries: {exc}")
                        return []
                    continue
                logger.error(f"Gemini API error: {exc}")
                return []
        else:
            return []

        try:
            raw_text = response.text.strip()

            # Strip markdown code fences (```json ... ``` or ``` ... ```)
            if raw_text.startswith("```"):
                lines = raw_text.splitlines()
                # drop first and last fence lines
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                raw_text = "\n".join(lines).strip()

            questions = json.loads(raw_text)

            if not isinstance(questions, list):
                logger.error(f"Gemini returned non-list: {type(questions)}")
                return []

            logger.debug(f"Generated {len(questions)} questions")
            return questions

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return []
