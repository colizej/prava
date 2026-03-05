# PRAVA — Documentation du projet

> Application web Django de préparation à l'examen théorique du permis de conduire en Belgique.
> Langues : FR · NL · RU

---

## Navigation de la documentation

| Document | Description |
|---|---|
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Architecture technique : stack, apps Django, sécurité, Tailwind, i18n |
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | Guide de déploiement production (Gunicorn, Nginx, checklist) |
| **[ROADMAP.md](ROADMAP.md)** | Roadmap par phases et statut d'avancement |
| **[DATA_SCHEMA.md](DATA_SCHEMA.md)** | Schéma JSON des données (lois, articles, questions) |
| **[SCRIPTS.md](SCRIPTS.md)** | Documentation du pipeline de scripts |
| `archive/` | Documents de recherche initiale (brainstorming, analyses concurrents) |

---

## Vue d'ensemble du projet

**PRAVA** permet aux candidats au permis de conduire (catégorie B) de préparer l'examen théorique belge.

### Sources légales

| Loi | Référence | Dossier | Statut |
|-----|-----------|---------|--------|
| AR du 1er décembre 1975 | Code de la route — version actuelle | `data/laws/1975/` | ✅ En cours de traitement |
| Nouveau code (prévu 2027) | Version révisée | `data/laws/2027/` | 🔜 Placeholder — publication progressive |

> La migration vers 2027 se fera **progressivement**, en parallèle de l'indexation SEO du contenu 1975.

### Langues

| Langue | Source | Outil |
|--------|--------|-------|
| **FR** | Source primaire | `codedelaroute.be` |
| **NL** | Source secondaire | `wegcode.be` (même structure HTML) |
| **RU** | Traduction machine | DeepL Free API (500 000 car/mois) |

### Stack technique

- **Backend** : Django 6.0.2, Python 3.14
- **Base de données** : SQLite (dev) → PostgreSQL (prod)
- **Frontend** : Tailwind CSS v4.2.1 + Alpine.js
- **Paiement** : Mollie (Bancontact, Visa, iDEAL)
- **Email** : Mailjet SMTP
- **Traduction** : DeepL Free API
- **Génération de questions** : Gemini 2.5 Flash (Google AI)
- **Erreurs / monitoring** : Sentry SDK

---

## Structure du projet

```
prava/
├── apps/
│   ├── accounts/          # Utilisateurs, abonnements, badges quotidiens
│   ├── blog/              # Articles de blog (SEO)
│   ├── examens/           # Tests, questions, sessions d'examen
│   ├── main/              # Pages principales (accueil, about...)
│   └── reglementation/    # Articles du code de la route
│
├── config/                # Settings Django, URLs racine, wsgi/asgi
│
├── data/                  # ← TOUTES les données (voir DATA_SCHEMA.md)
│   ├── laws/
│   │   ├── 1975/          # Loi actuelle (en production)
│   │   └── 2027/          # Future loi (placeholder)
│   ├── processed/         # Données traitées par les scripts
│   │   ├── 1975/
│   │   │   ├── articles/  # Un fichier JSON par article
│   │   │   └── themes/    # Regroupés par thème (code, permis, assurance...)
│   │   └── questions/     # Questions générées (avant import BDD)
│   ├── sources/           # Données brutes scrapées (NE PAS MODIFIER)
│   │   ├── codedelaroute.be/
│   │   ├── wegcode.be/
│   │   └── competitors/   # Analyses concurrentielles (référence uniquement)
│   └── templates/         # Schémas et templates JSON de référence
│
├── docs/                  # ← CE DOSSIER — documentation vivante
│
├── scripts/
│   ├── pipeline/          # Scripts numérotés 01 → 05 (pipeline principal)
│   ├── utils/             # Clients DeepL, Gemini, helpers JSON/diff
│   └── archive/           # Anciens scripts expérimentaux (NE PAS EXÉCUTER)
│
├── static/                # CSS, JS, images statiques
├── media/                 # Fichiers uploadés (images, avatars)
└── templates/             # Templates HTML Django
```

---

## Pipeline de données — ordre d'exécution

```bash
python scripts/pipeline/01_scrape.py      # FR + NL → data/laws/1975/
python scripts/pipeline/02_translate.py   # FR → RU via DeepL
python scripts/pipeline/03_process.py     # → data/processed/1975/articles/
python scripts/pipeline/04_questions.py   # → data/processed/questions/ (Gemini)
python scripts/pipeline/05_import.py      # → Django DB
```

> Ces scripts sont également déclenchables depuis le **Admin Dashboard** (voir ARCHITECTURE.md §4).

---

## Statut — Dernière mise à jour

**2 mars 2026** — Phase 0 complétée : restructuration de l'architecture (dossiers, docs).
Prochaine étape : **Phase 1** — implémentation de `01_scrape.py` (FR + NL → JSON).
