# PRAVA — Roadmap de développement

> Dernière mise à jour : 4 mars 2026 (soir)

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

## Phase 1 — Scraping FR + NL ✅

> **Terminée : 2 mars 2026**

- [x] `scripts/pipeline/01_scrape.py` — scraper FR (codedelaroute.be) + NL (wegcode.be)
  - [x] Scraper AR 1975 — code de la route principal (122 articles)
  - [x] Sauvegarder → `data/laws/1975/fr_reglementation.json` et `nl_reglementation.json`
  - [x] Détection de diff au 2ème lancement
- [x] `scripts/utils/http_client.py` — client HTTP avec retry, rate limiting

---

## Phase 2 — Traduction RU ✅

> **Terminée : 2 mars 2026**

- [x] `scripts/pipeline/02_translate.py` — traduction FR → RU via DeepL Free API
- [x] `scripts/utils/deepl_client.py` — client DeepL avec gestion quota
- [x] `data/laws/1975/ru_reglementation.json` — 122 articles traduits

---

## Phase 3 — Traitement & Découpage ✅

> **Terminée : 3 mars 2026**

- [x] `scripts/pipeline/03_process.py` — découpage en fichiers par article
- [x] `data/processed/1975/articles/` — 122 fichiers `art-{slug}.json`
- [x] `scripts/utils/json_helpers.py` — utilitaires JSON

---

## Phase 4 — Génération de questions ✅ / 🔄

> **En cours : 3–4 mars 2026** (limité par quota Gemini Free 500 RPD)

- [x] `scripts/pipeline/04_questions.py` — génération via Gemini 2.5 Flash Lite
- [x] `scripts/utils/gemini_client.py` — client Gemini avec rate limiting (10 RPM)
- [x] Format : 5 questions/article × 3 langues (FR/NL/RU), 3 options A/B/C, explication
- [x] 85 / 122 articles traités (au 4 mars 2026, 12h)
- [ ] 37 articles restants — reprendre le **5 mars 2026**
  - Art 59-1, 6, 61–70, 7, 70–82, 8–9… (articles non-séquentiels)
  - Note : Art 62, 62bis, 62ter pris en compte mais réponse vide (limite atteinte milieu de script)

### Quota Gemini Free (gemini-2.5-flash-lite)
- Limite : **20 requêtes/jour** (pas 500 — limite plus stricte observée)
- **Reprise : 5 mars 2026 matin** — `python3 scripts/pipeline/04_questions.py --law 1975`

---

## Phase 5 — Import en base de données ⬜

> Dépend de Phase 4 (complétion questions AR 1975)

- [ ] `scripts/pipeline/05_import.py`
  - [ ] Importer `RuleCategory`, `CodeArticle` (from `data/processed/1975/`)
  - [ ] Importer les questions (`ExamQuestion`, `QuestionOption`)
  - [ ] Gestion des doublons (update si slug existe, créer sinon)
  - [ ] Rapport d'import (nb créés, mis à jour, erreurs)
- [ ] Management command Django : `manage.py import_laws`

---

## Phase 5b — Lois complémentaires �

> **En cours depuis le 4 mars 2026** | Durée estimée : 5–7 jours restants

L'AR 1975 (règles de circulation) ne couvre qu'une partie du programme d'examen belge.
Pour une préparation complète, il faut scraper, traduire et générer des questions
pour les autres lois principales accessibles sur codedelaroute.be / wegcode.be.

### Lois prioritaires (catégorie B)

