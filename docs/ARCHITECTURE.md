# PRAVA — Architecture technique

> Dernière mise à jour : 5 mars 2026

---

## 1. Stack technique

| Couche | Technologie | Version |
|--------|-------------|---------|
| Backend | Django | 6.0.2 |
| Runtime | Python | 3.14.0 |
| Serveur WSGI | Gunicorn | ≥25.0 |
| Base de données | SQLite (dev) → PostgreSQL (prod) | — |
| Frontend CSS | Tailwind CSS v4 | 4.2.1 |
| Frontend JS | Alpine.js (CDN) | 3.x |
| Fichiers statiques | WhiteNoise (CompressedManifestStaticFilesStorage) | ≥6.0 |
| Paiement | Mollie (Bancontact, Visa, iDEAL) | mollie-api-python ≥3.0 |
| Email | Mailjet SMTP | — |
| Erreurs | Sentry SDK | ≥2.0 |
| Traduction | DeepL Free API | deepl ≥1.17 |
| Questions IA | Google Gemini 2.5 Flash | google-genai ≥1.0 |
| i18n | FR (défaut) · NL · RU | gettext .po/.mo |

---

## 2. Django Apps

### `apps/main/`
Pages publiques, contact, SEO.

**Modèles :** `ContactMessage`, `FAQ`, `SiteConfig`
**Vues clés :** `home`, `about`, `contact`, `pricing`, `legal`
**Extras :** context processor global (`context_processors.py`), sitemaps, image utils (WebP)

---

### `apps/accounts/`
Authentification et profils utilisateur.

**Modèles :**
| Modèle | Description |
|--------|-------------|
| `UserProfile` | Extension du User (is_premium, premium_until, avatar, langue) |

**Logique freemium :**
- 15 questions/jour gratuites (`FREE_DAILY_QUESTIONS`)
- Premium = accès illimité via abonnement `shop`
- Lecture des règles = toujours gratuite

---

### `apps/reglementation/`
Cœur de l'application — code de la route belge.

**Modèles :**
| Modèle | Description |
|--------|-------------|
| `RuleCategory` | Catégorie / thème (code, permis, assurance...) |
| `CodeArticle` | Article du code (FR/NL/RU). Lié à une `RuleCategory`. |
| `TrafficSign` | Panneau de signalisation (code, image, descriptions FR/NL/RU) |
| `ArticleImage` | Image associée à un article |

**10 lois couvertes :** 1975, 1968, 1976, 1998, 2005, 2006, 1968b, 1985, 1989, 2001

---

### `apps/examens/`
Tests et questions d'examen.

**Modèles :**
| Modèle | Description |
|--------|-------------|
| `ExamQuestion` | Question (texte FR/NL/RU, type, difficulté, image) |
| `QuestionOption` | Option A/B/C (correct ou non, explication FR/NL/RU) |
| `ExamSession` | Session d'examen d'un utilisateur |
| `ExamResult` | Résultat par question dans une session |
| `SavedQuestion` | Questions sauvegardées par l'utilisateur |
| `StudyList` | Liste d'étude personnalisée |

---

### `apps/shop/`
Abonnements et paiements via Mollie.

**Modèles :**
| Modèle | Description |
|--------|-------------|
| `Plan` | Forfait (nom, prix, durée, bonus ⛽) |
| `Order` | Commande (UUID, user, plan, statut, mollie_payment_id) |

**Flux de paiement :**
```
/shop/checkout/<plan_key>/  →  POST  →  Mollie (checkout_url)
        ↓ (retour utilisateur)              ↓ (webhook serveur)
/shop/return/?order_id=…           /shop/webhook/
        ↓                                  ↓
     vérif Mollie              _activate_premium(order)
        ↓                              ↓
/shop/success/<id>/          → email confirmation (Mailjet)
                             → bonus ⛽ crédité (KeyWallet)
```

**Statuts Order :** `pending` → `paid` | `failed` | `expired` | `canceled`

---

### `apps/rewards/`
Système de réservoir de carburant ⛽ (gamification).

