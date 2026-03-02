#!/usr/bin/env python3
"""
PRAVA — Pipeline Step 05: Import processed data into Django database

Reads:
  data/processed/1975/articles/art{NNN}.json

Creates/updates in the Django database:
  - reglementation.RuleCategory  (from structure.titre)
  - reglementation.CodeArticle   (upsert by slug)
  - examens.ExamCategory         (one per article)
  - examens.Question + AnswerOption  (from exam_questions[])

On re-run: updates existing records (by slug), creates new ones.

Usage:
    python scripts/pipeline/05_import.py [--law-year 1975] [--dry-run] [--verbose]

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

TITRE_NAMES = {
    "I":    "Champ d'application et definitions",
    "II":   "Signalisation routiere",
    "III":  "Regles de circulation",
    "IV":   "Priorite",
    "V":    "Vitesse",
    "VI":   "Croisement et depassement",
    "VII":  "Intersection et priorite",
    "VIII": "Voies publiques et trottoirs",
    "IX":   "Stationnement",
    "X":    "Eclairage et signaux",
    "XI":   "Equipement des vehicules",
    "XII":  "Dispositions diverses",
}
TITRE_LIST = list(TITRE_NAMES.keys())


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_rule_category(article):
    from django.utils.text import slugify
    from apps.reglementation.models import RuleCategory
    titre = str((article.get("structure") or {}).get("titre") or "I")
    name = TITRE_NAMES.get(titre, f"Titre {titre}")
    slug = slugify(f"titre-{titre}")
    order = TITRE_LIST.index(titre) + 1 if titre in TITRE_LIST else 99
    cat, _ = RuleCategory.objects.get_or_create(slug=slug, defaults={"name": name, "order": order})
    return cat


# RuleCategory slug → ExamCategory slug (broad topic)
_TITRE_TO_EXAM_SLUG = {
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
}


def _get_exam_category(article: dict):
    """Return the broad topic ExamCategory for this article."""
    from apps.examens.models import ExamCategory
    rule_cat = _get_rule_category(article)
    exam_slug = _TITRE_TO_EXAM_SLUG.get(rule_cat.slug, "voie-publique")
    try:
        return ExamCategory.objects.get(slug=exam_slug)
    except ExamCategory.DoesNotExist:
        cat, _ = ExamCategory.objects.get_or_create(
            slug=exam_slug, defaults={"name": exam_slug.replace("-", " ").title()}
        )
        return cat


# ─── Import functions ─────────────────────────────────────────────────────────

def import_article(article: dict, dry_run: bool = False) -> tuple[str, str]:
    """
    Create or update a CodeArticle (and its RuleCategory).

    Returns:
        Tuple of (action, slug) where action is 'created', 'updated', or 'skipped'.
    """
    from apps.reglementation.models import CodeArticle

    slug = (article.get("slug") or "").strip()
    if not slug:
        return "skipped", ""
    if dry_run:
        return "skipped", slug

    category = _get_rule_category(article)
    art_number = str(article.get("article_number", "")).strip()
    defaults = {
        "article_number": art_number,
        "category": category,
        "title": (article.get("title_fr") or art_number or slug).strip(),
        "title_nl": (article.get("title_nl") or "").strip(),
        "title_ru": (article.get("title_ru") or "").strip(),
        "content": (article.get("content_html_fr") or article.get("content_md_fr") or "").strip(),
        "content_nl": (article.get("content_html_nl") or article.get("content_md_nl") or "").strip(),
        "content_ru": (article.get("content_md_ru") or "").strip(),
        "content_text": (article.get("full_text_fr") or "").strip(),
    }
    obj, created = CodeArticle.objects.get_or_create(slug=slug, defaults=defaults)
    if not created:
        for field, value in defaults.items():
            setattr(obj, field, value)
        obj.save()
        return "updated", slug
    return "created", slug


def import_questions(article: dict, dry_run: bool = False) -> int:
    """
    Create/update Questions + AnswerOptions from article["exam_questions"].

    Returns:
        Number of questions upserted.
    """
    from apps.reglementation.models import CodeArticle
    from apps.examens.models import Question, AnswerOption

    slug = article.get("slug") or ""
    exam_questions = article.get("exam_questions") or []
    if not exam_questions:
        return 0
    if dry_run:
        return len(exam_questions)

    try:
        code_article = CodeArticle.objects.get(slug=slug)
    except CodeArticle.DoesNotExist:
        code_article = None

    exam_category = _get_exam_category(article)
    count = 0

    for q_data in exam_questions:
        text_fr = (q_data.get("text_fr") or "").strip()
        if not text_fr:
            continue
        q_obj, created = Question.objects.get_or_create(
            category=exam_category,
            text=text_fr,
            defaults={
                "code_article": code_article,
                "text_nl": (q_data.get("text_nl") or "").strip(),
                "text_ru": (q_data.get("text_ru") or "").strip(),
                "difficulty": int(q_data.get("difficulty") or 2),
                "is_active": True,
            },
        )
        if not created:
            q_obj.code_article = code_article
            q_obj.text_nl = (q_data.get("text_nl") or "").strip()
            q_obj.text_ru = (q_data.get("text_ru") or "").strip()
            q_obj.difficulty = int(q_data.get("difficulty") or 2)
            q_obj.save(update_fields=["code_article", "text_nl", "text_ru", "difficulty"])

        options = q_data.get("options") or []
        if options:
            q_obj.options.all().delete()
            for idx, opt in enumerate(options):
                letter = (opt.get("letter") or chr(65 + idx)).strip()
                AnswerOption.objects.create(
                    question=q_obj,
                    letter=letter,
                    text=(opt.get("text_fr") or opt.get("text") or "").strip(),
                    text_nl=(opt.get("text_nl") or "").strip(),
                    text_ru=(opt.get("text_ru") or "").strip(),
                    is_correct=bool(opt.get("is_correct", False)),
                    order=idx,
                )
        count += 1

    return count


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PRAVA — Import data into Django DB")
    parser.add_argument("--law-year", default=LAW_YEAR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    articles_dir = PROJECT_ROOT / "data" / "processed" / args.law_year / "articles"

    if args.dry_run:
        logger.info("DRY RUN — no database changes will be made.")

    article_files = sorted(articles_dir.glob("art*.json"))
    logger.info(f"Found {len(article_files)} article files in {articles_dir}.")

    stats = {
        "articles_created": 0, "articles_updated": 0,
        "articles_skipped": 0, "articles_errors": 0,
        "questions_total": 0,  "questions_errors": 0,
    }

    for article_file in article_files:
        article = load_json(article_file)
        if not article:
            stats["articles_errors"] += 1
            continue

        try:
            action, slug = import_article(article, dry_run=args.dry_run)
            stats[f"articles_{action}"] += 1
            logger.debug(f"{action.upper():8s} article: {slug}")
        except Exception as exc:
            logger.error(f"Error importing article {article_file.name}: {exc}")
            stats["articles_errors"] += 1
            continue

        try:
            n = import_questions(article, dry_run=args.dry_run)
            stats["questions_total"] += n
            if n:
                logger.debug(f"  -> {n} questions for {slug}")
        except Exception as exc:
            logger.error(f"Error importing questions from {article_file.name}: {exc}")
            stats["questions_errors"] += 1

    logger.info(
        f"Import complete — Articles: "
        f"{stats['articles_created']} created, "
        f"{stats['articles_updated']} updated, "
        f"{stats['articles_skipped']} skipped, "
        f"{stats['articles_errors']} errors | "
        f"Questions: {stats['questions_total']} upserted, "
        f"{stats['questions_errors']} errors"
    )
    return stats


if __name__ == "__main__":
    main()
