# Workflow : Génération et Import des Questions d'examen

Ce document décrit comment générer des questions via Gemini chaque jour, comment
consulter les résultats localement, et comment les déployer en base de données
sur le serveur de production.

---

## Vue d'ensemble du pipeline

```
data/processed/{loi}/articles/art-{slug}.json
        │
        ▼
  04_questions.py  ←── Gemini API (génération FR/NL/RU)
        │
        ▼
  art-{slug}.json  (champ exam_questions rempli)
        │
        ▼
  05_import.py  ←── Django ORM (upsert en BDD)
        │
        ▼
  SQLite local / PostgreSQL prod
```

Lois disponibles : `1975 1968 1968b 1976 1985 1989 1998 2001 2005 2006`

---

## 1. Génération quotidienne des questions

### Prérequis

- `GEMINI_API_KEY` présent dans le fichier `.env`
- Virtualenv activé (ou utiliser le chemin complet `venv/bin/python3`)

### Лancer toutes les lois (script complet)

```bash
# Depuis la racine du projet
nohup bash scripts/run_questions.sh >> logs/questions_$(date +%Y%m%d).log 2>&1 &
echo "PID: $!"
```

> `nohup` empêche l'arrêt du processus si le terminal se ferme.
> Le script contient `exec < /dev/null` pour éviter l'erreur Python
> _"Bad file descriptor"_ qui survient quand stdin est fermé par nohup.
> Le log est créé dans `logs/questions_YYYYMMDD.log`.

### Lancer une seule loi

```bash
venv/bin/python3 scripts/pipeline/04_questions.py --law 1975
```

### Options utiles

| Option | Description |
|---|---|
| `--law 1975` | Traiter uniquement cette loi |
| `--limit 10` | Traiter seulement les 10 premiers articles en attente |
| `--dry-run` | Simuler sans appeler l'API |
| `--regenerate` | Réécrire les questions déjà générées |
| `--verbose` | Log détaillé |

### Suivre la progression en temps réel

```bash
tail -f logs/questions_$(date +%Y%m%d).log
```

### Vérifier l'état d'avancement par loi (JSON)

```bash
python3 -c "
import json
from pathlib import Path
from collections import defaultdict
stats = defaultdict(lambda: {'total':0,'done':0})
for f in Path('data/processed').rglob('art-*.json'):
    law = f.parent.parent.name
    stats[law]['total'] += 1
    d = json.loads(f.read_text())
    if d.get('exam_questions'):
        stats[law]['done'] += 1
for law, s in sorted(stats.items()):
    pct = round(s['done']/s['total']*100) if s['total'] else 0
    print(f'{law}: {s[\"done\"]}/{s[\"total\"]} ({pct}%) — {s[\"total\"]-s[\"done\"]} restants')
"
```

**État au 6 mars 2026 :**

| Loi | Fait | Total | En attente |
|---|---|---|---|
| 1975 | 113 | 122 | 9 |
| 1968 | 3 | 93 | 90 |
| 1968b | 1 | 101 | 100 |
| 1976 | 0 | 23 | 23 |
| 1985 | 0 | 12 | 12 |
| 1989 | 0 | 46 | 46 |
| 1998 | 0 | 96 | 96 |
| 2001 | 0 | 41 | 41 |
| 2005 | 0 | 8 | 8 |
| 2006 | 1 | 51 | 50 |
| **Total** | **118** | **593** | **475** |

> La table est obsolète dès que la génération avance — utiliser le script
> ci-dessus pour avoir les chiffres en temps réel.

### Limite de taux Gemini (Free tier)

- 15 requêtes/minute → pause automatique de ~4 s entre articles
- Quota journalier : non épuisé en pratique avec ≤ 150 articles/jour
- En cas d'erreur 429 : le script attend automatiquement, puis reprend

---

## 2. Consulter les questions générées localement

### Compter les questions dans un fichier JSON d'article

```bash
cat data/processed/1975/articles/art-73.json | python3 -c "
import json,sys
d=json.load(sys.stdin)
qs=d.get('exam_questions',[])
print(f'{len(qs)} questions — {d[\"title_fr\"][:60]}')
for i,q in enumerate(qs,1):
    print(f'  {i}. [{q[\"difficulty\"]}] {q[\"text_fr\"][:70]}')
"
```

### Lister tous les articles avec leurs questions (résumé)

