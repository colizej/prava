# PRAVA — Roadmap de développement

> Dernière mise à jour : 5 mars 2026 (soir — Phase 7 terminée, email confirmation, HTTPS prod)

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

## Phase 4 — Génération de questions 🔄

> **En cours : 3–5 mars 2026** (limité par quota Gemini Free)

- [x] `scripts/pipeline/04_questions.py` — génération avec flag `--law`, `--article`, `--limit`, `--regenerate`
- [x] `scripts/utils/gemini_client.py` — client Gemini avec rate limiting
- [x] Format : 3 théoriques + 5 pratiques × 3 langues (FR/NL/RU), 3 options A/B/C, explication
- [x] Prompt amélioré le 5 mars 2026 :
  - JAMAIS de référence à un article/loi dans les questions
  - Accent sur les définitions, noms officiels, situations concrètes
  - Questions réparties sur les sous-points (6.1, 6.2, 6.3.1…)
  - Articles trop courts → minimum 3 questions
- [x] `build_prompt()` : cap FR 8000 chars (était 3000) — couvre les grands articles avec 50+ sous-points
- [x] **Modèle migré vers `gemini-2.5-flash`** (5 mars) — `gemini-2.5-flash-lite` quota épuisé (20 req/jour)
  - `thinking_budget=0` configuré — désactive le mode "thinking" (vitesse ×4 ~12s vs 56s)
- [x] `scripts/run_questions.sh` — script de lancement de toute la chaîne
- [x] **107 / 593 articles traités** (18 % — au 5 mars 2026 soir)
  - 1975 : 102/122, 1968 : 3/93, 2006 : 1/51, 1968b : 1/101
- [ ] ~486 articles restants — reprendre le **6 mars 2026**
  ```bash
  nohup bash scripts/run_questions.sh > logs/questions_$(date +%Y%m%d).log 2>&1 &
  ```

### Quota Gemini Free
- `gemini-2.5-flash-lite` : **20 req/jour** (épuisé le 5 mars)
- `gemini-2.5-flash` : quota disponible, ~10–15 RPM free tier
- `gemini-2.0-flash` et `gemini-2.0-flash-lite` : quota `limit: 0` sur ce projet (bloqués)

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

## Phase 5b — Lois complémentaires ✅

> **Terminée : 5 mars 2026** | Pipeline complet pour 10 lois

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

### Implémentation réalisée (4–5 mars 2026)

- [x] `scripts/utils/laws_registry.py` — registre central de toutes les lois (ajout 1989, 2001 le 5 mars)
- [x] `01_scrape.py --law <id>` + `--list-laws` + fallback parser
- [x] `02_translate.py --law <id>` — traduction dynamique par loi
- [x] `03_process.py --law <id>` — `slugify_number()` corrigé le 5 mars :
  - Problème : slugs avec espaces/accents/points (`1998-art-i. cette annexe…`) → `NoReverseMatch`
  - Fix : `unicodedata.normalize("NFKD")` + regex `[^a-z0-9-]` → slugs propres
  - 17 lignes DB réparées + 17 fichiers JSON mis à jour
- [x] `04_questions.py --law <id>` — fonctionnel sur toutes les lois
- [x] `05_import.py --law <id>` — `_LAW_DEFAULT_EXAM_SLUG` étendu à 1989 et 2001
- [x] `apps/reglementation/views.py` — `_LAW_META` couvre les 9 lois non-1975 avec titres/couleurs
- [x] Templates `/reglementation/` connectés à toutes les lois (index + category sidebar)

**Pipeline complet par loi :**
```bash
python3 scripts/pipeline/01_scrape.py --law 1989
python3 scripts/pipeline/02_translate.py --law 1989
python3 scripts/pipeline/03_process.py --law 1989
python3 scripts/pipeline/04_questions.py --law 1989
python3 scripts/pipeline/05_import.py --law 1989
```

### Quota DeepL Free — plan de rotation

> **Situation 5 mars 2026** : toutes les lois traduites — quota utilisé sur plusieurs comptes

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

## Phase 7 — Frontend utilisateur ✅

> **Terminée : 5 mars 2026**

- [x] Page d'accueil — hero, stats bar 4 colonnes, section "Pourquoi PRAVA?" avant catégories
- [x] Barre stats enrichie : icônes, descriptions, +50, FR·NL·RU
- [x] Page tarifs (`/shop/`) avec plans + mention ⛽ carburant gratuit
- [x] Page profil — carte portefeuille ⛽, tests récents avec badge score (vert/rouge)
- [x] Page historique tests (`/examens/history/`) — design amélioré
- [x] Navbar desktop : widget ⛽ interactif avec jauge animée et échange
- [x] Navbar mobile : widget ⛽ lecture seule (balance + barre de remplissage)
- [x] Système de réservoir ⛽ complet (`apps/rewards/`) :
  - Heartbeat toutes les 60s (accumulation carburant en ligne)
  - Échange : 20L→+10q, 40L→+30q, 60L→+50q
  - `KeySettings` singleton, `KeyWallet` par user, `KeyTransaction` journal
  - Admin panel complet
