# data/archive — Données archivées PRAVA

> Ces dossiers sont conservés **en lecture seule** pour référence.
> **Ne pas modifier, ne pas utiliser dans le code.**

---

## Contenu

### `reglementation_v1/`
5 fichiers JSON thématiques avec l'**ancienne schema v1** (27-28 février 2026) :
- `01_dispositions_preliminaires.json` → `05_dispositions_finales.json`
- Schéma : `{theme, articles[{article_number, title, content_html, content_text}]}`
- Sans multi-langues (FR uniquement), sans definitions[], sans exam_questions[]
- Utilisés par : `apps/reglementation/management/commands/import_reglementation.py` (deprecated)
- Remplacés par : `data/processed/1975/articles/*.json` (nouvelle schema)

### `reglementation_db/`
Exemple unique `Art_65__art65_.json` avec la **nouvelle schema v2** (28 février 2026) :
- Premier article complet en FR/NL/RU avec definitions[], images[], _meta
- C'est l'ancêtre de `data/templates/article_template.json`

### `sites_old/`
Données brutes d'exploration initiale des 4 sites concurrents (27 février 2026) :
- `codedelaroute.be/` — scripts et output du scraper initial
- `permis24.be/` — analyse de l'API et structure du site
- `permisdeconduire-online.be/` — analyse des questions premium
- `readytoroad.be/` — analyse du contenu payant
- Ces analyses d'exploration ont conduit à la décision d'architecture actuelle.
- Les données utiles sont dans `data/sources/` et `data/laws/`.
