#!/usr/bin/env python3
"""
PRAVA — Pipeline Step 04: Generate exam questions via Gemini 1.5 Flash

Reads:  data/processed/1975/articles/art{NNN}.json
Writes: data/processed/questions/art{NNN}_questions.json

Generates 5 questions per article:
  - 2 theoretical (definition / signal meaning)
  - 3 practical (application in a driving scenario)

Questions are generated in FR, NL, and RU.
On re-run: skips articles that already have a questions file.

Usage:
    python scripts/pipeline/04_questions.py [--article art001] [--regenerate] [--dry-run] [--verbose]

Requires:
    GEMINI_API_KEY in .env
    pip install google-generativeai

See: docs/SCRIPTS.md §04_questions.py
"""
import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.gemini_client import GeminiClient  # noqa: E402
from scripts.utils.json_helpers import load_json, save_json  # noqa: E402

# ─── Configuration ────────────────────────────────────────────────────────────

LAW_YEAR = "1975"
ARTICLES_DIR = PROJECT_ROOT / "data" / "processed" / LAW_YEAR / "articles"
QUESTIONS_DIR = PROJECT_ROOT / "data" / "processed" / "questions"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="PRAVA — Generate exam questions via Gemini")
    parser.add_argument("--article", help="Process only this article (e.g. art001)")
    parser.add_argument("--regenerate", action="store_true", help="Regenerate even if questions file exists")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not ARTICLES_DIR.exists():
        logger.error(f"Articles directory not found: {ARTICLES_DIR}")
        logger.error("Run 03_process.py first.")
        sys.exit(1)

    # Determine which articles to process
    if args.article:
        article_files = list(ARTICLES_DIR.glob(f"{args.article}.json"))
    else:
        article_files = sorted(ARTICLES_DIR.glob("art*.json"))

    logger.info(f"Found {len(article_files)} articles to process.")

    client = GeminiClient()

    for article_file in article_files:
        slug = article_file.stem  # e.g. "art001"
        questions_file = QUESTIONS_DIR / f"{slug}_questions.json"

        if questions_file.exists() and not args.regenerate:
            logger.debug(f"Skipping {slug} — questions already exist.")
            continue

        article = load_json(article_file)
        if not article:
            logger.warning(f"Could not load {article_file}, skipping.")
            continue

        logger.info(f"Generating questions for {slug}...")

        if args.dry_run:
            logger.info(f"DRY RUN — would call Gemini for {slug}.")
            continue

        questions = client.generate_questions(article)

        if not questions:
            logger.error(f"No questions generated for {slug}.")
            continue

        output = {
            "article_number": article.get("article_number", ""),
            "article_slug": article.get("slug", slug),
            "law_year": LAW_YEAR,
            "generated_by": "gemini-1.5-flash",
            "questions": questions,
        }
        QUESTIONS_DIR.mkdir(parents=True, exist_ok=True)
        save_json(output, questions_file)
        logger.info(f"Saved {len(questions)} questions → {questions_file}")

    logger.info("Step 04 complete.")


if __name__ == "__main__":
    main()
