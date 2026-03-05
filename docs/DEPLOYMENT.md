# PRAVA — Guide de déploiement production

> Dernière mise à jour : 5 mars 2026

---

## Prérequis serveur

| Requis | Version |
|--------|---------|
| Python | 3.14+ |
| Node.js | 18+ (pour build Tailwind) |
| PostgreSQL | 15+ |
| Gunicorn | ≥25.0 |
| Nginx (recommandé) | pour proxy + HTTPS |

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
DATABASE_URL=postgres://user:password@localhost:5432/prava

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

```bash
# Build Tailwind CSS (OBLIGATOIRE — output.css est gitignored)
make css
# ou directement :
npx @tailwindcss/cli -i ./static/css/input.css -o ./static/css/output.css --minify

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

## 7. Configuration Nginx

```nginx
server {
    listen 80;
    server_name prava.be www.prava.be;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name prava.be www.prava.be;

    ssl_certificate     /etc/letsencrypt/live/prava.be/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/prava.be/privkey.pem;

    location /media/ {
        alias /var/www/prava/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

> **Note :** les fichiers statiques (`/static/`) sont servis directement par WhiteNoise via Gunicorn — pas de configuration Nginx nécessaire pour les statics.

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
- [ ] `DATABASE_URL` pointe vers PostgreSQL
- [ ] `MOLLIE_API_KEY` commence par `live_` (pas `test_`)
- [ ] `MAILJET_API_KEY` et `MAILJET_SECRET_KEY` renseignés
- [ ] `make css` exécuté (Tailwind build)
- [ ] `python manage.py collectstatic --noinput` exécuté
- [ ] `python manage.py migrate` exécuté
- [ ] `python manage.py compilemessages` exécuté
- [ ] HTTPS configuré (Let's Encrypt / Nginx)
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
