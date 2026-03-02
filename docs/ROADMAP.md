# PRAVA — Roadmap de développement

> Dernière mise à jour : 2 mars 2026

---

## Légende statut

| Symbole | Signification |
|---------|---------------|
| ✅ | Terminé |
| 🔄 | En cours |
| 🔜 | Prochain |
| ⬜ | Planifié |
| 🔒 | Bloqué / dépend d'une autre tâche |

---

## Phase 0 — Architecture & Nettoyage ✅

> Durée : 1-2 jours | **Terminée : 2 mars 2026**

- [x] Audit complet du code existant (scripts, data, docs)
- [x] Nouvelle structure de dossiers (`data/laws/`, `data/processed/`, `data/sources/`)
- [x] Archivage des anciens scripts (`scripts/archive/`)
- [x] Archivage de l'ancienne documentation (`docs/archive/`)
- [x] Création de la documentation vivante (README, ARCHITECTURE, ROADMAP, DATA_SCHEMA, SCRIPTS)
- [x] Création de la structure `scripts/pipeline/` et `scripts/utils/`

---

## Phase 1 — Scraping FR + NL 🔜

> Durée estimée : 3-5 jours

### Scripts à implémenter
- [ ] `scripts/pipeline/01_scrape.py` — scraper FR (codedelaroute.be) + NL (wegcode.be)
  - [ ] Scraper le code de la route principal (Titres I–V, ~100 articles)
  - [ ] Scraper les thèmes complémentaires (permis, assurance, amendes)
  - [ ] Sauvegarder → `data/laws/1975/fr_reglementation.json` et `nl_reglementation.json`
  - [ ] Détection de diff au 2ème lancement (afficher les changements)
- [ ] `scripts/utils/http_client.py` — client HTTP avec retry, rate limiting
- [ ] `scripts/utils/diff_checker.py` — comparaison JSON (détection modifications)

### Thèmes à scraper sur codedelaroute.be / wegcode.be
- [ ] Code de la route (Titres I–V) — déjà disponible dans `data/laws/1975/fr_reglementation_raw.json`
- [ ] Permis de conduire
- [ ] Assurance
- [ ] Infractions & amendes (Code pénal de la route)

### Données de sortie
```
data/laws/1975/
├── fr_reglementation.json     # Version nettoyée et structurée
├── fr_reglementation_raw.json # Brut scrapé (déjà présent)
└── nl_reglementation.json     # À créer
```

---

## Phase 2 — Traduction RU 🔒

> Durée estimée : 1-2 jours | Dépend de Phase 1

- [ ] `scripts/pipeline/02_translate.py`
  - [ ] Connexion DeepL Free API (clé dans `.env`)
  - [ ] Traduction FR → RU article par article
  - [ ] Gestion du quota (500k car/mois) — traduction progressive
  - [ ] Sauvegarde → `data/laws/1975/ru_reglementation.json`
- [ ] `scripts/utils/deepl_client.py` — client DeepL avec gestion quota

### Stratégie quota DeepL Free
- ~100 articles × ~3 000 car. = ~300 000 car. pour le code de la route
- Budget restant (~200k) pour thèmes complémentaires et questions
- Si quota dépassé : mise en file d'attente, reprise le mois suivant

---

## Phase 3 — Traitement & Découpage 🔒

> Durée estimée : 2-3 jours | Dépend de Phase 1

- [ ] `scripts/pipeline/03_process.py`
  - [ ] Découper le JSON complet en fichiers par article (`data/processed/1975/articles/`)
  - [ ] Grouper par thème (`data/processed/1975/themes/`)
  - [ ] Extraire les définitions et termes clés
  - [ ] Extraire les codes de panneaux (signes) pour liaison avec `TrafficSign`
- [ ] `scripts/utils/json_helpers.py` — utilitaires de transformation JSON

---

## Phase 4 — Génération de questions 🔒

> Durée estimée : 3-5 jours | Dépend de Phase 3

- [ ] `scripts/pipeline/04_questions.py`
  - [ ] Connexion Gemini 1.5 Flash API (clé dans `.env`)
  - [ ] Générer 5 questions par article/définition :
    - 2 questions théoriques ("Que signifie... ?")
    - 3 questions pratiques (application du règle dans un scénario)
  - [ ] Pour chaque question : texte (FR/NL/RU), 3 options (A/B/C), explication, prompt image
  - [ ] Sauvegarder → `data/processed/questions/` (un JSON par article)
  - [ ] Mode révision : régénérer seulement les questions manquantes
- [ ] `scripts/utils/gemini_client.py` — client Gemini avec rate limiting

### Stratégie Gemini Free
- 15 req/min, 1M tokens/jour sur tier gratuit
- ~100 articles × 1 requête = ~100 requêtes (~7 min à 15 req/min)
- Résultat stocké en JSON → révision manuelle dans l'admin avant import

---

## Phase 5 — Import en base de données 🔒

> Durée estimée : 2-3 jours | Dépend de Phase 3 + 4

- [ ] `scripts/pipeline/05_import.py`
  - [ ] Importer `RuleCategory`, `CodeArticle`, `TrafficSign` (from `data/processed/`)
  - [ ] Importer les questions (`ExamQuestion`, `QuestionOption`)
  - [ ] Gestion des doublons (update si slug existe, créer sinon)
  - [ ] Rapport d'import (nb créés, mis à jour, erreurs)
- [ ] Management command Django : `manage.py import_laws`

---

## Phase 6 — Admin Dashboard 🔒

> Durée estimée : 3-5 jours | Dépend de Phase 5

- [ ] Vue admin custom `PravaDashboard` (accès superuser uniquement)
- [ ] 4 boutons-pipelines avec feedback en temps réel (HTMX + SSE ou polling)
  1. **Scraper FR + NL** → déclenche `01_scrape.py`
  2. **Traduire en RU** → déclenche `02_translate.py`
  3. **Générer questions** → déclenche `03_process.py` + `04_questions.py`
  4. **Importer en BDD** → déclenche `05_import.py`
- [ ] Interface de révision des questions (liste + édition inline)
- [ ] Affichage des diffs au re-scraping

---

## Phase 7 — Frontend utilisateur 🔒

> Durée estimée : 5-7 jours | Dépend de Phase 5

- [ ] Page liste des thèmes (`/reglementation/`)
- [ ] Page article (`/reglementation/{slug}/`)
- [ ] Page examen (`/examen/`)
- [ ] Système de badges quotidiens (1 badge = 1 connexion)
- [ ] Règle freemium :
  - Illimité : lecture des règles
  - Limité gratuit : N tests de base par jour (badge)
  - Premium : simulations illimitées, examen complet 50 questions

---

## Phase 8 — SEO & Publication 2027 ⬜

> Durée estimée : ongoing

- [ ] Sitemap XML (articles, thèmes)
- [ ] Meta tags dynamiques (Open Graph, Schema.org)
- [ ] Rédaction articles blog (aide à l'indexation)
- [ ] Préparation contenu loi 2027 (publication progressive)
- [ ] Traductions RU restantes (au fur et à mesure du quota DeepL)

---

## Vue d'ensemble du calendrier

```
Mars 2026    : Phase 0 ✅ + Phase 1 🔄 (scraping FR/NL)
Avril 2026   : Phase 2 (traduction RU) + Phase 3 (traitement)
Mai 2026     : Phase 4 (questions) + Phase 5 (import BDD)
Juin 2026    : Phase 6 (admin dashboard)
Juil. 2026   : Phase 7 (frontend utilisateur) + lancement beta
Août+ 2026   : Phase 8 (SEO, contenu 2027 progressif)
```
