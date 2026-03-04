# Génération Automatique d'Extraits PDF

## 🎯 Fonctionnalité

Le système génère **automatiquement** des extraits PDF lorsque tu sauvegardes un fichier dans l'admin Django.

---

## 📋 Comment Utiliser (Admin Django)

### Méthode 1 : Upload du fichier complet + configuration (RECOMMANDÉE)

1. **Aller dans Admin → Play Files → Ajouter fichier**

2. **Uploader le fichier PDF complet** (par exemple, 180 pages)

3. **File type** : Sélectionner `PDF` (sera automatiquement changé en `Extrait` après sauvegarde)

4. **Cocher "Is free" (Ce fichier est-il gratuit)**

5. **Définir les pages de l'extrait** :
   - `Excerpt start page` = `1` (ou page de début souhaitée)
   - `Excerpt end page` = `4` (ou page de fin souhaitée)

6. **Cliquer "Sauvegarder"**

7. **Résultat** : ✅ Le système :
   - Génère automatiquement un PDF de 4 pages (pages 1-4)
   - Remplace le fichier original par l'extrait
   - **Change automatiquement `file_type` de `PDF` → `Extrait`** 🔥
   - Affiche un message de confirmation vert

---

## 🔧 Comment ça Marche

### Code (`profiles/admin.py`)

```python
def save_model(self, request, obj, form, change):
    """Generate excerpt automatically when saving"""
    super().save_model(request, obj, form, change)

    # Conditions pour générer l'extrait
    if obj.is_free and obj.excerpt_start_page and obj.excerpt_end_page and obj.file:
        if obj.file.name.lower().endswith('.pdf'):
            # Génère l'extrait
            excerpt_content = create_pdf_excerpt(
                obj.file,
                obj.excerpt_start_page,
                obj.excerpt_end_page
            )

            # Remplace le fichier par l'extrait
            filename = os.path.basename(obj.file.name)
            obj.file.save(filename, excerpt_content, save=False)

            # CRITIQUE: Change file_type en 'extrait'
            obj.file_type = 'extrait'
            obj.save(update_fields=['file', 'file_type'])
```

**Changement clé** : `obj.file_type = 'extrait'` est automatiquement défini !

### Double Protection

1. **À la sauvegarde (Admin)** : Génère l'extrait automatiquement
2. **Au téléchargement (Frontend)** : Vérifie et régénère si nécessaire

Voir [profiles/views.py](../profiles/views.py#L372-L445) pour la logique de téléchargement.

---

## ⚠️ Important

### Ce qui est modifié automatiquement

Quand tu uploades un PDF de 180 pages avec `file_type='PDF'` et configures `is_free=True` + pages 1-4 :

- **AVANT sauvegarde** :
  - Fichier = 180 pages
  - `file_type` = `'pdf'`

- **APRÈS sauvegarde** :
  - Fichier = 4 pages ✅
  - `file_type` = `'extrait'` ✅ (changé automatiquement)

Le fichier original est **remplacé** par l'extrait ET le type est changé automatiquement.

### Si tu veux garder les deux fichiers

Tu dois créer **2 fichiers séparés** :

1. **Fichier 1** (complet, payant) :
   - Upload PDF 180 pages
   - `file_type` = `PDF`
   - `is_free` = `False` (décoché)
   - Pas de `excerpt_start_page/end_page`
   - **Reste 180 pages**

2. **Fichier 2** (extrait, gratuit) :
   - Upload le **même** PDF 180 pages
   - `file_type` = `PDF` (sera changé automatiquement)
   - `is_free` = `True` (coché) ✅
   - `excerpt_start_page` = `1`
   - `excerpt_end_page` = `4`
   - **Après sauvegarde** → devient automatiquement :
     - 4 pages ✅
     - `file_type = 'extrait'` ✅

---

## 🧪 Test de la Fonctionnalité

### Test Local

1. Aller dans Admin : `http://localhost:8000/admin/profiles/playfile/`

2. Ajouter un nouveau fichier :
   - Play = (choisir une pièce)
   - File = (upload un PDF de test)
   - Is free = ✅ Coché
   - Excerpt start page = `1`
   - Excerpt end page = `3`

3. Cliquer **Sauvegarder**

4. **Vérifier** :
   - Message vert : "✅ Extrait généré automatiquement (pages 1-3)"
   - Télécharger le fichier → doit avoir 3 pages

### Test en Production

Même processus, mais vérifier les logs Gunicorn/Django pour les erreurs.

---

## 🐛 Dépannage

### Erreur : "Extrait non généré"

**Causes possibles** :

1. **Le fichier n'est pas un PDF**
   - Vérifier extension : `.pdf`

2. **Pages invalides**
   - `start_page` > `end_page`
   - Pages inexistantes dans le PDF

3. **PDF corrompu ou protégé**
   - Impossible à lire avec PyPDF

**Solution** : Vérifier les logs Django pour message d'erreur précis

### Le fichier téléchargé est toujours complet

**Cause** : Sauvegarde n'a pas fonctionné correctement

**Solution** :
1. Re-éditer le fichier dans l'admin
2. Vérifier que `is_free=True` et pages sont définies
3. Cliquer "Sauvegarder" à nouveau
4. Le système va régénérer l'extrait

### Message d'erreur dans l'admin

Si tu vois un message rouge après sauvegarde :

```
❌ Erreur lors de la génération de l'extrait: [détails]
```

1. Copier le message d'erreur complet
2. Vérifier les logs Django
3. Le fichier est quand même sauvegardé (mais pas l'extrait)

---

## 📊 Workflow Complet

```
┌─────────────────────────────────────────────────────────┐
│ 1. UPLOAD dans Admin Django                            │
│    - Upload PDF complet (ex: 180 pages)                │
│    - Cocher "is_free"                                   │
│    - Définir start_page=1, end_page=4                   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 2. SAUVEGARDE (admin.py save_model)                     │
│    - Détecte : is_free=True + pages définies            │
│    - Génère extrait avec create_pdf_excerpt()           │
│    - Remplace fichier par extrait                       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 3. STOCKAGE                                             │
│    - Fichier en DB = Extrait 4 pages ✅                 │
│    - Utilisateur télécharge → reçoit 4 pages            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 4. TÉLÉCHARGEMENT (views.py download_play_file)         │
│    - Vérifie nombre de pages réel vs attendu            │
│    - Si mismatch → régénère l'extrait                   │
│    - Double protection ✅                                │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ Checklist Avant Déploiement

- [x] Code ajouté dans `profiles/admin.py` (méthode `save_model`)
- [ ] Test en local avec fichier PDF réel
- [ ] Vérifier message de confirmation dans l'admin
- [ ] Télécharger fichier généré et compter pages
- [ ] Tester avec PDF protégé (doit afficher erreur propre)
- [ ] Commit et push vers production
- [ ] Tester en production avec fichier réel

---

## 📝 Liens

- Code Admin : [profiles/admin.py](../profiles/admin.py#L475-L530)
- Code Download : [profiles/views.py](../profiles/views.py#L372-L445)
- Utilitaire PDF : [utils/pdf_utils.py](../utils/pdf_utils.py)

---

**Dernière mise à jour** : 27 janvier 2026
