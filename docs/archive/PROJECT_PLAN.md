# 🚗 PermisReady — Plan du Projet

> Application Django pour la préparation à l'examen théorique du permis de conduire en Belgique.
> Date de création : 27 février 2026

---

## 📋 Résumé du Projet

| Paramètre | Valeur |
|-----------|--------|
| **Framework** | Django 6.0+ |
| **Base de données** | SQLite3 (dev) → PostgreSQL (prod) |
| **Frontend** | Django Templates + Tailwind CSS + Alpine.js |
| **Serveur** | Gunicorn + Caddy |
| **Paiements** | Mollie (à implémenter) |
| **Langues** | FR / NL / RU |
| **Questions cibles** | 1000+ |

---

## 🏗️ Architecture des Applications

### Phase 1 — MVP (Actuel)

| App | Description | Statut |
|-----|-------------|--------|
| `main` | Coordination, page d'accueil, navigation, pages statiques | 🔨 En cours |
| `accounts` | Inscription, connexion, profils, quotas, progrès | 🔨 En cours |
| `blog` | Blog SEO, articles, catégories | 🔨 En cours |
| `reglementation` | Code de la route par thèmes, panneaux de signalisation | 🔨 En cours |
| `examens` | Questions d'examen, tests, catégories, résultats | 🔨 En cours |

### Phase 2 — Monétisation & Analytics

| App | Description | Statut |
|-----|-------------|--------|
| `shop` | Intégration Mollie, abonnements, factures | ⏳ Planifié |
| `analytics` | Statistiques utilisateurs, progrès, tableaux de bord | ⏳ Planifié |
| `notifications` | Emails, push, rappels | ⏳ Planifié |
| `newsletter` | Gestion newsletter, campagnes | ⏳ Planifié |

---

## 📂 Structure du Projet

```
permis-conduire/
├── manage.py
├── requirements.txt
├── .env
├── .gitignore
│
├── config/                     # Configuration Django
│   ├── settings.py             # Paramètres principaux
│   ├── urls.py                 # Routage URL principal
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                       # Applications Django
│   ├── main/                   # Coordination & pages statiques
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── context_processors.py
│   │   └── templates/main/
│   │
│   ├── accounts/               # Utilisateurs & profils
│   │   ├── models.py           # UserProfile, DailyQuota, Achievement
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── admin.py
│   │   ├── urls.py
│   │   └── templates/accounts/
│   │
│   ├── blog/                   # Blog SEO
│   │   ├── models.py           # BlogPost, BlogCategory
│   │   ├── views.py
│   │   ├── admin.py
│   │   ├── sitemaps.py
│   │   ├── urls.py
│   │   └── templates/blog/
│   │
│   ├── reglementation/         # Code de la route
│   │   ├── models.py           # RuleCategory, CodeArticle, TrafficSign
│   │   ├── views.py
│   │   ├── admin.py
│   │   ├── urls.py
│   │   └── templates/reglementation/
│   │
│   └── examens/                # Tests & questions
│       ├── models.py           # Category, Question, AnswerOption, TestAttempt
│       ├── views.py
│       ├── admin.py
│       ├── urls.py
│       └── templates/examens/
│
├── templates/                  # Templates globaux
│   ├── base.html
│   ├── includes/
│   │   ├── navbar.html
│   │   ├── footer.html
│   │   └── messages.html
│   └── errors/
│       ├── 404.html
│       └── 500.html
│
├── static/                     # Fichiers statiques
│   ├── css/
│   ├── js/
│   ├── img/
│   └── icons/
│
├── media/                      # Fichiers uploadés
│   ├── questions/
│   ├── blog/
│   ├── reglementation/
│   └── signs/
│
├── data/                       # Données scrapées (existantes)
│   ├── sites/
│   │   ├── codedelaroute.be/
│   │   ├── permis24.be/
│   │   ├── permisdeconduire-online.be/
│   │   └── readytoroad.be/
│   └── scraper.log
│
├── docs/                       # Documentation
│   ├── PROJECT_PLAN.md         # Ce document
│   ├── README.md
│   └── ... (anciens documents)
│
├── scripts_old/                # Anciens scripts de scraping
│
└── locale/                     # Fichiers de traduction i18n
    ├── fr/
    ├── nl/
    └── ru/
```

