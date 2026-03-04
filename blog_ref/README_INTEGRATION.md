# Blog App — Guide d'intégration dans un nouveau projet Django

Ce dossier contient tout le nécessaire pour intégrer l'application `blog` dans un nouveau projet Django.

---

## Structure du dossier `blog_ref/`

```
blog_ref/
├── README_INTEGRATION.md        ← ce fichier
├── blog/                        ← l'application Django (à copier à la racine du projet)
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── author_views.py          ← vues de gestion d'articles (auteurs)
│   ├── forms.py
│   ├── middleware.py            ← redirect anciens URLs catégories
│   ├── models.py                ← Article, Category, Tag, ArticleComment, ArticleLike, ArticleSeries, BlogSettings
│   ├── sitemaps.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   ├── management/
│   │   └── commands/
│   │       ├── publish_scheduled_articles.py
│   │       ├── stats_audit.py
│   │       ├── stats_report.py
│   │       ├── create_creators_guide_article.py
│   │       ├── fix_canonical_urls.py
│   │       └── update_faq_articles.py
│   ├── migrations/              ← 20 migrations (0001 → 0020)
│   ├── static/
│   │   └── admin/js/
│   │       └── markdown-editor.js
│   └── templatetags/
│       ├── article_extras.py    ← filtre markdown_to_html + autres
│       └── responsive_image.py
├── templates/
│   └── blog/                    ← templates HTML à placer dans templates/blog/
│       ├── article_confirm_delete.html
│       ├── article_detail.html
│       ├── article_form.html
│       ├── article_list.html
│       ├── category_detail.html
│       └── partials/
│           └── comment.html
├── utils/
│   └── yaml_utils.py            ← utilitaire partagé (YAML frontmatter parser)
├── tests/
│   └── blog/
│       ├── __init__.py
│       └── test_article_yaml.py
└── docs/                        ← documentation métier et technique
    ├── ArticlesBlog.md
    ├── EXCERPT_AUTO_GENERATION.md
    ├── SCHEDULED_PUBLISHING_GUIDE.md
    ├── QUICK_SEO_GUIDE.md
    ├── BLOG_YAML_REFACTOR_2026.md
    ├── MARKDOWN_STANDARD.md
    ├── YAML_FORMATS_COMPATIBILITY.md
    ├── YAML_TEXT_CLEANING.md
    └── TESTING_YAML_UTILS.md
```

---

## Dépendances Python (requirements)

À ajouter dans `requirements.txt` du nouveau projet :

```
django>=4.2
markdown>=3.5
Pillow>=10.0
PyYAML>=6.0
```

---

## Dépendances vers d'autres apps (POINTS D'ATTENTION)

L'app `blog` a des références vers d'autres apps du projet d'origine.
**Tu dois les adapter dans le nouveau projet.**

### 1. `profiles.Profile` — ForeignKey auteur

Dans `blog/models.py` :
```python
profile_author = models.ForeignKey(
    'profiles.Profile',
    on_delete=models.SET_NULL,
    null=True, blank=True,
    related_name="articles"
)
```

**Options dans le nouveau projet :**
- Créer une app `profiles` avec un modèle `Profile` ayant au minimum : `user (OneToOneField)`, `can_write_articles (BooleanField)`
- OU remplacer par `settings.AUTH_USER_MODEL` (User Django standard) — cela nécessite de modifier `models.py` et `author_views.py`
- OU laisser `null=True, blank=True` et passer `'profiles.Profile'` → `'auth.User'`

### 2. `profiles.Play` — ManyToMany produits recommandés

Dans `blog/models.py` :
```python
recommended_products = models.ManyToManyField(
    'profiles.Play',
    blank=True,
    related_name='recommended_in_articles'
)
```

**Options :**
- Supprimer ce champ si le nouveau projet n'a pas de modèle "Play"
- Créer un modèle `Play` dans une app `profiles`
- Remplacer par un autre modèle existant dans le nouveau projet

### 3. `profiles.ProductCategory` — dans templatetags

Dans `blog/templatetags/article_extras.py` (ligne ~124) :
```python
from profiles.models import ProductCategory
```

**Option :** Commenter cette ligne ou adapter si le nouveau projet ne l'a pas.

### 4. `author_views.py` — `user.profile`

Ce fichier utilise `request.user.profile` et `profile.can_write_articles`.
Cela suppose que le `User` Django a un attribut `profile` (OneToOne avec `Profile`).
Si tu utilises l'`User` standard, remplace par `request.user.is_staff`.

### 5. `views.py` — Fallback vers Play si article non trouvé

La vue `article_detail` essaie, si l'article n'est pas trouvé, de chercher un objet `Play` avec le même slug. **Si tu n'as pas de `Play` dans ton projet, supprime ce bloc** (lignes ~38-52 dans `views.py`).

### 6. Management commands avec `profiles`

Les commandes suivantes importent `profiles.models` :
- `management/commands/stats_audit.py` — importe `Play`
- `management/commands/stats_report.py` — importe `Play`
- `management/commands/create_creators_guide_article.py` — importe `Profile`

Adapter ou supprimer ces commandes si nécessaire.

---

## Intégration pas à pas

