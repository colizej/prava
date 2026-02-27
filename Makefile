# ============================================================================
# PRAVA.be — Makefile
# ============================================================================

PYTHON ?= venv/bin/python
PORT   ?= 8000
HOST   ?= 127.0.0.1

.PHONY: dev stop restart migrate shell static messages clean superuser help css css-watch

# ---------- Server management ----------

## Stop any running Django dev servers
stop:
	@echo "⏹  Stopping active Django servers..."
	@-lsof -ti :$(PORT) | xargs kill -9 2>/dev/null || true
	@echo "   Done."

## Build Tailwind CSS (one-shot)
css:
	@echo "🎨 Building Tailwind CSS..."
	npx @tailwindcss/cli -i ./static/css/input.css -o ./static/css/output.css --minify

## Watch Tailwind CSS (auto-rebuild)
css-watch:
	@echo "👁  Watching Tailwind CSS..."
	npx @tailwindcss/cli -i ./static/css/input.css -o ./static/css/output.css --watch

## Start the development server (builds CSS first)
dev: stop css
	@echo "▶  Starting server on http://$(HOST):$(PORT)/ ..."
	$(PYTHON) manage.py runserver $(HOST):$(PORT)

## Restart = stop + dev (alias)
restart: dev

# ---------- Database ----------

## Run migrations
migrate:
	$(PYTHON) manage.py makemigrations
	$(PYTHON) manage.py migrate

## Import regulation data from JSON
import-regl:
	$(PYTHON) manage.py import_reglementation

## Open Django shell
shell:
	$(PYTHON) manage.py shell

# ---------- Static / i18n ----------

## Collect static files
static:
	$(PYTHON) manage.py collectstatic --noinput

## Compile translations
messages:
	$(PYTHON) manage.py compilemessages

# ---------- Utilities ----------

## Remove __pycache__ and *.pyc
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "🧹 Cleaned."

## Create superuser
superuser:
	$(PYTHON) manage.py createsuperuser

## Show help
help:
	@echo ""
	@echo "  PRAVA.be — available commands:"
	@echo "  ─────────────────────────────────"
	@echo "  make dev        — Build CSS, stop servers & start dev server"
	@echo "  make css        — Build Tailwind CSS (one-shot)"
	@echo "  make css-watch  — Watch & rebuild Tailwind CSS"
	@echo "  make stop       — Stop active Django servers on port $(PORT)"
	@echo "  make restart    — Alias for dev (stop + start)"
	@echo "  make migrate    — makemigrations + migrate"
	@echo "  make shell      — Django shell"
	@echo "  make static     — collectstatic"
	@echo "  make messages   — compilemessages"
	@echo "  make clean      — Remove __pycache__ / *.pyc"
	@echo "  make superuser  — Create superuser"
	@echo ""
	@echo "  Override port:  make dev PORT=9000"
	@echo ""