---

## 🗃️ Modèles de Données

### accounts

```
UserProfile
├── user → OneToOne(User)
├── language: CharField (fr/nl/ru)
├── avatar: ImageField
├── is_premium: BooleanField
├── premium_until: DateTimeField
├── total_questions_answered: IntegerField
├── correct_answers: IntegerField
└── created_at / updated_at

DailyQuota
├── user → ForeignKey(User)
├── date: DateField
├── questions_answered: IntegerField
└── max_questions: IntegerField (default: 15)
```

### blog

```
BlogCategory
├── name: CharField
├── name_nl / name_ru: CharField
├── slug: SlugField
├── description: TextField
└── order: IntegerField

BlogPost
├── title / title_nl / title_ru: CharField
├── slug: SlugField
├── author → ForeignKey(User)
├── category → ForeignKey(BlogCategory)
├── content / content_nl / content_ru: TextField
├── excerpt / excerpt_nl / excerpt_ru: CharField
├── featured_image: ImageField
├── is_published: BooleanField
├── published_at: DateTimeField
├── views_count: IntegerField
├── read_time: IntegerField
├── meta_title / meta_description / keywords: CharField
└── created_at / updated_at
```

### reglementation

```
RuleCategory
├── name / name_nl / name_ru: CharField
├── slug: SlugField
├── icon: CharField
├── description / description_nl / description_ru: TextField
└── order: IntegerField

CodeArticle
├── article_number: CharField (ex: "Art. 12.1")
├── category → ForeignKey(RuleCategory)
├── title / title_nl / title_ru: CharField
├── content / content_nl / content_ru: TextField
├── is_free: BooleanField
├── order: IntegerField
└── created_at / updated_at

TrafficSign
├── code: CharField (ex: "C1")
├── category → ForeignKey(RuleCategory)
├── name / name_nl / name_ru: CharField
├── description / description_nl / description_ru: TextField
├── image: ImageField
└── order: IntegerField
```

### examens

```
ExamCategory
├── name / name_nl / name_ru: CharField
├── slug: SlugField
├── icon: CharField
├── description / description_nl / description_ru: TextField
├── order: IntegerField
└── is_active: BooleanField

Question
├── category → ForeignKey(ExamCategory)
├── code_article → ForeignKey(CodeArticle, nullable)
├── traffic_sign → ForeignKey(TrafficSign, nullable)
├── text / text_nl / text_ru: TextField
├── image: ImageField
├── explanation / explanation_nl / explanation_ru: TextField
├── difficulty: IntegerField (1-3)
├── is_active: BooleanField
├── is_official: BooleanField
├── source: CharField
├── times_answered: IntegerField
├── times_correct: IntegerField
├── tags: JSONField
└── created_at / updated_at

AnswerOption
├── question → ForeignKey(Question)
├── letter: CharField (A/B/C/D)
├── text / text_nl / text_ru: CharField
├── is_correct: BooleanField
└── order: IntegerField

TestAttempt
├── uuid: UUIDField
├── user → ForeignKey(User)
├── test_type: CharField (practice/exam)
├── category → ForeignKey(ExamCategory, nullable)
├── answers_data: JSONField
├── score: IntegerField
├── total_questions: IntegerField
├── percentage: DecimalField
├── passed: BooleanField
├── started_at: DateTimeField
├── completed_at: DateTimeField
└── time_spent: IntegerField (seconds)
```

---

## 🌐 Langues — Trilingual (FR/NL/RU)

### Approche

On utilise des **champs séparés** pour chaque langue directement dans les modèles :

```python
# Exemple
title = models.CharField(max_length=200)          # FR (défaut)
title_nl = models.CharField(max_length=200, blank=True)  # NL
title_ru = models.CharField(max_length=200, blank=True)  # RU
```

### Page Termes / Glossaire

Un glossaire trilingue des termes de conduite :

