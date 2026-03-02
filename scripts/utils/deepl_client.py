"""
PRAVA — DeepL Free API client.
Translates text from French to Russian with quota management.

Requires:
    pip install deepl
    DEEPL_API_KEY in .env
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Warn when remaining quota drops below this percentage
QUOTA_WARNING_THRESHOLD = 0.10  # 10%
QUOTA_STOP_THRESHOLD = 0.02     # 2% — hard stop to avoid running out


class DeepLClient:
    """
    Thin wrapper around the DeepL Free API.
    Manages quota and translates FR → RU (or any supported language pair).
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the client.

        Args:
            api_key: DeepL API key. Defaults to DEEPL_API_KEY env variable.

        Raises:
            ValueError: If no API key is found.
            ImportError: If the 'deepl' package is not installed.
        """
        try:
            import deepl as _deepl
            self._deepl = _deepl
        except ImportError:
            raise ImportError("Install the DeepL package: pip install deepl")

        self.api_key = api_key or os.environ.get("DEEPL_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPL_API_KEY not set. Add it to your .env file.")

        self.translator = self._deepl.Translator(self.api_key)
        self._usage_cache: Optional[object] = None

    def get_usage(self) -> dict:
        """
        Fetch current API usage.

        Returns:
            Dict with 'used', 'limit', 'remaining', 'percent_remaining'.
        """
        usage = self.translator.get_usage()
        remaining = usage.character.limit - usage.character.count
        percent = remaining / usage.character.limit if usage.character.limit else 0

        return {
            "used": usage.character.count,
            "limit": usage.character.limit,
            "remaining": remaining,
            "percent_remaining": round(percent, 4),
        }

    def check_quota(self, raise_on_low: bool = False) -> dict:
        """
        Check quota and log warnings.

        Args:
            raise_on_low: If True, raise RuntimeError when quota is critically low.

        Returns:
            Usage dict (see get_usage()).
        """
        usage = self.get_usage()
        pct = usage["percent_remaining"]

        if pct <= QUOTA_STOP_THRESHOLD:
            msg = f"DeepL quota critically low: {usage['remaining']} chars remaining ({pct:.1%})"
            logger.error(msg)
            if raise_on_low:
                raise RuntimeError(msg)
        elif pct <= QUOTA_WARNING_THRESHOLD:
            logger.warning(
                f"DeepL quota is low: {usage['remaining']} chars remaining ({pct:.1%})"
            )
        else:
            logger.debug(f"DeepL quota OK: {usage['remaining']} chars remaining ({pct:.1%})")

        return usage

    def translate(
        self,
        text: str,
        source_lang: str = "FR",
        target_lang: str = "RU",
        check_quota_before: bool = True,
    ) -> str:
        """
        Translate a text string.

        Args:
            text: Text to translate.
            source_lang: Source language code (default: "FR").
            target_lang: Target language code (default: "RU").
            check_quota_before: If True, check quota before translating.

        Returns:
            Translated text string.
        """
        if not text or not text.strip():
            return ""

        if check_quota_before:
            usage = self.check_quota(raise_on_low=True)
            if len(text) > usage["remaining"]:
                raise RuntimeError(
                    f"Text ({len(text)} chars) exceeds remaining DeepL quota "
                    f"({usage['remaining']} chars)."
                )

        result = self.translator.translate_text(
            text,
            source_lang=source_lang,
            target_lang=target_lang,
        )
        logger.debug(f"Translated {len(text)} chars {source_lang}→{target_lang}")
        return result.text

    def translate_article_fields(self, article: dict, fields: list[str]) -> dict:
        """
        Translate specific fields in an article dict (FR → RU).
        Creates new keys with `_ru` suffix.

        Args:
            article: Article dict containing fields to translate.
            fields: List of field names to translate (e.g. ['title_fr', 'content_text_fr']).

        Returns:
            Updated article dict with _ru fields added.
        """
        result = dict(article)
        for field in fields:
            if field in article and article[field]:
                ru_field = field.replace("_fr", "_ru")
                result[ru_field] = self.translate(article[field])
                logger.info(f"Translated field: {field} → {ru_field}")
        return result
