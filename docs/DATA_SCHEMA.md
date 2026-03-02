# PRAVA — Schéma des données JSON

> Dernière mise à jour : 2 mars 2026
> Template de référence : `data/templates/article_template.json`
> Schéma JSON valide : `data/templates/schema.json`

---

## 1. Structure des dossiers

```
data/
├── laws/
│   ├── 1975/
│   │   ├── fr_reglementation_raw.json   ← Brut scrapé (input de 01_scrape.py)
│   │   ├── fr_reglementation.json       ← Nettoyé et structuré (output de 01_scrape.py)
│   │   ├── nl_reglementation.json       ← Scrapé NL
│   │   └── ru_reglementation.json       ← Traduit via DeepL
│   └── 2027/                            ← Future loi (placeholder)
│
├── processed/
│   ├── 1975/
│   │   ├── articles/                    ← Un fichier par article (output de 03_process.py)
│   │   │   ├── art001.json
│   │   │   ├── art002.json
│   │   │   └── ...
│   │   └── themes/                      ← Groupés par thème
│   │       ├── code_route.json
│   │       ├── permis.json
│   │       ├── assurance.json
│   │       └── amendes.json
│   └── questions/                       ← Questions générées (output de 04_questions.py)
│       ├── art001_questions.json
│       └── ...
│
├── sources/                             ← NE PAS MODIFIER — données brutes
│   ├── codedelaroute.be/
│   ├── wegcode.be/
│   └── competitors/
│
└── templates/                           ← Référence de schéma
    ├── article_template.json
    ├── schema.json
    └── INSTRUCTIONS.md
```

---

## 2. Schéma — Fichier complet `fr_reglementation.json`

```json
{
  "law_year": "1975",
  "language": "fr",
  "source_url": "https://www.codedelaroute.be/fr/perma/.../regulation",
  "scraped_at": "2026-03-02T00:00:00",
  "title": "Arrêté royal du 1er décembre 1975...",
  "total_articles": 100,
  "categories": [
    {
      "name": "Dispositions préliminaires",
      "slug": "dispositions-preliminaires",
      "order": 1
    }
  ],
  "articles": [
    {
      "number": "1.",
      "title": "Article 1. Champ d'application",
      "category_slug": "dispositions-preliminaires",
      "content_html": "<p>Le présent règlement...</p>",
      "content_text": "Le présent règlement...",
      "images": [],
      "order": 1
    }
  ]
}
```

---

## 3. Schéma — Article individuel `processed/1975/articles/art001.json`

```json
{
  "law_year": "1975",
  "article_number": "1.",
  "slug": "art-1-champ-application",
  "category": {
    "name_fr": "Dispositions préliminaires",
    "name_nl": "Inleidende bepalingen",
    "name_ru": "Предварительные положения",
    "slug": "dispositions-preliminaires",
    "order": 1
  },
  "title_fr": "Article 1. Champ d'application",
  "title_nl": "Artikel 1. Toepassingsgebied",
  "title_ru": "Статья 1. Сфера применения",
  "content_html_fr": "<p>Le présent règlement...</p>",
  "content_html_nl": "<p>Dit reglement...</p>",
  "content_html_ru": "<p>Настоящий регламент...</p>",
  "content_text_fr": "Le présent règlement...",
  "content_text_nl": "Dit reglement...",
  "content_text_ru": "Настоящий регламент...",
  "definitions": [
    {
      "id": "2.1",
      "term_fr": "chaussée",
      "term_nl": "rijbaan",
      "term_ru": "проезжая часть",
      "text_fr": "La partie de la voie publique...",
      "text_nl": "Het gedeelte van de openbare weg...",
      "text_ru": "Часть общественной дороги..."
    }
  ],
  "images": [
    {
      "sign_code": "F5",
      "alt_text_fr": "Signal F5 — Début d'autoroute",
      "alt_text_nl": "Signaal F5 — Begin autosnelweg",
      "alt_text_ru": "Знак F5 — Начало автострады",
      "source_url": "https://...",
      "order": 1
    }
  ],
  "seo": {
    "title_fr": "Article 1 Code de la route Belgique",
    "title_nl": "Artikel 1 Verkeersreglement België",
    "title_ru": "Статья 1 ПДД Бельгия",
    "description_fr": "...",
    "description_nl": "...",
    "description_ru": "...",
    "keywords_fr": ["code de la route", "article 1", "champ application"]
  },
  "_meta": {
    "source_type": "scrape",
    "source_url": "https://www.codedelaroute.be/...",
    "translated_by_ru": "deepl-free",
    "last_updated": "2026-03-02",
    "validation_status": "draft"
  }
}
```

---

## 4. Schéma — Questions `processed/questions/art001_questions.json`

```json
{
  "article_number": "1.",
  "article_slug": "art-1-champ-application",
  "generated_by": "gemini-1.5-flash",
  "generated_at": "2026-03-02T00:00:00",
  "questions": [
    {
      "id": "art001_q1",
      "type": "theoretical",
      "difficulty": 1,
      "text_fr": "Que désigne le terme 'chaussée' ?",
      "text_nl": "Wat bedoelt men met 'rijbaan' ?",
      "text_ru": "Что означает термин 'проезжая часть' ?",
      "image": {
        "sign_code": null,
        "generation_prompt": "Belgian road with lanes marked, top view, clean illustration"
      },
      "options": [
        {
          "letter": "A",
          "text_fr": "La partie réservée aux piétons",
          "text_nl": "Het gedeelte voor voetgangers",
          "text_ru": "Часть, предназначенная для пешеходов",
          "is_correct": false
        },
        {
          "letter": "B",
          "text_fr": "La partie aménagée pour la circulation des véhicules",
          "text_nl": "Het gedeelte ingericht voor het rijverkeer",
          "text_ru": "Часть, предназначенная для движения транспортных средств",
          "is_correct": true
        },
        {
          "letter": "C",
          "text_fr": "L'ensemble de la voie publique",
          "text_nl": "De gehele openbare weg",
          "text_ru": "Вся общественная дорога",
          "is_correct": false
        }
      ],
      "explanation_fr": "Selon l'article 2.1, la chaussée désigne...",
      "explanation_nl": "Volgens artikel 2.1 is de rijbaan...",
      "explanation_ru": "Согласно статье 2.1, проезжая часть — это...",
      "validation_status": "draft"
    }
  ]
}
```

---

## 5. Règles de validation

1. Tous les champs présents dans le schéma doivent exister (même vides `""` ou `[]`)
2. `slug` : uniquement lettres minuscules, chiffres, tirets
3. `validation_status` : `draft` → `reviewed` → `approved` (progression obligatoire)
4. Les questions passent en `reviewed` après vérification manuelle dans l'admin
5. Seuls les articles `approved` sont importés en BDD par `05_import.py`