- [x] Email confirmation achat (Mailjet, déclenché par `_activate_premium()`)
- [x] Sécurité HTTPS production : `SECURE_SSL_REDIRECT`, HSTS 1 an, cookies sécurisés
- [x] i18n : corrections .po ru + nl, 4 nouvelles chaînes ⛽ par langue
- [x] Tailwind CSS dividers : `divide-gray-100` (était noir par défaut)

---

## Phase 7b — Intégration Mollie ✅

> **Terminée : 5 mars 2026**

- [x] Checkout → Mollie → webhook → `_activate_premium()`
- [x] Email confirmation achat (plan, montant, date expiration, bonus ⛽)
- [x] Dev fallback sans Mollie (simulation paiement en DEBUG)
- [x] Ordre `Status` : pending → paid / failed / expired / canceled

---

- [x] Page liste des thèmes (`/reglementation/`) — **terminée le 5 mars 2026**
  - Grille principale AR 1975, section "Textes législatifs de référence" avec cartes colorées par thème
  - Thèmes connectés : Politique criminelle (1968), Permis (1998), Assurance (1989), Conditions techniques (1968b)
- [x] Page catégorie (`/reglementation/category/<slug>/`) — sidebar filtrée par loi
- [ ] Page article individuel (`/reglementation/{slug}/`)
- [ ] Page examen (`/examen/`)
- [ ] Système de badges quotidiens → remplacé par système ⛽ carburant (Phase 7)
- [x] Règle freemium :
  - Illimité : lecture des règles
  - Gratuit : 15 questions/jour (`FREE_DAILY_QUESTIONS`)
  - Premium : accès illimité via abonnement (Mollie)
  - Bonus ⛽ : échange litres contre questions supplémentaires

---

## Phase 8 — SEO & Publication 2027 ⬜

> Durée estimée : ongoing

