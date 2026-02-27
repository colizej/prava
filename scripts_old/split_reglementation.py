#!/usr/bin/env python3
"""Split code_de_la_route_complet.json into 5 themed JSON files (matching Titres I-V)."""
import json
import re
import os

INPUT = "data/sites/codedelaroute.be/output/code_de_la_route_complet.json"
OUTPUT_DIR = "data/reglementation"


def art_num(number_str):
    """Extract leading number from article number like '22bis.' -> 22"""
    m = re.match(r"(\d+)", str(number_str))
    return int(m.group(1)) if m else 0


THEMES = [
    {
        "filename": "01_dispositions_preliminaires.json",
        "theme": {
            "name": "Titre I. Dispositions préliminaires",
            "name_nl": "Titel I. Inleidende bepalingen",
            "name_ru": "Раздел I. Предварительные положения",
            "slug": "dispositions-preliminaires",
            "icon": "book-open",
            "description": "Champ d'application, définitions, agents qualifiés et force obligatoire de la signalisation.",
            "description_nl": "Toepassingsgebied, definities, bevoegde agenten en bindende kracht van de verkeerstekens.",
            "description_ru": "Область применения, определения, уполномоченные агенты и обязательная сила дорожной сигнализации.",
        },
        "range": (1, 6),
    },
    {
        "filename": "02_regles_usage_voie_publique.json",
        "theme": {
            "name": "Titre II. Règles d'usage de la voie publique",
            "name_nl": "Titel II. Regels voor het gebruik van de openbare weg",
            "name_ru": "Раздел II. Правила пользования дорогами",
            "slug": "regles-usage-voie-publique",
            "icon": "car",
            "description": "Conducteurs, vitesse, priorité, dépassement, stationnement, piétons, cyclistes et dispositions diverses.",
            "description_nl": "Bestuurders, snelheid, voorrang, inhalen, parkeren, voetgangers, fietsers en diverse bepalingen.",
            "description_ru": "Водители, скорость, приоритет, обгон, стоянка, пешеходы, велосипедисты и прочие положения.",
        },
        "range": (7, 59),
    },
    {
        "filename": "03_signalisation_routiere.json",
        "theme": {
            "name": "Titre III. Signalisation routière",
            "name_nl": "Titel III. Verkeerstekens",
            "name_ru": "Раздел III. Дорожная сигнализация",
            "slug": "signalisation-routiere",
            "icon": "alert-triangle",
            "description": "Signaux lumineux, signaux routiers, marques routières et dispositions diverses.",
            "description_nl": "Verkeerslichten, verkeersborden, wegmarkeringen en diverse bepalingen.",
            "description_ru": "Светофоры, дорожные знаки, дорожная разметка и прочие положения.",
        },
        "range": (60, 80),
    },
    {
        "filename": "04_prescriptions_techniques.json",
        "theme": {
            "name": "Titre IV. Prescriptions techniques",
            "name_nl": "Titel IV. Technische voorschriften",
            "name_ru": "Раздел IV. Технические предписания",
            "slug": "prescriptions-techniques",
            "icon": "settings",
            "description": "Conditions techniques pour véhicules à moteur, cycles, engins de déplacement et véhicules attelés.",
            "description_nl": "Technische voorwaarden voor motorvoertuigen, fietsen, voortbewegingstoestellen en bespannen voertuigen.",
            "description_ru": "Технические требования к автомобилям, велосипедам, средствам передвижения и гужевым транспортным средствам.",
        },
        "range": (81, 83),
    },
    {
        "filename": "05_dispositions_finales.json",
        "theme": {
            "name": "Titre V. Dispositions abrogatoires et transitoires",
            "name_nl": "Titel V. Opheffings- en overgangsbepalingen",
            "name_ru": "Раздел V. Отменяющие и переходные положения",
            "slug": "dispositions-finales",
            "icon": "file-text",
            "description": "Dispositions abrogatoires, transitoires et mise en vigueur.",
            "description_nl": "Opheffingsbepalingen, overgangsbepalingen en inwerkingtreding.",
            "description_ru": "Отменяющие положения, переходные положения и вступление в силу.",
        },
        "range": (84, 99),
    },
]


def main():
    with open(INPUT, encoding="utf-8") as f:
        data = json.load(f)

    articles = data["articles"]
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for t in THEMES:
        lo, hi = t["range"]
        theme_articles = []
        for i, art in enumerate(articles):
            n = art_num(art["number"])
            if lo <= n <= hi:
                theme_articles.append({
                    "article_number": f"Art. {art['number'].rstrip('.')}",
                    "title": art["title"],
                    "content_html": art["html"],
                    "content_text": art["full_text"],
                    "content_paragraphs": art["content"],
                    "source_id": art.get("id", ""),
                    "order": i + 1,
                })

        output = {
            "theme": t["theme"],
            "source": "codedelaroute.be — Arrêté royal du 1er décembre 1975",
            "articles_count": len(theme_articles),
            "articles": theme_articles,
        }

        path = os.path.join(OUTPUT_DIR, t["filename"])
        with open(path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"  ✅ {path}: {len(theme_articles)} articles")

    print("\nDone!")


if __name__ == "__main__":
    main()