```
Glossary
├── term: CharField
├── term_nl / term_ru: CharField
├── definition / definition_nl / definition_ru: TextField
├── category: CharField
└── order: IntegerField
```

### Middleware de langue

La langue est détectée par :
1. Préférence utilisateur (UserProfile.language)
2. Paramètre URL (?lang=nl)
3. Cookie
4. Accept-Language header

---

## 💰 Monétisation — Tarifs

### Plans d'abonnement (Phase 2 — Mollie)

| Plan | Prix | Durée | Questions/jour |
|------|------|-------|----------------|
| **Gratuit** | 0€ | — | 15 questions |
| **Journalier** | €1.99 | 24h | Illimité |
| **Hebdomadaire** | €4.99 | 7 jours | Illimité |
| **Mensuel** | €9.99 | 30 jours | Illimité |
| **Trimestriel** | €19.99 | 90 jours | Illimité |

### Fonctionnalités Premium

- ✅ Questions illimitées
- ✅ Mode examen simulé
- ✅ Statistiques détaillées
- ✅ Accès aux articles premium du code
- ✅ Sans publicité
- ✅ Support prioritaire

---

## 🔍 SEO — Stratégie Blog

### Fonctionnalités SEO

- [x] Meta title / description par article
- [x] Canonical URLs
- [x] Open Graph tags (Facebook, LinkedIn)
- [x] Twitter Cards
- [x] Schema.org (Article, FAQPage, BreadcrumbList)
- [x] Sitemap XML automatique
- [x] robots.txt
- [x] Breadcrumbs structurés
- [x] URLs SEO-friendly (slugs)
- [x] Pagination SEO
- [x] Images avec alt text
- [x] Temps de lecture estimé
- [x] Dates de publication structurées
- [x] hreflang pour FR/NL/RU

### Types de contenu pour le blog

1. **Guides** — "Comment réussir l'examen théorique en 2026"
2. **Explications** — "Les panneaux de signalisation expliqués"
3. **Actualités** — "Changements du code de la route 2026"
4. **Conseils** — "10 erreurs fréquentes à l'examen"
5. **Témoignages** — Histoires de réussite

---

## 🚀 Déploiement

### Stack de production

```
Client → Caddy (HTTPS, reverse proxy)
              → Gunicorn (Django WSGI)
                    → SQLite3 (phase 1)
                    → PostgreSQL (phase 2)
```

### Caddy config (exemple)

```
permisready.be {
    reverse_proxy localhost:8000
    encode gzip
    file_server /static/* {
        root /path/to/staticfiles/
    }
}
```

### Commandes de déploiement

```bash
# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Appliquer les migrations
python manage.py migrate

# Lancer Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

---

## 📅 Calendrier de Développement

### Semaine 1 : Fondations ✅ En cours

- [x] Structurer le projet Django
- [x] Créer les 5 applications
- [ ] Implémenter les modèles
- [ ] Configurer l'admin
- [ ] Créer les templates de base
- [ ] Importer les données existantes

### Semaine 2 : Fonctionnalités Core

- [ ] Système de quiz complet (practice + exam)
- [ ] Pages réglementation
- [ ] Blog avec SEO complet
- [ ] Système d'inscription/connexion
- [ ] Profil utilisateur avec statistiques

### Semaine 3 : Frontend & UX

- [ ] Tailwind CSS + design mobile-first
- [ ] Alpine.js composants interactifs
- [ ] PWA (manifest.json, Service Worker)
- [ ] Animations et transitions
- [ ] Tests sur mobiles

### Semaine 4 : Monétisation & Lancement

- [ ] Intégration Mollie (app shop)
- [ ] Système de quotas
- [ ] Analytics
- [ ] Tests finaux
- [ ] Déploiement production

---

## 📚 Dépendances

### requirements.txt

```
Django>=6.0
Pillow>=12.0
django-environ>=0.13
gunicorn>=25.0
whitenoise>=6.0
```

### Futures dépendances (Phase 2)

```
mollie-api-python    # Paiements
django-allauth       # Social auth
django-import-export # Import/export admin
redis                # Cache & sessions
celery               # Tâches async
```

---

**Document vivant — mis à jour au fur et à mesure du développement.**
