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

from scripts.utils.json_helpers import load_json          # noqa: E402
from scripts.utils.laws_registry import get_law, law_ids  # noqa: E402

# ─── Configuration ────────────────────────────────────────────────────────────

_DEFAULT_LAW = "1975"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Structure label → RuleCategory name (AR 1975 titres) ──────────────────────
_1975_TITRE_NAMES = {
    "I":    "Titre I. Dispositions préliminaires",
    "II":   "Titre II. Règles d'usage de la voie publique",
    "III":  "Titre III. Signalisation routière",
    "IV":   "Titre IV. Prescriptions techniques",
    "V":    "Titre V. Dispositions abrogatoires et transitoires",
    "VI":   "Titre VI. Croisement et dépassement",
    "VII":  "Titre VII. Intersection et priorité",
    "VIII": "Titre VIII. Voies publiques et trottoirs",
    "IX":   "Titre IX. Stationnement",
    "X":    "Titre X. Éclairage et signaux",
    "XI":   "Titre XI. Équipement des véhicules",
    "XII":  "Titre XII. Dispositions diverses",
}

# ── Default broad ExamCategory per law ────────────────────────────────────────
_LAW_DEFAULT_EXAM_SLUG = {
    "1968":  "situations",
    "2005":  "situations",
    "1998":  "obligations",
    "2006":  "obligations",
    "1976":  "signalisation",
    "1975b": "signalisation",
    "1968b": "obligations",
    "1985":  "obligations",
    "1989":  "obligations",
    "2001":  "obligations",
}


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


_EXAM_SLUG_META = {
    "voie-publique":       {"name": "Voie Publique",        "icon": "road",               "order": 1},
    "signalisation":       {"name": "Signalisation",        "icon": "sign-post",          "order": 2},
    "priorites":           {"name": "Priorités",            "icon": "arrow-right-circle", "order": 3},
    "vitesse-freinage":    {"name": "Vitesse & Freinage",   "icon": "gauge",              "order": 4},
    "depassement":         {"name": "Dépassement",          "icon": "arrows-pointing-out","order": 5},
    "arret-stationnement": {"name": "Arrêt & Stationnement","icon": "parking",            "order": 6},
    "obligations":         {"name": "Obligations",          "icon": "id-card",            "order": 7},
    "situations":          {"name": "Situations",           "icon": "map",                "order": 8},
}


def _get_exam_category(article: dict, law_id: str):
    """Return the broad topic ExamCategory for this article."""
    from apps.examens.models import ExamCategory

    if law_id == "1975":
        rule_cat = _get_rule_category(article, law_id)
        short_slug = rule_cat.slug.replace(f"{law_id}-", "", 1)
        exam_slug = _TITRE_TO_EXAM_SLUG.get(short_slug, "voie-publique")
    else:
        exam_slug = _LAW_DEFAULT_EXAM_SLUG.get(law_id, "situations")

    meta = _EXAM_SLUG_META.get(exam_slug, {"name": exam_slug.replace("-", " ").title(), "icon": "", "order": 99})
    cat, _ = ExamCategory.objects.get_or_create(
        slug=exam_slug,
        defaults={"name": meta["name"], "icon": meta["icon"], "order": meta["order"]},
    )
    # Patch icon/name if they were created without metadata (legacy empty values)
    if not cat.icon and meta["icon"]:
        ExamCategory.objects.filter(pk=cat.pk).update(icon=meta["icon"], name=meta["name"], order=meta["order"])
        cat.refresh_from_db()
    return cat


# ─── Helpers — structure ──────────────────────────────────────────────

def _structure_slug(article: dict, law_id: str) -> tuple[str, str, int]:
    from django.utils.text import slugify
    structure = article.get("structure") or {}
    titre = str(structure.get("titre") or "")
    chap = str(structure.get("chapitre") or "")

    if law_id == "1975" and titre:
        name = _1975_TITRE_NAMES.get(titre, f"Titre {titre}")
        slug = slugify(f"{law_id}-titre-{titre}")
        titre_list = list(_1975_TITRE_NAMES.keys())
        order = titre_list.index(titre) + 1 if titre in titre_list else 99
    elif chap:
        slug = slugify(f"{law_id}-chapitre-{chap}")
        name = f"Chapitre {chap}"
        order = 0
    elif titre:
        slug = slugify(f"{law_id}-titre-{titre}")
        name = f"Titre {titre}"
        order = 0
    else:
        slug = slugify(f"{law_id}-general")
        name = "Général"
        order = 0
    return slug, name, order


_1975_TITRE_ICONS = {
    "i":   "book-open",
    "ii":  "car",
    "iii": "sign-post",
    "iv":  "wrench",
    "v":   "gavel",
}


def _get_rule_category(article: dict, law_id: str):
    from apps.reglementation.models import RuleCategory
    slug, name, order = _structure_slug(article, law_id)
    structure = article.get("structure") or {}
    titre = str(structure.get("titre") or "").lower()
    icon = _1975_TITRE_ICONS.get(titre, "") if law_id == "1975" else ""
    cat, created = RuleCategory.objects.get_or_create(
        slug=slug,
        defaults={"name": name, "order": order, "law_id": law_id, "icon": icon},
    )
    if not created and not cat.icon and icon:
        RuleCategory.objects.filter(pk=cat.pk).update(icon=icon)
        cat.icon = icon
    return cat


# ─── Import functions ─────────────────────────────────────────────────────────

