#!/usr/bin/env python3
"""
PRAVA — Pipeline Step 06: Merge per-article ExamCategories into broad topic categories.

Problem: 05_import.py creates one ExamCategory per article (art-1, art-2, …).
         There are also 8 hand-curated broad topic ExamCategories.

This script:
  1. Reassigns all questions from art-* categories to the matching broad category
     based on the article's RuleCategory (titre)
  2. Deletes the now-empty art-* ExamCategories

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

# RuleCategory slug → ExamCategory slug
TITRE_TO_EXAM = {
    "titre-i":    "voie-publique",       # Champ d'application et définitions
    "titre-ii":   "signalisation",       # Signalisation routière
    "titre-iii":  "voie-publique",       # Règles de circulation
    "titre-iv":   "priorites",           # Priorité relative
    "titre-v":    "vitesse-freinage",    # Vitesse
    "titre-vi":   "depassement",         # Croisement et dépassement
    "titre-vii":  "priorites",           # Intersection et priorité
    "titre-viii": "voie-publique",       # Voies publiques et trottoirs
    "titre-ix":   "arret-stationnement", # Stationnement
    "titre-x":    "obligations",         # Éclairage et signaux
    "titre-xi":   "obligations",         # Équipement des véhicules
    "titre-xii":  "situations",          # Dispositions diverses
}

DEFAULT_EXAM_SLUG = "voie-publique"


def run(dry_run: bool = False):
    art_cats = list(ExamCategory.objects.filter(slug__startswith="art-"))
    logger.info(f"Found {len(art_cats)} per-article ExamCategories to merge")

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

            target_slug = TITRE_TO_EXAM.get(rule_cat_slug, DEFAULT_EXAM_SLUG)
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
            logger.info(f"  [dry-run] would move {len(questions)}q from {art_cat.slug} → "
                        f"{TITRE_TO_EXAM.get(questions[0].code_article.category.slug if questions[0].code_article else None, DEFAULT_EXAM_SLUG)}")

    logger.info(f"Done: {moved} questions moved, {deleted} art-* categories deleted, {skipped} skipped")

    if not dry_run:
        # Show final counts
        for cat in ExamCategory.objects.exclude(slug__startswith="art-").order_by("order"):
            q_count = Question.objects.filter(category=cat).count()
            logger.info(f"  {cat.slug:30} → {q_count} questions")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