### Étape 1 — Copier les fichiers

```bash
# Depuis le dossier blog_ref/
cp -r blog/  <nouveau_projet>/
cp -r templates/blog/  <nouveau_projet>/templates/blog/
cp utils/yaml_utils.py  <nouveau_projet>/utils/yaml_utils.py
```

### Étape 2 — `settings.py`

```python
INSTALLED_APPS = [
    ...
    'blog',
    ...
]

MIDDLEWARE = [
    ...
    'blog.middleware.CategoryQueryRedirectMiddleware',  # Redirect /blog/?category=slug
    ...
]
```

### Étape 3 — `urls.py` principal

```python
from blog.sitemaps import ArticleSitemap
from django.contrib.sitemaps.views import sitemap

sitemaps = {
    'articles': ArticleSitemap,
    # ... autres sitemaps
}

urlpatterns = [
    ...
    path('', include('blog.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    ...
]
```

### Étape 4 — Migrations

```bash
python manage.py migrate blog
```

> ⚠️ Les migrations font référence à `profiles.Profile` et `profiles.Play`.
> Si ces modèles n'existent pas, les migrations 0004, 0006, 0012, 0016, 0017 échoueront.
> **Voir section "Adapter les migrations" ci-dessous.**

### Étape 5 — Templates base

Les templates `blog/*.html` héritent probablement d'un `base.html` du projet d'origine.
Vérifie les balises `{% extends "..." %}` et adapte-les à la structure du nouveau projet.

---

## Adapter les migrations (si pas de `profiles` app)

Si le nouveau projet n'a **pas** d'app `profiles`, il faut modifier 4 migrations :

### Migration 0004 — `profile_author`
Remplacer `to='profiles.profile'` par `to=settings.AUTH_USER_MODEL` ou supprimer le champ.

### Migration 0006 — `author_profile` dans ArticleComment
Même chose.

### Migration 0012 — `recommended_products`
Supprimer ce champ de la migration si pas de `Play`.

### Migration 0016 et 0017 — Migrate author → profile
Ces migrations de données peuvent être ignorées si tu pars d'une DB vide.

**Alternative simple :** créer les migrations from scratch :
```bash
# Supprimer blog/migrations/ (sauf __init__.py)
# Adapter models.py (retirer FK vers profiles)
python manage.py makemigrations blog
```

---

## Modèles inclus dans le blog

| Modèle | Description |
|--------|-------------|
| `Article` | Article de blog (Markdown + YAML frontmatter, statuts draft/review/published) |
| `ArticleImage` | Images attachées à un article |
| `Category` | Catégorie d'article |
| `Tag` | Tag d'article |
| `ArticleComment` | Commentaires avec modération (approbation manuelle) |
| `ArticleLike` | J'aime (par user ou session anonyme) |
| `ArticleSeries` | Série d'articles (ex: tutoriel en plusieurs parties) |
| `BlogSettings` | Paramètres globaux du blog (singleton) |

---

## URLs générées par le blog

| URL | Nom | Description |
|-----|-----|-------------|
| `/blog/` | `blog:article_list` | Liste des articles |
| `/blog/<slug>/` | `blog:category_detail` | Détail d'une catégorie |
| `/<slug>/` | `blog:article_detail` | Détail d'un article |
| `/<slug>/like/` | `blog:like_article` | Like un article (POST) |
| `/<slug>/comment/` | `blog:add_comment` | Poster un commentaire (POST) |
| `/articles/new/` | `blog:article_create` | Créer un article (auteurs) |
| `/articles/<slug>/edit/` | `blog:article_edit` | Modifier un article |
| `/articles/<slug>/delete/` | `blog:article_delete` | Supprimer un article |

---

## Format des articles (YAML frontmatter + Markdown)

Les articles sont écrits en Markdown avec un entête YAML optionnel :

```yaml
---
title: Mon article
slug: mon-article
status: published
meta_description: Description SEO de 50-160 caractères
category: nom-categorie
tags:
  - tag1
  - tag2
---

Contenu de l'article en **Markdown**...
```

Voir `docs/ArticlesBlog.md` et `docs/MARKDOWN_STANDARD.md` pour le format complet.

---

## Fonctionnalités clés

- ✅ Articles en Markdown avec YAML frontmatter
- ✅ Génération automatique du HTML depuis Markdown
- ✅ Support vidéos YouTube/Vimeo intégrées `[video:youtube:VIDEO_ID]`
- ✅ Variantes d'images responsives (WebP)
- ✅ Catégories et tags
- ✅ Séries d'articles
- ✅ Articles mis en avant (featured)
- ✅ Pages techniques (FAQ, légal) séparées du blog
- ✅ Commentaires avec modération manuelle
- ✅ J'aime (users connectés + anonymes par session)
- ✅ Publication planifiée (scheduled publishing)
- ✅ Sitemap XML automatique
- ✅ SEO : meta_title, meta_description, canonical_url, og_title, og_description
- ✅ Temps de lecture estimé
- ✅ Navigation précédent/suivant dans la catégorie
- ✅ Produits recommandés dans les articles (nécessite `profiles.Play`)
- ✅ Middleware redirect anciens URLs catégories