```bash
python3 -c "
import json
from pathlib import Path
for f in sorted(Path('data/processed').rglob('art-*.json')):
    d = json.loads(f.read_text())
    qs = d.get('exam_questions',[])
    if qs:
        law = f.parent.parent.name
        print(f'[{law}] {f.stem}: {len(qs)} questions — {d.get(\"title_fr\",\"\")[:50]}')
"
```

### Voir le contenu d'une question complète

```bash
python3 -c "
import json
from pathlib import Path
f = Path('data/processed/1975/articles/art-73.json')
d = json.loads(f.read_text())
for q in d['exam_questions']:
    print('─'*60)
    print('FR:', q['text_fr'])
    print('NL:', q['text_nl'])
    print('RU:', q['text_ru'])
    for opt in q['options']:
        mark = '✓' if opt['is_correct'] else '✗'
        print(f'  {mark} {opt[\"text_fr\"]}')
    print('Explication:', q.get('explanation_fr',''))
"
```

### Consulter les questions en BDD (locale)

```bash
venv/bin/python3 manage.py shell -c "
from apps.examens.models import Question
print('Total questions en BDD:', Question.objects.count())
for q in Question.objects.all()[:5]:
    print(f'  [{q.pk}] {q.text_fr[:60]}')
"
```

---

## 3. Importer les questions en base de données

### 3a. Import local (développement)

```bash
# Une seule loi
venv/bin/python3 scripts/pipeline/05_import.py --law-year 1975

# Toutes les lois
for law in 1975 1968 1968b 1976 1985 1989 1998 2001 2005 2006; do
    echo "=== Import loi $law ==="
    venv/bin/python3 scripts/pipeline/05_import.py --law-year $law
done

# Simuler sans modifier la BDD
venv/bin/python3 scripts/pipeline/05_import.py --law-year 1975 --dry-run
```

L'import est **idempotent** : relancer ne crée pas de doublons, il met à jour
les enregistrements existants (upsert par slug).

### 3b. Déployer sur le serveur de production

Le flux recommandé :

**Étape 1 — Pousser les fichiers JSON générés sur Git**

```bash
git add data/processed/
git commit -m "questions: add generated questions for laws 1975 1968 …"
git push
```

**Étape 2 — Sur le serveur : récupérer et importer**

```bash
# Connexion SSH
ssh user@mon-serveur

# Dans le dossier du projet
cd /srv/prava
git pull

# Activer le virtualenv de production
source venv/bin/activate

# Importer toutes les lois
for law in 1975 1968 1968b 1976 1985 1989 1998 2001 2005 2006; do
    python3 scripts/pipeline/05_import.py --law-year $law
done

# Vérifier le résultat
python3 manage.py shell -c "
from apps.examens.models import Question
print('Questions en prod:', Question.objects.count())
"
```

> Si le serveur utilise PostgreSQL, la commande `05_import.py` fonctionne
> sans modification — Django gère le backend automatiquement via `DATABASE_URL`.

### Vérification post-import

```bash
venv/bin/python3 manage.py shell -c "
from apps.examens.models import Question, ExamCategory
print('Questions :', Question.objects.count())
print('Catégories :', ExamCategory.objects.count())
"
```

---

## 4. Résumé des commandes essentielles

```bash
# Générer (toutes les lois, fond de tâche, résistant aux déconnexions)
nohup bash scripts/run_questions.sh >> logs/questions_$(date +%Y%m%d).log 2>&1 &

# Suivre le log
tail -f logs/questions_$(date +%Y%m%d).log

# Vérifier l'état des JSON
python3 -c "import json; from pathlib import Path; from collections import defaultdict; s=defaultdict(lambda:{'t':0,'d':0}); [s[f.parent.parent.name].__setitem__('t',s[f.parent.parent.name]['t']+1) or (s[f.parent.parent.name].__setitem__('d',s[f.parent.parent.name]['d']+1) if json.loads(f.read_text()).get('exam_questions') else None) for f in Path('data/processed').rglob('art-*.json')]; [print(f'{k}: {v[\"d\"]}/{v[\"t\"]}') for k,v in sorted(s.items())]"

# Importer en BDD locale
venv/bin/python3 scripts/pipeline/05_import.py --law-year 1975

# Vérifier la BDD
venv/bin/python3 manage.py shell -c "from apps.examens.models import Question; print(Question.objects.count(), 'questions')"
```
