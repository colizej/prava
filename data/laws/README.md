# data/laws/ — Code de la route par version

Chaque sous-dossier correspond à une version du code de la route belge.

## Structure

```
laws/
├── 1975/    ← AR du 1er décembre 1975 (version ACTUELLE en production)
└── 2027/    ← Future version (placeholder — publication progressive)
```

## `1975/` — Version actuelle

| Fichier | Statut | Description |
|---------|--------|-------------|
| `fr_reglementation_raw.json` | ✅ Présent | Données brutes sérapées (ancienne structure) |
| `fr_reglementation.json` | 🔜 À créer | Output de `01_scrape.py` — schéma normalisé |
| `nl_reglementation.json` | 🔜 À créer | Output de `01_scrape.py` — NL scrappé |
| `ru_reglementation.json` | 🔜 À créer | Output de `02_translate.py` — traduction DeepL |

## `2027/` — Future version

Placeholder. Le nouveau code de la route belge entre en vigueur progressivement.

**Stratégie :**
1. Scraper dans `2027/` quand la version complète est disponible
2. Comparer automatiquement avec `1975/` (diff par article)
3. Publier les articles modifiés progressivement via l'admin dashboard
4. Config Django : `CURRENT_LAW_YEAR = "1975"` → `"2027"` une fois prêt

## Ne pas modifier les fichiers `_raw.json`
Ces fichiers sont les données brutes — toujours réutilisables comme source de secours.
