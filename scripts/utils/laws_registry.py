"""
PRAVA — Central registry of Belgian road law documents.

Each entry describes a law available on codedelaroute.be / wegcode.be.
The `slug` is the URL path segment shared by both sites:
  FR: https://www.codedelaroute.be/fr/regelgeving/{slug}
  NL: https://www.wegcode.be/nl/regelgeving/{slug}

Usage:
    from scripts.utils.laws_registry import LAWS, get_law, law_ids

    law = get_law("1968")     # → dict with all metadata
    print(law_ids())           # → ["1975", "1968", "2005", ...]
"""

# ─── Registry ─────────────────────────────────────────────────────────────────

LAWS: dict[str, dict] = {

    # ── Already processed ──────────────────────────────────────────────────────
    "1975": {
        "slug": "1975120109~hra8v386pu",
        "title_fr": "AR du 1er décembre 1975 — Règlement général sur la police de la circulation routière",
        "title_nl": "KB van 1 december 1975 — Algemeen reglement op de politie van het wegverkeer",
        "theme": "regles-de-circulation",
        "theme_ru": "Правила дорожного движения",
        "type": "Arrêté royal",
        "scope": "Belgique",
        "priority": 1,
        "notes": "Code de la route principal — 122 articles",
    },

    # ── Politique criminelle (sanctions, infractions) ──────────────────────────
    "1968": {
        "slug": "1968031601~invynqx4tj",
        "title_fr": "Loi du 16 mars 1968 relative à la police de la circulation routière",
        "title_nl": "Wet van 16 maart 1968 betreffende de politie over het wegverkeer",
        "theme": "politique-criminelle",
        "theme_ru": "Уголовная политика / Санкции",
        "type": "Loi",
        "scope": "Belgique",
        "priority": 2,
        "notes": "Loi-cadre: définit les infractions, les peines, la déchéance du droit de conduire",
    },
    "2005": {
        "slug": "2005014182~5yjza0ajqn",
        "title_fr": "AR du 30 septembre 2005 — Infractions par degré (1–4)",
        "title_nl": "KB van 30 september 2005 — Overtredingen per graad (1–4)",
        "theme": "politique-criminelle",
        "theme_ru": "Уголовная политика / Санкции",
        "type": "Arrêté royal",
        "scope": "Belgique",
        "priority": 2,
        "notes": "Classifie chaque infraction du code de la route en degré 1, 2, 3 ou 4",
    },

    # ── Permis de conduire ─────────────────────────────────────────────────────
    "1998": {
        "slug": "1998014078~w8ylf1lyws",
        "title_fr": "AR du 23 mars 1998 relatif au permis de conduire",
        "title_nl": "KB van 23 maart 1998 betreffende het rijbewijs",
        "theme": "permis-de-conduire",
        "theme_ru": "Водительское удостоверение",
        "type": "Arrêté royal",
        "scope": "Belgique",
        "priority": 3,
        "notes": "Catégories de permis, conditions médicales, échange, retrait, points",
    },
    "2006": {
        "slug": "2006014162~khugwmgcip",
        "title_fr": "AR du 10 juillet 2006 relatif au permis de conduire pour les véhicules de catégorie B",
        "title_nl": "KB van 10 juli 2006 betreffende het rijbewijs voor voertuigen van categorie B",
        "theme": "permis-de-conduire",
        "theme_ru": "Водительское удостоверение",
        "type": "Arrêté royal",
        "scope": "Belgique",
        "priority": 3,
        "notes": "Formation, examen théorique et pratique, conduite accompagnée (cat. B)",
    },

    # ── Infrastructure et signalisation ───────────────────────────────────────
    "1976": {
        "slug": "1976101105~j6siwtihko",
        "title_fr": "AM du 11 octobre 1976 — Dimensions et placement de la signalisation routière",
        "title_nl": "MB van 11 oktober 1976 — Minimumafmetingen en plaatsingsvoorwaarden verkeerstekens",
        "theme": "infrastructure-et-signalisation",
        "theme_ru": "Инфраструктура и сигнализация",
        "type": "Arrêté ministériel",
        "scope": "Belgique",
        "priority": 4,
        "notes": "Dimensions minimales, placement des panneaux, marquages au sol",
    },
    "1975b": {
        "slug": "1975120125~q1rrr4iaw7",
        "title_fr": "AM du 1er décembre 1975 — Caractéristiques des disques, signalisations et plaques",
        "title_nl": "MB van 1 december 1975 — Kenmerken van bepaalde schijven, signalen en platen",
        "theme": "infrastructure-et-signalisation",
        "theme_ru": "Инфраструктура и сигнализация",
        "type": "Arrêté ministériel",
        "scope": "Belgique",
        "priority": 4,
        "notes": "Complète l'AR 1975 — couleurs, formes, dimensions exactes de chaque panneau",
    },

    # ── Conditions techniques ──────────────────────────────────────────────────
    "1968b": {
        "slug": "1968031501~fhniyzocos",
        "title_fr": "AR du 15 mars 1968 — Conditions techniques des véhicules automobiles",
        "title_nl": "KB van 15 maart 1968 — Technische eisen voor motorvoertuigen en aanhangwagens",
        "theme": "conditions-techniques",
        "theme_ru": "Технические требования к транспортным средствам",
        "type": "Arrêté royal",
        "scope": "Belgique",
        "priority": 5,
        "notes": "Conditions techniques des voitures, camions, remorques",
    },
    "1985": {
        "slug": "1985014311~fcbcg8t4eq",
        "title_fr": "Loi du 21 juin 1985 — Conditions techniques des véhicules de transport",
        "title_nl": "Wet van 21 juni 1985 — Technische eisen voor voertuigen voor vervoer te land",
        "theme": "conditions-techniques",
        "theme_ru": "Технические требования к транспортным средствам",
        "type": "Loi",
        "scope": "Belgique",
        "priority": 5,
        "notes": "Loi-cadre sur les conditions techniques",
    },
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_law(law_id: str) -> dict:
    """
    Return metadata for the given law ID.

    Args:
        law_id: e.g. "1975", "1968", "2005"

    Returns:
        Law dict from LAWS registry.

    Raises:
        KeyError: if law_id is not in the registry.
    """
    if law_id not in LAWS:
        available = ", ".join(sorted(LAWS.keys()))
        raise KeyError(f"Unknown law ID {law_id!r}. Available: {available}")
    return LAWS[law_id]


def law_ids() -> list[str]:
    """Return all registered law IDs, sorted by priority then ID."""
    return sorted(LAWS.keys(), key=lambda k: (LAWS[k]["priority"], k))


def fr_url(law_id: str) -> str:
    """Return codedelaroute.be URL for this law."""
    slug = get_law(law_id)["slug"]
    return f"https://www.codedelaroute.be/fr/regelgeving/{slug}"


def nl_url(law_id: str) -> str:
    """Return wegcode.be URL for this law."""
    slug = get_law(law_id)["slug"]
    return f"https://www.wegcode.be/nl/regelgeving/{slug}"
