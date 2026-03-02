# scripts/archive — Anciens scripts PRAVA

> **NE PAS EXÉCUTER** — conservés uniquement pour référence lors de l'implémentation du nouveau pipeline.

## Contenu

### `scripts_old/` (35 scripts, phase d'exploration — 27 février 2026)
Scripts créés pendant la phase d'analyse initiale du projet. Valeur de référence :
- `scrape_themes.py` — sélecteurs CSS des thèmes sur codedelaroute.be
- `restructure_categories.py` — logique de transformation des catégories
- `analyze_html*.py` — structure HTML du site codedelaroute.be
- `import_exam_questions.py` — logique d'import en BDD (v1, non structurée)

### Scripts de la phase v1 (28 février 2026)
- `scrape_reglementation_universal.py` — skeleton du scraper universel FR+NL
- `universal_reglementation_parser.py` — parser HTML avancé (sélecteurs utiles)
- `parse_reglementation_article.py` — parsing d'un article individuel
- `crawl_reglementation_urls.py` — crawling des URLs d'articles

## Quand consulter ces scripts ?

Lors de l'implémentation de `scripts/pipeline/01_scrape.py` :
- Voir les sélecteurs CSS dans `universal_reglementation_parser.py`
- Voir la structure de parsing dans `scrape_reglementation_universal.py`
- La structure du site est documentée dans `scripts_old/analyze_html_deep.py`

## Ne PAS réutiliser directement
Ces scripts n'ont pas de structure uniforme, pas de gestion d'erreurs adaptée,
et ne suivent pas les schémas définis dans `docs/DATA_SCHEMA.md`.