def import_article(article: dict, law_id: str, dry_run: bool = False) -> tuple[str, str]:
    """
    Create or update a CodeArticle (and its RuleCategory).

    DB slug = "{law_id}-{article_slug}" to avoid cross-law conflicts.

    Returns:
        Tuple of (action, db_slug).
    """
    from apps.reglementation.models import CodeArticle

    article_slug = (article.get("slug") or "").strip()
    if not article_slug:
        return "skipped", ""

    db_slug = f"{law_id}-{article_slug}"

    if dry_run:
        return "skipped", db_slug

    category = _get_rule_category(article, law_id)
    art_number = str(article.get("article_number", "")).strip()
    defaults = {
        "article_number": art_number,
        "category": category,
        "law_id": law_id,
        "title": (article.get("title_fr") or art_number or db_slug).strip(),
        "title_nl": (article.get("title_nl") or "").strip(),
        "title_ru": (article.get("title_ru") or "").strip(),
        "content": (article.get("content_html_fr") or article.get("content_md_fr") or "").strip().replace('/media/image/orig/', 'https://www.codedelaroute.be/media/image/orig/'),
        "content_nl": (article.get("content_html_nl") or article.get("content_md_nl") or "").strip().replace('/media/image/orig/', 'https://www.codedelaroute.be/media/image/orig/'),
        "content_ru": (article.get("content_md_ru") or "").strip().replace('/media/image/orig/', 'https://www.codedelaroute.be/media/image/orig/'),
        "content_text": (article.get("full_text_fr") or "").strip(),
    }
    obj, created = CodeArticle.objects.get_or_create(slug=db_slug, defaults=defaults)
    if not created:
        for field, value in defaults.items():
            setattr(obj, field, value)
        obj.save()
        return "updated", db_slug
    return "created", db_slug


def import_questions(article: dict, law_id: str, dry_run: bool = False) -> int:
    """
    Create/update Questions + AnswerOptions from article["exam_questions"].

    Returns:
        Number of questions upserted.
    """
    from apps.reglementation.models import CodeArticle, TrafficSign
    from apps.examens.models import Question, AnswerOption

    article_slug = article.get("slug") or ""
    db_slug = f"{law_id}-{article_slug}" if article_slug else ""
    exam_questions = article.get("exam_questions") or []
    if not exam_questions:
        return 0
    if dry_run:
        return len(exam_questions)

    try:
        code_article = CodeArticle.objects.get(slug=db_slug)
    except CodeArticle.DoesNotExist:
        code_article = None

    exam_category = _get_exam_category(article, law_id)
    count = 0

    for q_data in exam_questions:
        text_fr = (q_data.get("text_fr") or "").strip()
        if not text_fr:
            continue

        # Parse image field (dict with sign_code + generation_prompt)
        image_data = q_data.get("image") or {}
        sign_code = (image_data.get("sign_code") or "").strip() if isinstance(image_data, dict) else ""
        image_prompt = (image_data.get("generation_prompt") or "").strip() if isinstance(image_data, dict) else ""

        # Resolve traffic sign FK
        traffic_sign = None
        if sign_code:
            traffic_sign = TrafficSign.objects.filter(code=sign_code).first()

        q_obj, created = Question.objects.get_or_create(
            category=exam_category,
            text=text_fr,
            defaults={
                "code_article": code_article,
                "text_nl": (q_data.get("text_nl") or "").strip(),
                "text_ru": (q_data.get("text_ru") or "").strip(),
                "difficulty": int(q_data.get("difficulty") or 2),
                "image_prompt": image_prompt,
                "image_sign_code": sign_code,
                "traffic_sign": traffic_sign,
                "is_active": True,
            },
        )
        if not created:
            q_obj.code_article = code_article
            q_obj.text_nl = (q_data.get("text_nl") or "").strip()
            q_obj.text_ru = (q_data.get("text_ru") or "").strip()
            q_obj.difficulty = int(q_data.get("difficulty") or 2)
            q_obj.image_prompt = image_prompt
            q_obj.image_sign_code = sign_code
            q_obj.traffic_sign = traffic_sign
            q_obj.save(update_fields=["code_article", "text_nl", "text_ru", "difficulty",
                                      "image_prompt", "image_sign_code", "traffic_sign"])

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
    parser.add_argument("--law", default=_DEFAULT_LAW,
                        help=f"Law ID to import (default: {_DEFAULT_LAW}). Use --list-laws to see all.")
    parser.add_argument("--law-year", default=None,
                        help="Alias for --law (legacy, deprecated)")
    parser.add_argument("--list-laws", action="store_true", help="List available laws and exit")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.list_laws:
        for lid in law_ids():
            info = get_law(lid)
            print(f"  {lid:8}  {info['title_fr']}")
        return

    law_id = args.law_year or args.law
    try:
        law_info = get_law(law_id)
    except KeyError:
        logger.error(f"Unknown law ID: {law_id!r}. Use --list-laws to see valid IDs.")
        sys.exit(1)

    logger.info(f"Law: {law_id} — {law_info['title_fr']}")

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    articles_dir = PROJECT_ROOT / "data" / "processed" / law_id / "articles"
    if not articles_dir.exists():
        logger.error(f"Articles directory not found: {articles_dir}")
        sys.exit(1)

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
            action, db_slug = import_article(article, law_id, dry_run=args.dry_run)
            stats[f"articles_{action}"] += 1
            logger.debug(f"{action.upper():8s} article: {db_slug}")
        except Exception as exc:
            logger.error(f"Error importing article {article_file.name}: {exc}")
            stats["articles_errors"] += 1
            continue

        try:
            n = import_questions(article, law_id, dry_run=args.dry_run)
            stats["questions_total"] += n
            if n:
                logger.debug(f"  -> {n} questions for {db_slug}")
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