**Modèles :**
| Modèle | Description |
|--------|-------------|
| `KeySettings` | Singleton de configuration (capacité, icône, taux de remplissage) |
| `KeyWallet` | Portefeuille par utilisateur (balance en litres) |
| `KeyTransaction` | Journal des transactions (crédit/débit + raison) |

**Logique :**
- Le carburant s'accumule pendant que l'utilisateur est connecté (heartbeat toutes les 60s)
- **Échange :** 20L→+10q, 40L→+30q, 60L (plein)→+50q
- Réservoir max : 60L
- Bonus à l'achat d'un forfait : configurable par `Plan.key_bonus`

**Template tags :** `keys_widget` (navbar desktop), `keys_widget_mobile` (menu mobile)

---

### `apps/blog/`
Articles de blog (SEO, markdown).

### `apps/dashboard/`
Tableau de bord admin custom (gestion questions, stats).

---

## 3. Data Pipeline

```
[codedelaroute.be]  [wegcode.be]
        │                 │
        ▼                 ▼
   01_scrape.py  ─────────────→  data/laws/{year}/
                                  ├── fr_reglementation.json
                                  └── nl_reglementation.json
                                          │
                                          ▼
                                   02_translate.py (DeepL FR→RU)
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
                   04_questions.py (Gemini 2.5 Flash)
                              │  3 théoriques + 5 pratiques × FR/NL/RU
                              ▼
                    processed/questions/
                              │
                              ▼
                       05_import.py
                              │
                              ▼
                        Django DB (SQLite→PostgreSQL)
```

**Scripts :** voir [SCRIPTS.md](SCRIPTS.md)

---

## 4. Internationalisation (i18n)

| Langue | Statut | Fichier |
|--------|--------|---------|
| FR | Défaut (pas de .po) | — |
| NL | Actif | `locale/nl/LC_MESSAGES/django.po` |
| RU | Actif | `locale/ru/LC_MESSAGES/django.po` |

Compilation : `make messages` → `django.mo`

---

## 5. Sécurité

| Mécanisme | Statut |
|-----------|--------|
| CSRF protection | ✅ `CsrfViewMiddleware` |
| XSS / clickjacking | ✅ `XFrameOptionsMiddleware` |
| SecurityMiddleware | ✅ |
| HTTPS redirect | ✅ `SECURE_SSL_REDIRECT` (prod uniquement) |
| HSTS (1 an) | ✅ `SECURE_HSTS_SECONDS=31536000` (prod) |
| Cookies sécurisés | ✅ `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` (prod) |
| Fichiers statiques | ✅ WhiteNoise (pas de Nginx requis pour les statics) |
| Webhook Mollie | ✅ CSRF exempt + vérification payment_id via API |
| Sentry | ✅ `send_default_pii=False` (GDPR) |

---

## 6. Tailwind CSS

- **Input :** `static/css/input.css`
- **Output :** `static/css/output.css` ← **gitignored**, à rebuilder à chaque déploiement
- **Build :** `make css` → `npx @tailwindcss/cli -i ./static/css/input.css -o ./static/css/output.css --minify`
- **Version :** Tailwind CSS v4.2.1

---

## 7. Fichiers statiques en production

1. `make css` — build Tailwind
2. `python manage.py collectstatic --noinput` — copie vers `staticfiles/`
3. WhiteNoise sert `staticfiles/` avec compression gzip + cache headers

---

## 8. Variables d'environnement

Voir `.env.example` pour la liste complète. Variables obligatoires en production :

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Clé Django (≥50 chars aléatoires) |
| `DEBUG` | `False` en production |
| `ALLOWED_HOSTS` | ex. `prava.be,www.prava.be` |
| `DATABASE_URL` | PostgreSQL URL |
| `SITE_URL` | ex. `https://prava.be` |
| `MOLLIE_API_KEY` | Clé live Mollie (commence par `live_`) |
| `MAILJET_API_KEY` | Clé API Mailjet |
| `MAILJET_SECRET_KEY` | Secret Mailjet |
| `DEFAULT_FROM_EMAIL` | ex. `noreply@prava.be` |
| `ADMIN_EMAIL` | Email admin pour les notifications |
| `SENTRY_DSN` | DSN Sentry (optionnel mais recommandé) |


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
