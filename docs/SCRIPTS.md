# PRAVA — Documentation des scripts

> Dernière mise à jour : 2 mars 2026

---

## Structure

```
scripts/
├── pipeline/          ← Scripts exécutables du pipeline principal
│   ├── 01_scrape.py
│   ├── 02_translate.py
│   ├── 03_process.py
│   ├── 04_questions.py
│   └── 05_import.py
├── utils/             ← Utilitaires partagés (importés par le pipeline)
│   ├── __init__.py
│   ├── http_client.py
│   ├── json_helpers.py
│   ├── deepl_client.py
│   └── gemini_client.py
└── archive/           ← Anciens scripts (NE PAS EXÉCUTER — référence uniquement)
    ├── scripts_old/   ← 35 scripts d'exploration initiale
    └── *.py           ← Scripts de la v1 du projet
```

---

## Règles générales

1. **Numérotation** : les scripts pipeline sont toujours exécutés dans l'ordre (01→05)
2. **Idempotence** : chaque script peut être relancé sans risque — il détecte les diffs et ne recrée pas ce qui existe déjà
3. **Logs** : chaque script écrit dans `data/logs/{script_name}_{date}.log`
4. **Config** : toutes les clés API sont lues depuis `.env` (jamais en dur dans le code)
5. **Dry-run** : chaque script supporte `--dry-run` pour simuler sans écrire

---

## 01_scrape.py — Scraping FR + NL

**Statut :** 🔜 À implémenter (Phase 1)

**Usage :**
```bash
python scripts/pipeline/01_scrape.py [--lang fr|nl|both] [--dry-run]
```

**Ce que ça fait :**
- Parcourt `codedelaroute.be` (FR) et `wegcode.be` (NL)
- Scrape le code de la route + thèmes complémentaires (permis, assurance, amendes)
- Sauvegarde dans `data/laws/1975/fr_reglementation.json` et `nl_reglementation.json`
- Si le fichier existe déjà → calcule le diff et affiche les changements

**Output :**
```
data/laws/1975/fr_reglementation.json
data/laws/1975/nl_reglementation.json
```

---

## 02_translate.py — Traduction FR → RU (DeepL)

**Statut :** 🔒 Bloqué — dépend de 01_scrape.py

**Usage :**
```bash
python scripts/pipeline/02_translate.py [--quota-check] [--dry-run]
```

**Ce que ça fait :**
- Lit `fr_reglementation.json`
- Traduit les champs texte via DeepL Free API (500k car/mois)
- Sauvegarde dans `data/laws/1975/ru_reglementation.json`
- Gère le quota : s'arrête si quota proche, note la position pour reprendre

**Clé requise :** `DEEPL_API_KEY` dans `.env`

---

## 03_process.py — Découpage en articles

**Statut :** 🔒 Bloqué — dépend de 01_scrape.py

**Usage :**
```bash
python scripts/pipeline/03_process.py [--law-year 1975] [--dry-run]
```

**Ce que ça fait :**
- Lit les 3 fichiers complets (fr/nl/ru)
- Fusionne par article dans `data/processed/1975/articles/art{NNN}.json`
- Groupe par thème dans `data/processed/1975/themes/`
- Valide contre `data/templates/schema.json`

---

## 04_questions.py — Génération de questions (Gemini)

**Statut :** 🔒 Bloqué — dépend de 03_process.py

**Usage :**
```bash
python scripts/pipeline/04_questions.py [--article art001] [--regenerate] [--dry-run]
```

**Ce que ça fait :**
- Lit les articles dans `data/processed/1975/articles/`
- Pour chaque article, appelle Gemini 1.5 Flash pour générer 5 questions (2 théo. + 3 pratiques)
- Sauvegarde dans `data/processed/questions/art{NNN}_questions.json`
- Respecte le rate limit (15 req/min) — pause automatique

**Clé requise :** `GEMINI_API_KEY` dans `.env`

**Prompt système utilisé :**
```
Tu es un expert du code de la route belge. À partir de l'article suivant,
génère exactement 5 questions d'examen : 2 théoriques et 3 pratiques.
Format JSON strict (voir DATA_SCHEMA.md §4).
Langues : FR, NL, RU pour toutes les questions et options.
```

---

## 05_import.py — Import en base de données

**Statut :** 🔒 Bloqué — dépend de 03_process.py + 04_questions.py

**Usage :**
```bash
python scripts/pipeline/05_import.py [--law-year 1975] [--status approved] [--dry-run]
```

**Ce que ça fait :**
- Lit les articles validés (`validation_status: approved`) depuis `data/processed/`
- Crée/met à jour `RuleCategory`, `CodeArticle`, `TrafficSign` en BDD
- Crée/met à jour `ExamQuestion`, `QuestionOption`
- Si `--status reviewed` : importe aussi les questions en statut `reviewed` (pour test admin)
- Génère un rapport : `{N} créés, {M} mis à jour, {E} erreurs`

---

## utils/http_client.py

Client HTTP partagé avec :
- User-Agent approprié
- Retry automatique (3x avec backoff)
- Rate limiting configurable (délai entre requêtes)
- Session persistante

---

## utils/deepl_client.py

Client DeepL Free API :
- Lecture de `DEEPL_API_KEY` depuis `.env`
- Méthode `translate(text, source="FR", target="RU")`
- Vérification quota avant chaque requête (`/v2/usage`)
- Si quota < 10% : warning et arrêt gracieux

---

## utils/gemini_client.py

Client Gemini 1.5 Flash :
- Lecture de `GEMINI_API_KEY` depuis `.env`
- Prompt système configurable
- Rate limiting : 15 req/min (pause automatique)
- Parsing de la réponse JSON

---

## utils/json_helpers.py

Fonctions utilitaires :
- `load_json(path)` — charge avec gestion d'erreur
- `save_json(data, path)` — sauvegarde avec indentation
- `diff_json(old, new)` — compare deux JSONs, retourne les différences
- `validate_against_schema(data, schema_path)` — validation JSON Schema

---

## archive/ — Anciens scripts

> **NE PAS EXÉCUTER** — conservés uniquement pour référence

| Dossier/Fichier | Origine | Utilité pour référence |
|-----------------|---------|----------------------|
| `scripts_old/analyze_html*.py` | Exploration HTML initiale | Structure du site codedelaroute.be |
| `scripts_old/scrape_themes.py` | V1 du scraper | Sélecteurs CSS des thèmes |
| `scripts_old/restructure_*.py` | Réorganisation données | Logique de transformation |
| `scrape_reglementation_universal.py` | V2 du scraper | Skeleton plus avancé |
| `universal_reglementation_parser.py` | Parser avancé | Logique de parsing HTML |
| `import_exam_questions.py` | Import V1 | Logique d'import BDD |
