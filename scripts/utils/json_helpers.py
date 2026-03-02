"""
PRAVA — JSON utility helpers.
Load, save, validate, and diff JSON data files.
"""
import json
import logging
from copy import deepcopy
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def load_json(path: str | Path) -> Any:
    """
    Load a JSON file. Returns None if the file doesn't exist.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed JSON data, or None if file not found.
    """
    path = Path(path)
    if not path.exists():
        logger.warning(f"JSON file not found: {path}")
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, path: str | Path, indent: int = 2) -> None:
    """
    Save data to a JSON file, creating parent directories if needed.

    Args:
        data: JSON-serializable object.
        path: Destination file path.
        indent: JSON indentation (default: 2).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
    logger.debug(f"Saved JSON: {path}")


def diff_json(old: dict | list, new: dict | list) -> dict:
    """
    Compare two JSON objects (dicts or lists) and return a summary of changes.
    Designed for comparing scraped law data between runs.

    Args:
        old: Previous version of the data.
        new: New version of the data.

    Returns:
        Dict with keys: 'added', 'removed', 'modified', 'unchanged'
    """
    if not isinstance(old, dict) or not isinstance(new, dict):
        # For simple values or lists, just check equality
        return {"changed": old != new, "old": old, "new": new}

    old_keys = set(old.keys())
    new_keys = set(new.keys())

    added = {k: new[k] for k in new_keys - old_keys}
    removed = {k: old[k] for k in old_keys - new_keys}
    modified = {}
    unchanged = []

    for k in old_keys & new_keys:
        if old[k] != new[k]:
            modified[k] = {"old": old[k], "new": new[k]}
        else:
            unchanged.append(k)

    return {
        "added": added,
        "removed": removed,
        "modified": modified,
        "unchanged_count": len(unchanged),
    }


def diff_articles(old_articles: list[dict], new_articles: list[dict], key: str = "number") -> dict:
    """
    Diff two lists of articles by their unique key (e.g., article number).

    Args:
        old_articles: Previous list of article dicts.
        new_articles: New list of article dicts.
        key: The field used as unique identifier.

    Returns:
        Dict with 'added', 'removed', 'modified' article lists.
    """
    old_map = {a[key]: a for a in old_articles if key in a}
    new_map = {a[key]: a for a in new_articles if key in a}

    added = [new_map[k] for k in set(new_map) - set(old_map)]
    removed = [old_map[k] for k in set(old_map) - set(new_map)]
    modified = []

    for k in set(old_map) & set(new_map):
        old_text = old_map[k].get("content_text", "")
        new_text = new_map[k].get("content_text", "")
        if old_text != new_text:
            modified.append({
                "number": k,
                "title": new_map[k].get("title", ""),
                "content_changed": True,
            })

    return {
        "added": added,
        "removed": removed,
        "modified": modified,
        "total_old": len(old_articles),
        "total_new": len(new_articles),
    }


def validate_article_schema(article: dict) -> list[str]:
    """
    Basic validation of an article dict against required fields.
    Returns a list of error messages (empty = valid).

    Args:
        article: Article dict to validate.

    Returns:
        List of validation error strings.
    """
    required_fields = [
        "law_year", "article_number", "slug", "category",
        "title_fr", "content_html_fr", "content_text_fr",
        "_meta"
    ]
    errors = []
    for field in required_fields:
        if field not in article:
            errors.append(f"Missing required field: '{field}'")
    return errors
