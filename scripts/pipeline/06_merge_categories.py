#!/usr/bin/env python3
"""
PRAVA — Pipeline Step 06: Merge / cleanup ExamCategories.

The new `05_import.py` assigns questions directly to broad ExamCategories,
so per-article ExamCategories (slug starts with "art-") should no longer appear.

This script is kept as a cleanup/migration utility to:
  1. Reassign questions from any stale per-article ExamCategories to the correct
     broad topic category (based on the article's RuleCategory slug)
  2. Delete the now-empty art-* ExamCategories

It handles both the old (pre-multi-law) slug format ("titre-i") and the new
format ("{law_id}-titre-{n}", "{law_id}-chapitre-{n}").

Usage:
    python scripts/pipeline/06_merge_categories.py [--dry-run]
"""
import argparse
import logging
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from apps.examens.models import ExamCategory, Question

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── RuleCategory slug → broad ExamCategory slug ───────────────────────────────
# Covers both old format ("titre-i") and new format ("1975-titre-i")
# For non-AR1975 laws: maps to default broad category by law_id prefix
TITRE_TO_EXAM = {
    # AR 1975 — old slug format (legacy, before multi-law support)
    "titre-i":    "voie-publique",
    "titre-ii":   "signalisation",
    "titre-iii":  "voie-publique",
    "titre-iv":   "priorites",
    "titre-v":    "vitesse-freinage",
    "titre-vi":   "depassement",
    "titre-vii":  "priorites",
    "titre-viii": "voie-publique",
    "titre-ix":   "arret-stationnement",
    "titre-x":    "obligations",
    "titre-xi":   "obligations",
    "titre-xii":  "situations",
    # AR 1975 — new slug format (prefixed with law_id)
    "1975-titre-i":    "voie-publique",
    "1975-titre-ii":   "signalisation",
    "1975-titre-iii":  "voie-publique",
    "1975-titre-iv":   "priorites",
    "1975-titre-v":    "vitesse-freinage",
    "1975-titre-vi":   "depassement",
    "1975-titre-vii":  "priorites",
    "1975-titre-viii": "voie-publique",
    "1975-titre-ix":   "arret-stationnement",
    "1975-titre-x":    "obligations",
    "1975-titre-xi":   "obligations",
    "1975-titre-xii":  "situations",
}

# Default exam category for laws without explicit titre mapping
LAW_PREFIX_TO_EXAM = {
    "1968": "situations",
    "2005": "situations",
    "1998": "obligations",
    "2006": "obligations",
    "1976": "signalisation",
    "1975b": "signalisation",
    "1968b": "obligations",
    "1985": "obligations",
}

DEFAULT_EXAM_SLUG = "voie-publique"


def _resolve_exam_slug(rule_cat_slug: str | None) -> str:
    """Map a RuleCategory slug to a broad ExamCategory slug."""
    if not rule_cat_slug:
        return DEFAULT_EXAM_SLUG
    # Direct lookup
    if rule_cat_slug in TITRE_TO_EXAM:
        return TITRE_TO_EXAM[rule_cat_slug]
    # Try law prefix: "1968-chapitre-i" → prefix "1968" → "situations"
    prefix = rule_cat_slug.split("-")[0]
    if prefix in LAW_PREFIX_TO_EXAM:
        return LAW_PREFIX_TO_EXAM[prefix]
    return DEFAULT_EXAM_SLUG



def run(dry_run: bool = False):
    art_cats = list(ExamCategory.objects.filter(slug__startswith="art-"))
    logger.info(f"Found {len(art_cats)} per-article ExamCategories to merge")

    if not art_cats:
        logger.info("Nothing to do — no per-article ExamCategories found.")
        return

    # Pre-load broad topic categories
    broad_cats = {c.slug: c for c in ExamCategory.objects.exclude(slug__startswith="art-")}
    logger.info(f"Broad topic categories: {list(broad_cats.keys())}")

    moved = 0
    skipped = 0
    deleted = 0

    for art_cat in art_cats:
        questions = list(Question.objects.filter(category=art_cat).select_related(
            "code_article__category"
        ))

        if not questions:
            logger.info(f"  {art_cat.slug}: empty, will delete")
            if not dry_run:
                art_cat.delete()
                deleted += 1
            continue

        for q in questions:
            rule_cat_slug = None
            if q.code_article and q.code_article.category:
                rule_cat_slug = q.code_article.category.slug

            target_slug = _resolve_exam_slug(rule_cat_slug)
            target_cat = broad_cats.get(target_slug)

            if not target_cat:
                logger.warning(f"  ⚠ No broad category '{target_slug}' found — skipping Q#{q.pk}")
                skipped += 1
                continue

            logger.debug(f"  Q#{q.pk} ({art_cat.slug} → {target_slug})")
            if not dry_run:
                q.category = target_cat
                q.save(update_fields=["category"])
            moved += 1

        # Delete empty art-* category after moving all questions
        if not dry_run:
            art_cat.delete()
            deleted += 1
        else:
            first_rule_slug = (questions[0].code_article.category.slug
                               if questions[0].code_article else None)
            logger.info(f"  [dry-run] would move {len(questions)}q from "
                        f"{art_cat.slug} → {_resolve_exam_slug(first_rule_slug)}")

    logger.info(f"Done: {moved} questions moved, {deleted} art-* categories deleted, {skipped} skipped")

    if not dry_run:
        for cat in ExamCategory.objects.exclude(slug__startswith="art-").order_by("order"):
            q_count = Question.objects.filter(category=cat).count()
            logger.info(f"  {cat.slug:30} → {q_count} questions")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
