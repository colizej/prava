#!/usr/bin/env python3
"""
PRAVA — Pipeline Step 04: Generate exam questions via Gemini 1.5 Flash

Reads:   data/processed/1975/articles/art-{slug}.json
Writes:  same files — fills in the `exam_questions` field of each article

Generates 5 questions per article (trilingual FR/NL/RU):
  - 2 THEORETICAL  (definition / signal meaning)
  - 3 PRACTICAL    (real driving scenario application)

Each question:
  - text_fr / text_nl / text_ru
  - 3 answer options (A/B/C) with is_correct flag  — each trilingual
  - difficulty 1–3
  - explanation_fr / explanation_nl / explanation_ru
  - optional image.sign_code reference

Incremental: skips articles that already have exam_questions populated.
Rate limit: 15 req/min (Gemini Free tier) → 4s delay between calls.

Usage:
    python scripts/pipeline/04_questions.py [--dry-run] [--verbose]
    python scripts/pipeline/04_questions.py --article 21
    python scripts/pipeline/04_questions.py --limit 10    # first 10 articles only
    python scripts/pipeline/04_questions.py --regenerate  # overwrite existing

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

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from scripts.utils.gemini_client import GeminiClient  # noqa: E402
from scripts.utils.json_helpers import load_json, save_json  # noqa: E402

# ─── Configuration ────────────────────────────────────────────────────────────

LAW_YEAR = "1975"
ARTICLES_DIR = PROJECT_ROOT / "data" / "processed" / LAW_YEAR / "articles"

# How many questions to generate per article
QUESTIONS_PER_ARTICLE = 5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ─── Prompt builder ────────────────────────────────────────────────────────────

def build_prompt(article: dict) -> str:
    """
    Build the generation prompt from a processed article dict.

    Uses content_md_fr (Markdown — better structure than plain text) and
    includes sign_codes and cross_refs as extra context for Gemini.

    Args:
        article: Processed article dict from 03_process.py output.

    Returns:
        String prompt to send to Gemini.
    """
    number = article.get("article_number", "?")
    title_fr = article.get("title_fr", "")
    content_fr = article.get("content_md_fr") or article.get("full_text_fr", "")
    content_nl = article.get("content_md_nl") or article.get("full_text_nl", "")
    sign_codes = article.get("sign_codes", [])
    cross_refs = article.get("cross_refs", [])

    lines = [
        f"=== Article {number}: {title_fr} ===",
        "",
        "[FR]",
        content_fr[:3000],  # cap at 3000 chars to stay within token limits
    ]

    if content_nl:
        lines += ["", "[NL]", content_nl[:1500]]

    if sign_codes:
        lines += ["", f"Panneaux de signalisation mentionnés: {', '.join(sign_codes)}"]

    if cross_refs:
        lines += [f"Références croisées: {', '.join(cross_refs[:5])}"]

    return "\n".join(lines)


# ─── Validation ────────────────────────────────────────────────────────────────

REQUIRED_QUESTION_FIELDS = {
    "type", "difficulty", "text_fr", "text_nl", "text_ru",
    "options", "explanation_fr", "explanation_nl", "explanation_ru",
}

REQUIRED_OPTION_FIELDS = {"letter", "text_fr", "text_nl", "text_ru", "is_correct"}


def validate_questions(questions: list[dict]) -> tuple[list[dict], list[str]]:
    """
    Validate a list of question dicts from Gemini.

    Returns:
        (valid_questions, error_messages)
    """
    valid = []
    errors = []

    for i, q in enumerate(questions):
        missing = REQUIRED_QUESTION_FIELDS - set(q.keys())
        if missing:
            errors.append(f"Q{i+1}: missing fields {missing}")
            continue

        if q.get("difficulty") not in (1, 2, 3):
            errors.append(f"Q{i+1}: invalid difficulty {q.get('difficulty')!r}")
            continue

        if not isinstance(q.get("options"), list) or len(q["options"]) < 2:
            errors.append(f"Q{i+1}: need at least 2 options")
            continue

        # Validate options
        opt_errors = []
        has_correct = False
        for j, opt in enumerate(q["options"]):
            missing_opt = REQUIRED_OPTION_FIELDS - set(opt.keys())
            if missing_opt:
                opt_errors.append(f"option {j}: missing {missing_opt}")
            if opt.get("is_correct"):
                has_correct = True
        if opt_errors:
            errors.append(f"Q{i+1}: {'; '.join(opt_errors)}")
            continue
        if not has_correct:
            errors.append(f"Q{i+1}: no correct option marked")
            continue

        valid.append(q)

    return valid, errors


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PRAVA — Generate exam questions via Gemini")
    parser.add_argument(
        "--article", type=str, default=None, metavar="NUMBER",
        help="Process a single article by number (e.g. --article 21)"
    )
    parser.add_argument(
        "--limit", type=int, default=None, metavar="N",
        help="Process at most N articles (useful for testing)"
    )
    parser.add_argument(
        "--regenerate", action="store_true",
        help="Regenerate questions even if already present"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be generated without calling the API"
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not ARTICLES_DIR.exists():
        logger.error(f"Articles dir not found: {ARTICLES_DIR}")
        logger.error("Run 03_process.py first.")
        sys.exit(1)

    # ── Collect article files ────────────────────────────────────────────────
    if args.article:
        # Normalise: "21" → "art-21"
        slug = args.article if args.article.startswith("art-") else f"art-{args.article}"
        article_files = list(ARTICLES_DIR.glob(f"{slug}.json"))
        if not article_files:
            logger.error(f"Article file {slug}.json not found in {ARTICLES_DIR}")
            sys.exit(1)
    else:
        article_files = sorted(ARTICLES_DIR.glob("art-*.json"))

    # Filter out already-done (unless --regenerate)
    pending_files = []
    skipped = 0
    for f in article_files:
        data = load_json(f)
        if data and data.get("exam_questions") and not args.regenerate:
            skipped += 1
        else:
            pending_files.append(f)

    if args.limit:
        pending_files = pending_files[: args.limit]

    logger.info(
        f"Articles: {len(article_files)} total | "
        f"{skipped} already have questions | "
        f"{len(pending_files)} pending"
        + (f" (limited to {args.limit})" if args.limit else "")
    )

    if not pending_files:
        logger.info("Nothing to do.")
        return

    if args.dry_run:
        for f in pending_files[:5]:
            art = load_json(f)
            logger.info(f"  [DRY] {f.stem} — {art.get('title_fr', '')[:60]}")
        if len(pending_files) > 5:
            logger.info(f"  ... and {len(pending_files) - 5} more")
        logger.info(f"DRY RUN — would call Gemini {len(pending_files)} times")
        return

    # ── Initialise Gemini client ─────────────────────────────────────────────
    client = GeminiClient()

    # ── Generation loop ──────────────────────────────────────────────────────
    generated = failed = 0

    for i, article_file in enumerate(pending_files, 1):
        article = load_json(article_file)
        if not article:
            logger.warning(f"Could not load {article_file}")
            continue

        number = article.get("article_number", article_file.stem)
        title = article.get("title_fr", "")

        logger.info(f"[{i:>3}/{len(pending_files)}] Art {number}: {title[:55]}")

        prompt = build_prompt(article)
        logger.debug(f"  Prompt length: {len(prompt)} chars")

        questions_raw = client.generate_questions(article, prompt_override=prompt)

        if not questions_raw:
            logger.error(f"  No questions returned — skipping Art {number}")
            failed += 1
            continue

        valid_questions, errs = validate_questions(questions_raw)

        if errs:
            for e in errs:
                logger.warning(f"  Validation: {e}")

        if not valid_questions:
            logger.error(f"  All questions failed validation — skipping Art {number}")
            failed += 1
            continue

        logger.info(f"  ✓ {len(valid_questions)} valid questions")

        # Write back into the article file
        article["exam_questions"] = valid_questions
        article["_meta"]["questions_generated_at"] = __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        article["_meta"]["questions_model"] = "gemini-1.5-flash"
        article["_meta"]["questions_count"] = len(valid_questions)
        save_json(article, article_file)

        generated += 1

    logger.info(
        f"Done. {generated} articles got questions | {failed} failed | "
        f"{skipped} already had questions."
    )


if __name__ == "__main__":
    main()

