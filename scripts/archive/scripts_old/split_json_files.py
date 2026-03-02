"""
Split 3 JSON data files into 5 files matching the 5 Titres of the 1975 royal decree.
"""
import json
import os
from pathlib import Path

DATA_DIR = Path("data/reglementation")

TITRE_I_NUMS = {'Art. 1', 'Art. 2', 'Art. 3', 'Art. 4', 'Art. 5', 'Art. 6'}
TITRE_V_NUMS = {'Art. 84', 'Art. 85', 'Art. 86', 'Art. 87'}


def main():
    # ── Load existing files ──
    with open(DATA_DIR / "01_regles_circulation.json", "r", encoding="utf-8") as f:
        data_regles = json.load(f)
    with open(DATA_DIR / "02_signalisation.json", "r", encoding="utf-8") as f:
        data_signal = json.load(f)
    with open(DATA_DIR / "03_conditions_techniques.json", "r", encoding="utf-8") as f:
        data_tech = json.load(f)

    # ── Split 01_regles → Titre I + Titre II ──
    art_titre_i = [a for a in data_regles["articles"] if a["article_number"] in TITRE_I_NUMS]
    art_titre_ii = [a for a in data_regles["articles"] if a["article_number"] not in TITRE_I_NUMS]

    # ── Split 03_conditions → Titre IV + Titre V ──
    art_titre_iv = [a for a in data_tech["articles"] if a["article_number"] not in TITRE_V_NUMS]
    art_titre_v = [a for a in data_tech["articles"] if a["article_number"] in TITRE_V_NUMS]

    print(f"Titre I:   {len(art_titre_i)} articles (Art. {art_titre_i[0]['article_number']} .. {art_titre_i[-1]['article_number']})")
    print(f"Titre II:  {len(art_titre_ii)} articles (Art. {art_titre_ii[0]['article_number']} .. {art_titre_ii[-1]['article_number']})")
    print(f"Titre III: {len(data_signal['articles'])} articles (unchanged)")
    print(f"Titre IV:  {len(art_titre_iv)} articles (Art. {art_titre_iv[0]['article_number']} .. {art_titre_iv[-1]['article_number']})")
    print(f"Titre V:   {len(art_titre_v)} articles (Art. {art_titre_v[0]['article_number']} .. {art_titre_v[-1]['article_number']})")
    print()

    # ── Write new files ──
    files_to_write = {
        "01_dispositions_preliminaires.json": {
            "theme": {
                "name": "Titre I. Dispositions préliminaires",
                "name_nl": "Titel I. Inleidende bepalingen",
                "name_ru": "Раздел I. Предварительные положения",
                "slug": "dispositions-preliminaires",
                "icon": "book-open",
                "description": "Champ d'application, définitions, agents qualifiés et force obligatoire de la signalisation.",
                "description_nl": "Toepassingsgebied, definities, bevoegde agenten en bindende kracht van de verkeerstekens.",
                "description_ru": "Область применения, определения, уполномоченные агенты и обязательная сила дорожной сигнализации."
            },
            "articles": art_titre_i
        },
        "02_regles_usage_voie_publique.json": {
            "theme": {
                "name": "Titre II. Règles d'usage de la voie publique",
                "name_nl": "Titel II. Regels voor het gebruik van de openbare weg",
                "name_ru": "Раздел II. Правила пользования дорогами",
                "slug": "regles-usage-voie-publique",
                "icon": "car",
                "description": "Conducteurs, vitesse, priorité, dépassement, stationnement, piétons, cyclistes et dispositions diverses.",
                "description_nl": "Bestuurders, snelheid, voorrang, inhalen, parkeren, voetgangers, fietsers en diverse bepalingen.",
                "description_ru": "Водители, скорость, приоритет, обгон, стоянка, пешеходы, велосипедисты и прочие положения."
            },
            "articles": art_titre_ii
        },
        "03_signalisation_routiere.json": {
            "theme": {
                "name": "Titre III. Signalisation routière",
                "name_nl": "Titel III. Verkeerstekens",
                "name_ru": "Раздел III. Дорожная сигнализация",
                "slug": "signalisation-routiere",
                "icon": "alert-triangle",
                "description": "Signaux lumineux, signaux routiers, marques routières et dispositions diverses.",
                "description_nl": "Verkeerslichten, verkeersborden, wegmarkeringen en diverse bepalingen.",
                "description_ru": "Светофоры, дорожные знаки, дорожная разметка и прочие положения."
            },
            "articles": data_signal["articles"]
        },
        "04_prescriptions_techniques.json": {
            "theme": {
                "name": "Titre IV. Prescriptions techniques",
                "name_nl": "Titel IV. Technische voorschriften",
                "name_ru": "Раздел IV. Технические предписания",
                "slug": "prescriptions-techniques",
                "icon": "settings",
                "description": "Conditions techniques pour véhicules à moteur, cycles, engins de déplacement et véhicules attelés.",
                "description_nl": "Technische voorwaarden voor motorvoertuigen, fietsen, voortbewegingstoestellen en bespannen voertuigen.",
                "description_ru": "Технические требования к автомобилям, велосипедам, средствам передвижения и гужевым транспортным средствам."
            },
            "articles": art_titre_iv
        },
        "05_dispositions_finales.json": {
            "theme": {
                "name": "Titre V. Dispositions abrogatoires et transitoires",
                "name_nl": "Titel V. Opheffings- en overgangsbepalingen",
                "name_ru": "Раздел V. Отменяющие и переходные положения",
                "slug": "dispositions-finales",
                "icon": "file-text",
                "description": "Dispositions abrogatoires, transitoires et mise en vigueur.",
                "description_nl": "Opheffingsbepalingen, overgangsbepalingen en inwerkingtreding.",
                "description_ru": "Отменяющие положения, переходные положения и вступление в силу."
            },
            "articles": art_titre_v
        },
    }

    for fname, content in files_to_write.items():
        path = DATA_DIR / fname
        with open(path, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
        print(f"✓ Written: {fname} ({len(content['articles'])} articles)")

    # ── Archive old files ──
    archive_dir = DATA_DIR / "_archive"
    archive_dir.mkdir(exist_ok=True)
    for old_name in ["01_regles_circulation.json", "02_signalisation.json", "03_conditions_techniques.json"]:
        old_path = DATA_DIR / old_name
        if old_path.exists():
            old_path.rename(archive_dir / old_name)
            print(f"  📦 Archived: {old_name}")

    print("\n✅ Done! 5 JSON files ready for import.")


if __name__ == "__main__":
    main()
