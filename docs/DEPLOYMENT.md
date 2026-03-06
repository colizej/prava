# PRAVA — Guide de déploiement production

> Dernière mise à jour : 5 mars 2026

---

## Prérequis serveur

| Requis | Version |
|--------|---------|
| Python | 3.14+ |
| Node.js | **20+** (Tailwind v4 exige ≥20) — ou utiliser le binaire standalone (voir §3) |
| Gunicorn | ≥25.0 |
| Caddy 2 | proxy inverse + HTTPS automatique |
| SQLite | intégré (WAL mode activé, suffisant pour 1000+ users) |

---

## 1. Variables d'environnement

Copier `.env.example` → `.env` et remplir **toutes** les valeurs :

```bash
cp .env.example .env
nano .env
```

Variables obligatoires :

```env
DEBUG=False
SECRET_KEY=<générer avec: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
ALLOWED_HOSTS=prava.be,www.prava.be
SITE_URL=https://prava.be

# Mollie live (pas test_)
MOLLIE_API_KEY=live_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Mailjet
MAILJET_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxx
MAILJET_SECRET_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxx
DEFAULT_FROM_EMAIL=noreply@prava.be
ADMIN_EMAIL=votre@email.com

# Sentry (optionnel mais recommandé)
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
```

---

## 2. Installation des dépendances

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
npm install  # pour Tailwind CLI
```

---

## 3. Build des assets

### Si Node ≥ 20 disponible
```bash
npm install
make css
```

### Si Node < 20 (ex: Node 18 — utiliser le binaire standalone)

Le binaire Tailwind standalone ne dépend pas de Node du tout :

```bash
# Télécharger le binaire standalone Tailwind v4 (Linux x64)
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64
mv tailwindcss-linux-x64 tailwindcss
chmod +x tailwindcss
# make css détecte automatiquement ./tailwindcss et l'utilise
make css
```

> Le Makefile détecte `./tailwindcss` automatiquement — pas besoin de modifier les commandes.

```bash
# Collect static files
python manage.py collectstatic --noinput
```

---

## 4. Base de données

```bash
# Migrations
python manage.py migrate

# Données initiales
python manage.py seed_plans       # Forfaits shop
python manage.py createsuperuser  # Admin

# Import du code de la route (si pas encore fait)
python manage.py import_reglementation
```

---

## 5. Compilation des traductions

```bash
python manage.py compilemessages
```

---

## 6. Lancement avec Gunicorn

```bash
gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --timeout 60 \
  --access-logfile logs/gunicorn-access.log \
  --error-logfile logs/gunicorn-error.log
```

Ou via systemd (`/etc/systemd/system/prava.service`) :

```ini
[Unit]
Description=PRAVA Django application
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/prava
EnvironmentFile=/var/www/prava/.env
ExecStart=/var/www/prava/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 7. Configuration Caddy

Caddy gère HTTPS automatiquement (Let's Encrypt). Pas besoin de configurer les certificats.

`/etc/caddy/Caddyfile` :

```caddy
prava.be, www.prava.be {
    # Fichiers media (uploads utilisateurs)
    handle /media/* {
        root * /var/www/prava
        file_server
    }

    # Tout le reste → Gunicorn
    reverse_proxy localhost:8000 {
        header_up Host {host}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }
}
```

```bash
sudo systemctl reload caddy
```

> **Note :** les fichiers statiques (`/static/`) sont servis directement par WhiteNoise via Gunicorn — Caddy ne les touche pas. Seul `/media/` (avatars, images) est servi directement par Caddy.

---

## 8. Vérifications post-déploiement

```bash
# Check Django
python manage.py check --deploy

# Vérifier les migrations
python manage.py showmigrations | grep "\[ \]"

# Tester l'envoi d'email (console si DEBUG=True, Mailjet si DEBUG=False)
python manage.py shell -c "
from django.core.mail import send_mail
from django.conf import settings
send_mail('Test PRAVA', 'Ça marche!', settings.DEFAULT_FROM_EMAIL, [settings.ADMINS[0][1]])
print('Email envoyé')
"
```

---

## 9. Checklist déploiement

- [ ] `DEBUG=False` dans `.env`
- [ ] `SECRET_KEY` fort et unique
- [ ] `ALLOWED_HOSTS` contient le domaine réel
- [ ] `MOLLIE_API_KEY` commence par `live_` (pas `test_`)
- [ ] `MAILJET_API_KEY` et `MAILJET_SECRET_KEY` renseignés
- [ ] `make css` exécuté (Tailwind build)
- [ ] `python manage.py collectstatic --noinput` exécuté
- [ ] `python manage.py migrate` exécuté
- [ ] `python manage.py compilemessages` exécuté
- [ ] HTTPS configuré (Caddy — automatique)
- [ ] Webhook Mollie configuré sur `https://prava.be/shop/webhook/`
- [ ] `python manage.py check --deploy` sans erreurs critiques
- [ ] Sentry DSN configuré et testé

---

## 10. Mise à jour (update en production)

```bash
git pull
source venv/bin/activate
pip install -r requirements.txt
make css
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py compilemessages
sudo systemctl restart prava
```

---

## 11. Workflow — Ajout de contenu (questions, articles)

### Principe général

```
PC local                           Serveur production
─────────────────────              ──────────────────────────────
① Générer questions
   04_questions.py --law X
   (Gemini API, vos clés)
   ↓
② Vérifier / corriger
   data/processed/X/articles/
   ↓
③ Importer en BDD locale
   05_import.py --law X
   ↓
④ git add data/processed/
   git push                   →   ⑤ git pull
                                      05_import.py --law X
                                      (importe dans PostgreSQL)
                                      sudo systemctl restart prava  ← optionnel
```

### Pourquoi générer localement (pas sur le serveur)

- ✅ Clés API Gemini/DeepL sur votre machine — pas besoin de les mettre sur le serveur
- ✅ Facile à débuguer et corriger avant publication
- ✅ `data/processed/` est suivi par git (603 fichiers JSON) — synchronisation naturelle
- ✅ Zéro risque de planter le serveur pendant la génération (rate limiting, erreurs API)

### Commandes types

```bash
# --- LOCAL : générer et importer ---
python3 scripts/pipeline/04_questions.py --law 1968 --limit 10
python3 scripts/pipeline/05_import.py --law 1968
git add data/processed/1968/
git commit -m "feat: questions loi 1968 (93 articles)"
git push

# --- SERVEUR : synchroniser ---
git pull
source venv/bin/activate
python3 scripts/pipeline/05_import.py --law 1968
# pas besoin de restart sauf si nouvelle migration
```

### Images des questions

Les images sont dans `media/questions/` — **non versionnées** (gitignore).
Deux options :
- **Option A (simple)** : uploader via Django admin (`/admin/`) directement sur le serveur
- **Option B (script)** : `rsync -avz media/questions/ user@server:/var/www/prava/media/questions/`

### Calendrier recommandé

| Étape | Quand | Où |
|-------|-------|----|
| Déploiement initial | Maintenant | — |
| Publication articles (SEO) | J+0 | Serveur via admin |
| Génération questions 1975 (486 restants) | J+1 à J+7 | Local |
| Import questions 1975 | Au fil de l'eau | Serveur (git pull + import) |
| Ajout images questions | Parallèle | Via admin serveur |
| Ouverture tests aux utilisateurs | Quand 1975 complet | — |