- [ ] Sitemap XML (articles, thèmes)
- [ ] Meta tags dynamiques (Open Graph, Schema.org)
- [ ] Rédaction articles blog (aide à l'indexation)
- [ ] Préparation contenu loi 2027 (publication progressive)
- [ ] Traductions RU restantes (au fur et à mesure du quota DeepL)

---

## Phase 9 — Internationalisation complète (i18n) FR/NL/RU ⬜

> Durée estimée : 1–2 semaines | Dépend de Phase 7 | **Variante choisie : B (Full Django i18n)**

### Contexte — État actuel (4 mars 2026)

| Élément | État |
|---------|------|
| `USE_I18N = True` + `LocaleMiddleware` | ✅ Configuré |
| 3 langues déclarées : fr, nl, ru | ✅ Configuré |
| Champ `User.language` (préférence utilisateur) | ✅ Existant |
| `{% trans %}` dans templates | ⚠️ Partiellement ajouté |
| Fichiers `.po` / `.mo` dans `locale/` | ❌ Vides — aucune traduction |
| Switcher de langue dans navbar | ❌ Absent |
| URL `set_language` | ❌ Non déclaré |
| Contenu traduit affiché (articles, signes) | ❌ Non connecté aux templates |

### Niveau 1 — Interface utilisateur (UI strings)

- [ ] Auditer tous les templates — ajouter les `{% trans %}` manquants
  - `templates/base.html`, `templates/includes/navbar.html`, `templates/includes/footer.html`
  - `apps/main/templates/main/` — home, pricing, contact, glossary
  - `apps/accounts/templates/accounts/` — login, register, profile
  - `apps/examens/templates/examens/` — quiz, results, categories, history
  - `apps/reglementation/templates/reglementation/` — index, article, signs, category
  - `apps/blog/templates/blog/` — list, detail, search
- [ ] `python manage.py makemessages -l ru -l nl` — générer les `.po`
- [ ] Remplir `locale/ru/LC_MESSAGES/django.po` (~200–300 chaînes UI)
- [ ] Remplir `locale/nl/LC_MESSAGES/django.po` (~200–300 chaînes UI)
- [ ] `python manage.py compilemessages` — compiler les `.mo`
- [ ] Switcher de langue dans la navbar (cookie + `set_language` Django)
- [ ] Brancher `User.language` → appliquer automatiquement à la connexion

### Niveau 2 — Contenu (données en BDD)

- [ ] **Articles de loi** — templates `article.html` affichent `content_md_fr` / `content_md_nl` / `content_md_ru` selon langue active
- [ ] **Signes routiers** — `signs.html` affiche `name` (FR) / `name_nl` / `name_ru` selon langue (ajouter champs au modèle si nécessaire)
- [ ] **Questions d'examen** — déjà sur 3 langues dans les données, vérifier rendu dans `quiz.html`
- [ ] **Options de réponse** — `text` / `text_nl` / `text_ru` selon langue active
- [ ] **Titres et slugs** — gérer les URLs multilingues (slug FR reste canonique)

### Niveau 3 — Emails et messages système

- [ ] `accounts/` — emails d'inscription/confirmation traduits
- [ ] Messages flash Django (`messages.success/error`) avec `{% trans %}`
- [ ] Formulaires — labels et messages d'erreur traduits

### Niveau 4 (optionnel) — URLs préfixées par langue

> Non prioritaire, peut être fait en Phase 8b

- [ ] `i18n_patterns()` dans `config/urls.py` → URLs `/fr/`, `/nl/`, `/ru/`
- [ ] Avantage SEO : pages indexées séparément par langue
- [ ] Redirection par défaut selon langue du navigateur

### Dépendances techniques

```bash
# Workflow i18n complet :
python manage.py makemessages -l ru -l nl -l fr  # extraire les chaînes
# → éditer locale/ru/LC_MESSAGES/django.po
# → éditer locale/nl/LC_MESSAGES/django.po
python manage.py compilemessages                  # compiler
# Ajouter dans config/urls.py :
# path('i18n/', include('django.conf.urls.i18n')),  # pour set_language
```

---

## Phase 9b — Signes routiers — Import complet depuis PDF officiel 🔄

> Indépendant des autres phases

### Contexte & état actuel (12 mars 2026)

- PDF source : `signaux.pdf` (53 pages, catalogue belge officiel valable dès 01/06/2027)
  - Véhiculés vectoriels (pas de bitmaps embarqués)
  - Structure : tableau 3 colonnes par page — `[NL] | [image + code] | [FR]`
  - Détection de tableau via `pymupdf.page.find_tables()` → bbox exacte par cellule
- **252 signes extraits** → `data/signs/*.png` + `data/signs/signs_index.json`
  - Format : PNG 3× zoom ≈ 216 DPI, fond gris → blanc (flood-fill)
  - Chaque signe = 2 lignes PDF : ligne 0 = code texte, ligne 1 = image vide
  - Script d'extraction : `scripts/extract_signs_full.py`
- BDD actuelle : seulement **~27 signes** — à remplacer entièrement

### Problèmes connus à régler avant import

- [ ] **A25** : image absente (ligne image à `i+2` au lieu de `i+1`) — 1 PNG à refaire manuellement ou corriger le regex de scan
- [ ] **Qualité variable des PNG** : certains ont encore un léger fond gris, d'autres des marges inégales
  - Piste : remplacer flood-fill par remplacement pixel-à-pixel de tous les gris proches de `(216,217,216)`
  - Piste : auto-crop tight + recentrage sur carré 400×400 (déjà testé dans version intermédiaire du script, mais causait d'autres problèmes)
- [ ] **Codes `M33-P.2`, `M41a-P.1`** : variantes de panneaux similaires — OK d'avoir un seul PNG pour la famille, à confirmer côté modèle BDD

### À faire — Import BDD

- [ ] Vérifier modèle `TrafficSign` : champs `code`, `name_fr`, `name_nl`, `image` — ajouter `name_nl` si absent (migration)
- [ ] Script `scripts/import_signs.py` : lire `signs_index.json`, créer/mettre à jour `TrafficSign` en BDD, copier PNG vers `media/signs/`
- [ ] Vérifier que les noms NL/FR sont complets (actuellement tronqués à 50 chars dans le log, vérifier JSON)
- [ ] Ajouter RU translations manquantes via DeepL ou manuellement

### À faire — Affichage

- [ ] `apps/reglementation/templates/reglementation/signs.html` : afficher `name_fr` / `name_nl` / `name_ru` selon langue active
- [ ] Page detail par signe avec image grande + descriptions multilingues
- [ ] Lier signes aux articles de loi concernés (`TrafficSign` ↔ `CodeArticle`)

---

## Vue d'ensemble du calendrier

```
2 mars 2026   : Phase 0 ✅  Phase 1 ✅  Phase 2 ✅  Phase 3 ✅
3-4 mars 2026 : Phase 4 🔄  AR 1975 questions : 85/122 (Gemini limite/jour)
4 mars 2026   : Phase 5b 🔄 Pipeline multi-loi implémenté, 1968+2005 complets,
               1998+2006+1976 scrapés, DeepL quota épuisé → rotation de compte
5 mars 2026   : Phase 5b ✅  10 lois importées (593 articles) — 1968b, 1985, 1989, 2001 ajoutés
               Phase 4  🔄  Prompt amélioré (3 théo + 5 prat, sous-points, no refs)
                             gemini-2.5-flash, thinking_budget=0, 107/593 (18%)
               Phase 7  🔄  /reglementation/ connecté aux 10 lois (templates + views)
               Phase 3  ✅  slugify_number() corrigé (NoReverseMatch 1998 réparé)
6 mars 2026   : Phase 4 🔜  Reprendre génération (~486 articles restants)
                             nohup bash scripts/run_questions.sh > logs/questions_$(date +%Y%m%d).log 2>&1 &
7-10 mars     : Phase 5 🔜  Import toutes les lois en BDD (05_import.py par loi)
Mars–Avril    : Phase 6     Admin dashboard
Avril–Mai     : Phase 7     Frontend utilisateur + lancement beta
Mai           : Phase 9b    Signes routiers — import complet PDF (200+ signes)
Mai–Juin      : Phase 9     i18n complète FR/NL/RU (UI + contenu)
Juin+         : Phase 8     SEO, contenu 2027 progressif
```
