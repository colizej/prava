"""
PRAVA — Groq API client (fallback for when Gemini quota is exhausted).
Generates exam questions from article content using Llama-3.3-70B via Groq.

Free tier limits (groq.com):
  - llama-3.3-70b-versatile: 14,400 RPD, 30 RPM, 6,000 TPM
  → Far more generous than Gemini's 20 RPD

Requires:
    pip install groq
    GROQ_API_KEY in .env (get free key at console.groq.com)
"""
import json
import logging
import os
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Groq free tier: 30 RPM for llama-3.3-70b — use 20 RPM to be safe
RATE_LIMIT_RPM = 20
RATE_LIMIT_DELAY = 60 / RATE_LIMIT_RPM   # 3s between requests

MAX_RETRIES = 3
RETRY_BASE_DELAY = 65  # seconds on 429

MODEL_NAME = "llama-3.3-70b-versatile"

# Same system prompt as GeminiClient for consistent output format
SYSTEM_PROMPT = """\
Tu es un expert du code de la route belge.
À partir de l'article fourni, génère des questions d'examen :
  - 3 questions THÉORIQUES centrées sur les définitions, les noms officiels et la signification des concepts
  - 5 questions PRATIQUES basées sur des situations de conduite réelles

RÈGLES ABSOLUES :
- NE JAMAIS mentionner de numéro d'article, de titre de loi ou de référence juridique dans le texte
  des questions ou des réponses
- Chaque question doit tester la COMPRÉHENSION du concept, pas la mémorisation d'un numéro
- Si l'article contient plusieurs sous-points, répartis les questions pour couvrir des SOUS-POINTS DIFFÉRENTS
- Si l'article est trop court pour générer 8 questions vraiment distinctes, génère-en moins
  (minimum 3) plutôt que de répéter le même sens sous une forme différente
- Toutes les questions et réponses doivent être en 3 langues : FR, NL, RU

Pour chaque question, fournis STRICTEMENT ce format JSON :
{
  "type": "theoretical" | "practical",
  "difficulty": 1 | 2 | 3,
  "text_fr": "...",
  "text_nl": "...",
  "text_ru": "...",
  "image": {"sign_code": null, "generation_prompt": ""},
  "options": [
    {"letter": "A", "text_fr": "...", "text_nl": "...", "text_ru": "...", "is_correct": false},
    {"letter": "B", "text_fr": "...", "text_nl": "...", "text_ru": "...", "is_correct": true},
    {"letter": "C", "text_fr": "...", "text_nl": "...", "text_ru": "...", "is_correct": false}
  ],
  "explanation_fr": "...",
  "explanation_nl": "...",
  "explanation_ru": "..."
}

Retourne UNIQUEMENT un tableau JSON d'objets question. Aucun texte avant ou après.
"""


class DailyQuotaExhausted(Exception):
    """Raised when Groq daily quota is exhausted."""


class GroqClient:
    """
    Wrapper around Groq API (Llama-3.3-70B) for question generation.
    Drop-in replacement for GeminiClient — same generate_questions() interface.
    """

    def __init__(self, api_key: Optional[str] = None):
        try:
            from groq import Groq
            self._Groq = Groq
        except ImportError:
            raise ImportError("Install the Groq package: pip install groq")

        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not set. Add it to your .env file.")

        self._client = self._Groq(api_key=self.api_key)
        self._last_request_time: float = 0
        self._model_name = MODEL_NAME

    def _rate_limit(self) -> None:
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
        Generate exam questions for a given article.
        Same interface as GeminiClient.generate_questions().
        """
        self._rate_limit()

        if prompt_override:
            prompt = prompt_override
        else:
            content_fr = (
                article.get("content_md_fr")
                or article.get("full_text_fr", "")
            )
            prompt = (
                f"Article: {article.get('article_number', '')} — {article.get('title_fr', '')}"
                f"\n\n[FR]\n{content_fr[:3000]}"
            )

        for attempt in range(MAX_RETRIES):
            try:
                response = self._client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=4096,
                )
                self._last_request_time = time.time()

                raw_text = response.choices[0].message.content.strip()

                # Strip markdown fences if present
                if raw_text.startswith("```"):
                    lines = raw_text.splitlines()
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].strip() == "```":
                        lines = lines[:-1]
                    raw_text = "\n".join(lines).strip()

                questions = json.loads(raw_text)
                if not isinstance(questions, list):
                    logger.error(f"Groq returned non-list: {type(questions)}")
                    return []

                logger.debug(f"Groq generated {len(questions)} questions")
                return questions

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Groq response as JSON: {e}")
                return []

            except Exception as exc:
                err_str = str(exc)
                if "429" in err_str or "rate_limit" in err_str.lower():
                    if "day" in err_str.lower() or "daily" in err_str.lower():
                        logger.error("Groq daily quota exhausted.")
                        raise DailyQuotaExhausted("Groq daily quota exhausted.")
                    logger.warning(
                        f"Groq 429 rate limit (attempt {attempt + 1}/{MAX_RETRIES}), "
                        f"waiting {RETRY_BASE_DELAY}s…"
                    )
                    time.sleep(RETRY_BASE_DELAY)
                    self._last_request_time = time.time()
                    if attempt == MAX_RETRIES - 1:
                        logger.error(f"Groq API error after {MAX_RETRIES} retries: {exc}")
                        return []
                    continue
                logger.error(f"Groq API error: {exc}")
                return []

        return []