| Priorité | Loi | Thème site | Slug FR | Slug NL | Dossier |
|----------|-----|-----------|---------|---------|---------|
| ⭐⭐⭐ | Loi 16 mars 1968 — police de la circulation | Politique criminelle | `1968031601~invynqx4tj` | idem | `data/laws/1968/` |
| ⭐⭐⭐ | AR 30 sept. 2005 — infractions par degré (1–4) | Politique criminelle | `2005014182~5yjza0ajqn` | idem | `data/laws/2005/` |
| ⭐⭐⭐ | AR 23 mars 1998 — permis de conduire | Permis de conduire | `1998014078~w8ylf1lyws` | idem | `data/laws/1998/` |
| ⭐⭐⭐ | AR 10 juillet 2006 — permis catégorie B | Permis de conduire | `2006014162~khugwmgcip` | idem | `data/laws/2006/` |
| ⭐⭐ | AM 11 oct. 1976 — signalisation routière (dimensions) | Infrastructure | `1976101105~j6siwtihko` | idem | `data/laws/1976/` |
| ⭐⭐ | AM 1 déc. 1975 — caractéristiques disques/plaques | Infrastructure | `1975120125~q1rrr4iaw7` | idem | `data/laws/1975b/` |
| ⭐ | AR 15 mars 1968 — conditions techniques véhicules | Conditions techniques | `1968031501~fhniyzocos` | idem | `data/laws/1968b/` |
| ⭐ | Loi 21 juin 1985 — conditions techniques | Conditions techniques | `1985014311~fcbcg8t4eq` | idem | `data/laws/1985/` |

### Lois non prioritaires (hors cat. B standard)
- Transport de marchandises, Transport de personnes, Aptitude professionnelle
  → à ajouter ultérieurement si extension vers cat. C/D

### Implémentation réalisée le 4 mars 2026

- [x] `scripts/utils/laws_registry.py` — registre central de toutes les lois belges
- [x] `01_scrape.py --law <id>` + `--list-laws` + fallback parser (`<p>Art. N.` sans `<h5>`)
- [x] `02_translate.py --law <id>` — translate dynamique par loi
- [x] `03_process.py --law <id>` — `law_id` passé en paramètre (plus de `LAW_YEAR` hardcodé)
- [x] `04_questions.py --law <id>` — prêt, non testé sur nouvelles lois

**Pipeline complet par loi :**
```bash
python3 scripts/pipeline/01_scrape.py --law 1968
python3 scripts/pipeline/02_translate.py --law 1968
python3 scripts/pipeline/03_process.py --law 1968
python3 scripts/pipeline/04_questions.py --law 1968
python3 scripts/pipeline/05_import.py --law 1968  # à mettre à jour
```

### Quota DeepL Free — plan de rotation

> **Situation 4 mars 2026** : quota du compte principal épuisé (~37K restants sur 500K/mois)

| Besoin | Loi | Chars estimés |
|--------|-----|---------------|
| ✅ Fait | 1968 (93 art.) | ~144K |
| ✅ Fait | 2005 (8 art.) | ~3.5K |
| 🔜 Prochain | 1976 (23 art.) | ~151K |
| 🔜 | 2006 (60 art.) | ~60K |
| 🔜 | 1998 (156 art.) | ~250K |
| **Total restant** | | **~461K** |

**Plan : rotation de 4 comptes DeepL Free** (4 × 500K = 2M chars disponibles)
- Changer la clé `DEEPL_API_KEY` dans `.env` à chaque épuisement
- Ordre recommandé : compte 2 → 1976 + 2006, compte 3 → 1998, comptes 4+ en réserve
- **Abonnement payant non nécessaire** : 4 comptes gratuits couvrent amplement les ~461K chars restants

```bash
# Changer de compte dans .env :
DEEPL_API_KEY=xxxxx-nouveau-compte
# Puis reprendre :
python3 scripts/pipeline/02_translate.py --law 1976
```

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
2 mars 2026   : Phase 0 ✅  Phase 1 ✅  Phase 2 ✅  Phase 3 ✅
3-4 mars 2026 : Phase 4 🔄  AR 1975 questions : 85/122 (Gemini limite/jour)
4 mars 2026   : Phase 5b 🔄 Pipeline multi-loi implémenté, 1968+2005 complets,
               1998+2006+1976 scrapés, DeepL quota épuisé → rotation de compte
5 mars 2026   : Phase 4 🔜  Reprendre AR 1975 (37 restants) + 1968+2005 questions
               Phase 5b     Traduire 1976+2006+1998 (nouveau compte DeepL)
6-10 mars     : Phase 5 🔜  Import AR 1975 + 1968 + 2005 en BDD
Mars–Avril    : Phase 6     Admin dashboard
Avril–Mai     : Phase 7     Frontend utilisateur + lancement beta
Mai+          : Phase 8     SEO, contenu 2027 progressif
```
