# PRAVA — Architecture technique

> Dernière mise à jour : 2 mars 2026

---

## 1. Django Apps

### `apps/reglementation/`
Cœur de l'application — gestion du code de la route.

**Modèles principaux :**
| Modèle | Description |
|--------|-------------|
| `RuleCategory` | Catégorie / thème (code, permis, assurance...) |
| `CodeArticle` | Article du code (FR/NL/RU). Lié à une `RuleCategory`. |
| `TrafficSign` | Panneau de signalisation (code, image, descriptions FR/NL/RU) |
| `ArticleImage` | Image associée à un article |

**Relations :**
```
RuleCategory (1) ──→ (N) CodeArticle
CodeArticle  (1) ──→ (N) ArticleImage
TrafficSign         (utilisé dans questions et articles)
```

### `apps/examens/`
Tests et questions d'examen.

**Modèles :**
- `ExamQuestion` — Question (texte FR/NL/RU, type, difficulté, image)
- `QuestionOption` — Option de réponse (A/B/C, correct ou non, explication)
- `ExamSession` — Session d'examen d'un utilisateur
- `ExamResult` — Résultat par question

### `apps/accounts/`
Gestion utilisateurs et freemium.

**Logique freemium :**
- Chaque connexion → 1 badge (token)
- Badge = accès à 1 examen complet (50 questions)
- Épuisé → "Reviens demain" ou abonnement premium
- Lecture des règles = toujours gratuite

---

## 2. Data Pipeline

```
[codedelaroute.be]  [wegcode.be]
        │                 │
        ▼                 ▼
   01_scrape.py  ─────────────→  data/laws/1975/
                                  ├── fr_reglementation.json
                                  └── nl_reglementation.json
                                          │
                                          ▼
                                   02_translate.py (DeepL)
                                          │
                                          ▼
                                  ru_reglementation.json
                                          │
                                          ▼
                                   03_process.py
                                          │
                              ┌───────────┴───────────┐
                              ▼                       ▼
                    processed/articles/     processed/themes/
                              │
                              ▼
                       04_questions.py (Gemini)
                              │
                              ▼
                    processed/questions/
                              │
                              ▼
                       05_import.py
                              │
                              ▼
                        Django DB (SQLite→PostgreSQL)
```

---

## 3. Structure JSON des données

Voir [DATA_SCHEMA.md](DATA_SCHEMA.md) pour le schéma complet.

**Hiérarchie :**
```
data/laws/{year}/
    fr_reglementation.json   ← JSON complet (tous les articles)
    nl_reglementation.json
    ru_reglementation.json

data/processed/{year}/articles/
    fr_art001.json           ← Un article, toutes les langues
    nl_art001.json
    ru_art001.json

data/processed/questions/
    art001_questions.json    ← 5 questions par article
```

---

## 4. Admin Dashboard

**URL :** `/admin/dashboard/`
**Accès :** superuser uniquement

### Architecture de la vue

```python
# apps/reglementation/admin_views.py
class PravaDashboardView(AdminSiteMixin, TemplateView):
    template_name = "admin/dashboard.html"

# Chaque bouton déclenche un management command via subprocess
# Le résultat est streamé via HTMX (Server-Sent Events ou polling)
```

### Boutons et actions

| Bouton | Script | Output |
|--------|--------|--------|
| ▶ Scraper FR + NL | `01_scrape.py` | Nb articles scrapés, diff si re-scraping |
| ▶ Traduire RU | `02_translate.py` | Nb articles traduits, quota restant DeepL |
| ▶ Générer questions | `03_process.py` + `04_questions.py` | Nb questions générées |
| ▶ Importer en BDD | `05_import.py` | Nb créés, mis à jour, erreurs |

### Interface de révision des questions

- Liste paginée des questions générées (avant import)
- Champs éditables inline : texte, options, explication
- Ajout d'image (code panneau ou upload)
- Actions : Prévisualiser · Approuver · Supprimer

---

## 5. Versioning des lois

Le dossier `data/laws/{year}/` permet de gérer plusieurs versions du code.

```python
# config/settings.py
CURRENT_LAW_YEAR = "1975"    # Version active
UPCOMING_LAW_YEAR = "2027"   # Version future (publication progressive)
```

**Stratégie de migration vers 2027 :**
1. Scraper le nouveau code dans `data/laws/2027/`
2. Le comparer avec 1975 (diff automatique)
3. Publier les articles **modifiés/nouveaux** progressivement
4. Garder les articles 1975 actifs tant que 2027 n'est pas complet

---

## 6. Variables d'environnement

```bash
# .env (ne jamais committer)
SECRET_KEY=...
DEBUG=True

# DeepL Free API
DEEPL_API_KEY=...

# Gemini API
GEMINI_API_KEY=...

# Base de données (prod)
DATABASE_URL=postgres://...
```

---

## 7. Déploiement (cible)

- **Hébergement** : VPS (Hetzner/OVH) ou Railway
- **Serveur WSGI** : Gunicorn
- **Proxy** : Nginx
- **Certif SSL** : Let's Encrypt
- **Média** : stockage local ou S3-compatible
