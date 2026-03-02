#!/usr/bin/env python3
"""
PRAVA — Pipeline Step 05: Import processed data into Django database

Reads:
  data/processed/1975/articles/art{NNN}.json  (validation_status: approved)
  data/processed/questions/art{NNN}_questions.json  (validation_status: approved)

Creates/updates in the Django database:
  - reglementation.RuleCategory
  - reglementation.CodeArticle
  - reglementation.TrafficSign  (from images[] with sign_code)
  - examens.ExamQuestion + QuestionOption

On re-run: updates existing records (by slug), creates new ones.

Usage:
    python scripts/pipeline/05_import.py [--law-year 1975] [--status approved] [--dry-run] [--verbose]

    # Import even 'reviewed' questions (for admin testing):
    python scripts/pipeline/05_import.py --status reviewed

See: docs/SCRIPTS.md §05_import.py
"""
import argparse
import logging
import os
import sys
from pathlib import Path

# Set up Django environment
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402
django.setup()

from scripts.utils.json_helpers import load_json  # noqa: E402

# ─── Configuration ────────────────────────────────────────────────────────────

LAW_YEAR = "1975"
ARTICLES_DIR = PROJECT_ROOT / "data" / "processed" / LAW_YEAR / "articles"
QUESTIONS_DIR = PROJECT_ROOT / "data" / "processed" / "questions"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ─── Import functions ─────────────────────────────────────────────────────────

def import_article(article: dict, dry_run: bool = False) -> tuple[str, str]:
    """
    Create or update a CodeArticle (and its RuleCategory).

    Args:
        article: Article dict from processed/1975/articles/
        dry_run: If True, don't write to DB.

    Returns:
        Tuple of (action, slug) where action is 'created', 'updated', or 'skipped'.
    """
    from apps.reglementation.models import RuleCategory, CodeArticle

    # TODO (Phase 5): Implement upsert logic:
    #   1. get_or_create RuleCategory by slug
    #   2. get_or_create CodeArticle by slug
    #   3. Update all fields
    raise NotImplementedError("Article import not yet implemented.")


def import_questions(article_slug: str, questions_data: dict, dry_run: bool = False) -> int:
    """
    Create or update ExamQuestion and QuestionOption records.

    Args:
        article_slug: Slug of the related CodeArticle.
        questions_data: Questions JSON from processed/questions/
        dry_run: If True, don't write to DB.

    Returns:
        Number of questions imported.
    """
    # TODO (Phase 5): Import ExamQuestion + QuestionOption
    raise NotImplementedError("Question import not yet implemented.")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PRAVA — Import data into Django DB")
    parser.add_argument("--law-year", default=LAW_YEAR)
    parser.add_argument(
        "--status", default="approved", choices=["approved", "reviewed"],
        help="Minimum validation_status to import (default: approved)"
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.dry_run:
        logger.info("DRY RUN — no database changes will be made.")

    article_files = sorted(ARTICLES_DIR.glob("art*.json"))
    logger.info(f"Found {len(article_files)} article files.")

    stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}

    for article_file in article_files:
        article = load_json(article_file)
        if not article:
            stats["errors"] += 1
            continue

        meta = article.get("_meta", {})
        if meta.get("validation_status") not in (args.status, "approved"):
            stats["skipped"] += 1
            continue

        try:
            action, slug = import_article(article, dry_run=args.dry_run)
            stats[action] += 1
        except Exception as e:
            logger.error(f"Error importing {article_file.name}: {e}")
            stats["errors"] += 1

    logger.info(
        f"Import complete: "
        f"{stats['created']} created, "
        f"{stats['updated']} updated, "
        f"{stats['skipped']} skipped, "
        f"{stats['errors']} errors"
    )


if __name__ == "__main__":
    main()
