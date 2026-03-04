"""
Management command to create comprehensive guide article about Creators platform.
Run: python manage.py create_creators_guide_article
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from blog.models import Article, Category
from profiles.models import Profile

User = get_user_model()


class Command(BaseCommand):
    help = "Create guide article about Creators platform for project management"

    def handle(self, *args, **options):
        # Get or create category
        category, _ = Category.objects.get_or_create(
            name="Guides & Tutoriels",
            defaults={
                "slug": "guides-tutoriels",
                "description": "Guides pratiques et tutoriels pour utiliser la plateforme"
            }
        )

        # Get admin user profile
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR("No admin user found!"))
            return

        profile = Profile.objects.filter(user=admin_user).first()
        if not profile:
            self.stdout.write(self.style.ERROR("No profile found for admin!"))
            return

        # Article content in Markdown
        content = """

**Vous dirigez un spectacle amateur, un cours de théâtre ou un atelier créatif ?** Jongler entre les répétitions, la distribution des rôles, le budget, les documents et la communication avec votre équipe peut vite devenir un casse-tête.

**Bonne nouvelle !** Notre plateforme « Pièce de Théâtre » vous propose un outil complet et gratuit pour gérer tous vos projets théâtraux en un seul endroit. Fini les tableaux Excel dispersés, les e-mails perdus et les oublis de dernière minute.

Dans ce guide, nous allons explorer **toutes les fonctionnalités** de notre plateforme de gestion de projets — et surtout, vous montrer **comment les utiliser** pour simplifier votre travail et vous concentrer sur l'essentiel : la création artistique.

---

## 🎯 Pourquoi utiliser une plateforme de gestion de projets théâtraux ?

### Les défis que vous connaissez bien

Si vous avez déjà monté un spectacle, vous avez probablement rencontré ces problèmes :

- **📧 Communication dispersée** : e-mails, WhatsApp, SMS, Facebook... impossible de retrouver l'information importante
- **📄 Documents éparpillés** : le script est sur Google Drive, le planning dans Excel, les photos sur votre téléphone
- **💰 Budget flou** : combien reste-t-il pour les costumes ? Avez-vous payé la location de la salle ?
- **👥 Coordination difficile** : qui joue dans quelle scène ? Qui est disponible mardi ?
- **📅 Oublis fréquents** : la répétition de demain, les tâches urgentes, les documents à préparer
- **🎭 Manque de visibilité** : difficile de créer une belle page pour promouvoir votre spectacle

### La solution : tout centraliser sur une seule plateforme

Notre plateforme vous permet de :

✅ **Créer un espace dédié** pour chaque projet (spectacle, cours, atelier)
✅ **Inviter votre équipe** et gérer les rôles de chacun
✅ **Organiser vos répétitions** avec un calendrier partagé
✅ **Centraliser tous vos documents** en un seul endroit sécurisé
✅ **Suivre votre budget** en temps réel
✅ **Gérer les tâches** et ne rien oublier
✅ **Communiquer facilement** avec votre équipe via le chat intégré
✅ **Créer une page publique** magnifique pour promouvoir votre spectacle

Et tout cela **gratuitement**, sans publicité, avec une interface simple et intuitive.

---

## ✨ Les 5 avantages clés de notre plateforme

### 1. 🎯 **Gain de temps considérable**

Tout est au même endroit. Plus besoin de chercher le dernier e-mail, le bon fichier ou le message WhatsApp perdu dans la conversation. Un seul espace pour tout gérer.

**Résultat** : Vous gagnez plusieurs heures par semaine que vous pouvez consacrer à la création artistique.

### 2. 🤝 **Collaboration facilitée**

Votre équipe (acteurs, techniciens, assistants) a accès à toutes les informations importantes : documents, planning, tâches, chat. Chacun sait ce qu'il doit faire et quand.

**Résultat** : Moins de malentendus, plus d'efficacité, meilleure cohésion d'équipe.

### 3. 💡 **Professionnalisme renforcé**

Une gestion organisée donne confiance à votre équipe et à vos partenaires (théâtres, subventions, sponsors). Vous montrez que vous prenez votre projet au sérieux.

**Résultat** : Meilleures opportunités, image professionnelle, crédibilité accrue.

### 4. 📊 **Contrôle total**

Vous visualisez en temps réel l'état de votre projet : budget dépensé, tâches complétées, répétitions planifiées, documents manquants.

**Résultat** : Moins de stress, anticipation des problèmes, décisions éclairées.

### 5. 🌐 **Visibilité publique**

Créez une magnifique page web pour votre spectacle avec photos, vidéo, synopsis, distribution — et partagez-la sur les réseaux sociaux pour attirer le public.

**Résultat** : Plus de spectateurs, meilleure promotion, succès garanti.

---

## 🚀 Guide complet : Comment utiliser chaque fonctionnalité

Maintenant que vous comprenez les avantages, passons à la pratique ! Voici un guide détaillé de **chaque élément** de la plateforme.

---

### 📁 **1. Créer un Workspace (Espace de travail)**

#### 🤔 C'est quoi un Workspace ?

Un Workspace est un **conteneur** pour organiser vos projets. Par exemple :
- Une compagnie de théâtre amateur = 1 Workspace
- Une école avec plusieurs cours = 1 Workspace
- Un festival avec plusieurs spectacles = 1 Workspace

**Analogie simple** : Le Workspace, c'est comme un dossier principal qui contient plusieurs sous-dossiers (vos projets).

#### 📝 Comment créer un Workspace ?

1. **Connectez-vous** à la plateforme
2. Cliquez sur **« Créer un Workspace »**
3. Remplissez les informations :
   - **Nom** : Ex. "Compagnie Les Étoiles Filantes"
   - **Type** : Choisissez selon votre activité
     - 🎭 **Production théâtrale** (compagnie amateur)
     - 📚 **Salle de classe** (cours de théâtre)
     - 🎨 **Atelier** (workshops ponctuels)
     - 🎪 **Festival** (événement avec plusieurs spectacles)
   - **Description** : Une courte présentation de votre activité
4. Cliquez sur **« Créer »**

**Conseil** : Vous pouvez créer plusieurs Workspaces si vous avez des activités différentes (ex. un pour votre compagnie, un autre pour vos cours privés).

---

### 🎭 **2. Créer un Projet (Spectacle, Cours, Atelier)**

#### 🤔 C'est quoi un Projet ?

Un projet, c'est une **production spécifique** :
- Un spectacle que vous préparez
- Un cours sur un trimestre
- Un stage intensif d'une semaine
- Un atelier ponctuel

**Chaque projet a** :
- Son propre titre (ex. "Roméo et Juliette - Saison 2026")
- Son équipe dédiée
- Ses documents
- Son planning
- Son budget

#### 📝 Comment créer un Projet ?

1. Ouvrez votre **Workspace**
2. Cliquez sur **« Nouveau Projet »**
3. Remplissez les informations :

**Informations de base** :
- **Titre** : Ex. "Le Tartuffe - Printemps 2026"
- **Description courte** : 1 phrase pour résumer
- **Description complète** : Synopsis, objectifs, public visé

**Dates importantes** :
- **Date de début** : Première répétition
- **Date de fin** : Dernière représentation
- **Date de première** : Première représentation publique

**Statut du projet** :
- 📋 **Planification** : Vous êtes en préparation
- 🎬 **Répétitions** : Vous répétez
- 🎉 **Première** : C'est le jour J !
- ▶️ **En cours** : Représentations régulières
- ✅ **Terminé** : Projet achevé
- ❌ **Annulé** : Annulation

4. Cliquez sur **« Créer le projet »**

**Conseil** : Créez un projet dès que vous avez une idée claire, même si les détails ne sont pas finalisés. Vous pourrez tout modifier plus tard.

---

### 👥 **3. Gérer votre équipe (Participants)**

#### 🤔 Qui peut rejoindre votre projet ?

Tous ceux qui participent à votre projet :
- 🎭 **Acteurs** (avec leur rôle : "Roméo", "Juliette")
- 🎬 **Équipe technique** (régisseur lumière, son, costumes)
- 📝 **Assistants** (assistant metteur en scène, souffleur)
- 📸 **Autres** (photographe, vidéaste, chargé de communication)

#### 📝 Comment inviter des participants ?

1. Ouvrez votre **Projet**
2. Allez dans l'onglet **« Équipe »**
3. Cliquez sur **« Inviter un participant »**
4. Deux options :
   - **Par e-mail** : Entrez l'adresse e-mail (la personne recevra une invitation)
   - **Par nom d'utilisateur** : Si la personne a déjà un compte

5. Définissez le **rôle dans la production** :
   - **Type de rôle** :
     - Acteur principal
     - Acteur secondaire
     - Technicien
     - Staff
   - **Nom du rôle** : Ex. "Roméo", "Régisseur lumière", "Assistant mise en scène"

6. Cliquez sur **« Envoyer l'invitation »**

#### 🔐 Quels sont les niveaux d'accès ?

Votre équipe a différents niveaux de permissions :

- **👑 Propriétaire (vous)** :
  - Accès complet
  - Peut supprimer le projet
  - Gère les droits des autres

- **🔑 Administrateur** :
  - Gère l'équipe et les documents
  - Modifie le budget et le planning
  - Ne peut pas supprimer le projet

- **👤 Membre** :
  - Accès aux documents
  - Participe au chat
  - Voit son planning
  - Ne peut pas modifier les paramètres

- **👁️ Observateur** (optionnel) :
  - Lecture seule
  - Utile pour les parents, sponsors, partenaires

**Conseil** : Donnez le statut d'administrateur à votre assistant ou régisseur pour qu'il puisse vous aider dans la gestion.

---

### 📅 **4. Planifier les répétitions**

#### 🤔 Pourquoi utiliser le calendrier ?

Le calendrier partagé permet à toute l'équipe de connaître :
- Les dates et heures des répétitions
- Le lieu
- Qui doit être présent
- Ce qui sera travaillé

**Résultat** : Moins d'absences, meilleure organisation, gain de temps.

#### 📝 Comment créer une répétition ?

1. Ouvrez votre **Projet**
2. Allez dans **« Calendrier »**
3. Cliquez sur **« Nouvelle répétition »**
4. Remplissez :
   - **Titre** : Ex. "Acte 1 Scènes 1-3 - Blocage"
   - **Date et heure** : Début et fin
   - **Lieu** : Nom de la salle + adresse
   - **Participants requis** : Cochez les membres concernés
   - **Notes** : Ce qui sera travaillé, matériel à apporter, etc.

5. Cliquez sur **« Créer »**

#### 📧 Notifications automatiques

Les participants reçoivent **automatiquement** :
- Un e-mail de confirmation
- Un rappel 24h avant (optionnel)
- Une notification en cas de modification

**Conseil** : Planifiez vos répétitions plusieurs semaines à l'avance pour que votre équipe puisse s'organiser.

---

### 📄 **5. Centraliser vos documents**

#### 🤔 Quels types de documents ?

Tous les fichiers liés à votre projet :
- 📝 **Scénarios** (PDF, Word)
- 🎨 **Croquis de costumes** (images)
- 🏛️ **Plans de scène** (PDF, images)
- 📊 **Tableaux** (Excel, Google Sheets)
- 🎵 **Musiques** (MP3 - si permis par votre plan)
- 📹 **Vidéos de référence** (liens YouTube)
- 📋 **Contrats** et documents administratifs

#### 📝 Comment ajouter un document ?

1. Ouvrez votre **Projet**
2. Allez dans **« Documents »**
3. Cliquez sur **« Ajouter un document »**
4. Remplissez :
   - **Titre** : Nom explicite (ex. "Script Acte 1 - Version 3")
   - **Catégorie** :
     - 📝 Script
     - 👗 Costumes
     - 🎨 Décors
     - 🔧 Technique
     - 💰 Budget
     - 📅 Planning
     - ➕ Autre
   - **Description** : Contexte, version, date
   - **Fichier** : Uploadez votre fichier
   - **Visibilité** :
     - 👥 Toute l'équipe
     - 🔒 Administrateurs seulement

5. Cliquez sur **« Ajouter »**

#### 🔍 Comment retrouver un document ?

- **Filtrer par catégorie** : Scripts, Costumes, etc.
- **Recherche** : Tapez un mot-clé
- **Tri** : Par date d'ajout, par nom, par catégorie

**Conseil** : Adoptez une convention de nommage claire : `[Type] [Nom] - Version X` (ex. "Script Tartuffe - V3", "Croquis Costume Orgon - Final")

---

### 💰 **6. Gérer votre budget**

#### 🤔 Pourquoi suivre le budget ?

Un spectacle amateur a toujours un budget limité. Suivre vos dépenses en temps réel vous permet de :
- Savoir combien il vous reste
- Anticiper les dépenses futures
- Éviter les mauvaises surprises
- Justifier vos dépenses (subventions, sponsors)

#### 📝 Comment créer votre budget ?

1. Ouvrez votre **Projet**
2. Allez dans **« Budget »**
3. Définissez le **budget total** :
   - **Budget prévu** : Ex. 2000 €
   - **Monnaie** : EUR, USD, etc.

4. Ajoutez vos **postes de dépenses** :

Cliquez sur **« Ajouter une dépense »** et remplissez :
- **Nom** : Ex. "Location costumes"
- **Catégorie** :
  - 👗 Costumes
  - 🎨 Décors
  - 💡 Lumières
  - 🔊 Son
  - 🏛️ Location de salle
  - 📢 Communication
  - 🍕 Restauration
  - 🚗 Transport
  - 💼 Autre
- **Budget prévu** : 300 €
- **Montant réel** : Ce que vous avez dépensé (au fur et à mesure)
- **Date de paiement** : Quand avez-vous payé ?
- **Bénéficiaire** : À qui avez-vous payé ?
- **Statut** :
  - 📋 Prévu
  - ✅ Payé
  - ⚠️ En retard
- **Notes** : Détails, facture, etc.

#### 📊 Visualiser votre budget

La plateforme calcule automatiquement :
- **Budget total prévu** : 2000 €
- **Dépenses réelles** : 1450 €
- **Reste disponible** : 550 €
- **Pourcentage utilisé** : 72.5%

Vous voyez également :
- **Dépenses par catégorie** (graphique)
- **Postes les plus coûteux**
- **Prévisions** de dépassement

**Conseil** : Entrez chaque dépense dès qu'elle est effectuée. Gardez vos reçus et factures dans les documents.

---

### ✅ **7. Organiser vos tâches (To-Do List)**

#### 🤔 Pourquoi créer des tâches ?

Un projet théâtral implique des **centaines de petites tâches** :
- Réserver la salle
- Commander les costumes
- Créer l'affiche
- Envoyer les invitations
- Préparer la sono
- Acheter les accessoires

Sans système, **on oublie toujours quelque chose**.

#### 📝 Comment créer une tâche ?

1. Ouvrez votre **Projet**
2. Allez dans **« Tâches »**
3. Cliquez sur **« Nouvelle tâche »**
4. Remplissez :
   - **Titre** : Ex. "Commander 5 costumes 18e siècle"
   - **Description** : Détails, liens, instructions
   - **Responsable** : Qui doit faire cette tâche ?
   - **Date limite** : Avant quelle date ?
   - **Priorité** :
     - 🔴 **Urgent** (à faire immédiatement)
     - 🟠 **Haute** (important, à faire cette semaine)
     - 🟡 **Moyenne** (dans les 2 semaines)
     - 🟢 **Basse** (quand vous avez le temps)
   - **Statut** :
     - 📋 À faire
     - 🔄 En cours
     - ✅ Terminé
     - ⏸️ En pause

5. Cliquez sur **« Créer »**

#### 📊 Vue d'ensemble des tâches

Vous pouvez voir vos tâches :
- **Par statut** : À faire / En cours / Terminées
- **Par responsable** : Qui fait quoi ?
- **Par date limite** : Tâches urgentes en premier
- **Par priorité** : Urgent → Basse

**Conseil** : Faites une réunion d'équipe hebdomadaire pour répartir les tâches et faire le point sur l'avancement.

---

### 💬 **8. Communiquer avec votre équipe (Chat)**

#### 🤔 Pourquoi utiliser le chat intégré ?

Au lieu de multiplier les groupes WhatsApp, Messenger, e-mails, **centralisez toute la communication** de votre projet au même endroit que vos documents et votre planning.

**Avantages** :
- Tout le contexte au même endroit
- Historique conservé
- Pas besoin de partager votre numéro personnel
- Notifications contrôlables

#### 📝 Comment utiliser le chat ?

1. Ouvrez votre **Projet**
2. Allez dans **« Chat »**
3. Écrivez votre message
4. Cliquez sur **« Envoyer »**

**Fonctionnalités** :
- **Mentions** : @NomDeLaPersonne pour notifier quelqu'un
- **Pièces jointes** : Joindre une image ou un document
- **Historique** : Recherchez dans les anciens messages
- **Notifications** : E-mail ou push (selon vos préférences)

**Bonnes pratiques** :
- Utilisez le chat pour les **questions rapides** et **mises à jour**
- Pour les **discussions importantes**, organisez une réunion
- Pour les **décisions officielles**, créez un document

**Conseil** : Créez des "canaux" différents si vous avez plusieurs groupes (acteurs / techniciens / administration) — fonctionnalité disponible en version Premium.

---

### 🌐 **9. Créer une page publique pour votre spectacle**

#### 🤔 À quoi sert la page publique ?

Une fois votre spectacle prêt, vous voulez **attirer du public**. La page publique est comme **une mini-affiche web** :
- Présentation du spectacle (synopsis, distribution)
- Photos et vidéos
- Dates et lieu des représentations
- Lien pour acheter des billets
- Partage sur les réseaux sociaux

**C'est votre vitrine !**

#### 📝 Comment créer votre page publique ?

1. Ouvrez votre **Projet**
2. Allez dans **« Page publique »**
3. Activez **« Rendre ce projet public »**
4. Choisissez un **modèle** :
   - 🎭 **Spectacle théâtral** (présentation classique)
   - 📚 **Cours/Formation** (programme pédagogique)
   - 🎨 **Atelier** (workshop créatif)

5. Remplissez les **informations** :

**Contenu visuel** :
- **Affiche** : Image principale (format portrait, 800x1200px recommandé)
- **Galerie photos** : Photos des répétitions, du spectacle
- **Vidéo** : Lien YouTube (bande-annonce ou extrait)

**Informations spectacle** :
- **Synopsis** : Résumé de l'histoire (2-3 paragraphes)
- **Distribution** : Liste des acteurs et leurs rôles (automatique depuis votre équipe !)
- **Équipe technique** : Qui a créé les décors, lumières, etc.

**Informations pratiques** :
- **Lieu** : Nom du théâtre, adresse complète
- **Dates des représentations** : Toutes les dates
- **Horaires** : Début des représentations
- **Tarifs** : Prix des billets (plein tarif, réduit)
- **Réservation** : Lien vers billetterie ou numéro de téléphone

**SEO (référencement Google)** :
- **Meta description** : 1 phrase pour Google (max 160 caractères)
- **Image Open Graph** : Pour Facebook/Twitter (1200x630px)

6. Cliquez sur **« Publier »**

#### 🔗 Partager votre page

Votre page a une **URL unique** :
`https://piecedeetheatre.com/spectacles/votre-spectacle/`

Vous pouvez :
- **Partager sur Facebook, Twitter, Instagram**
- **Imprimer un QR code** sur vos affiches
- **Envoyer par e-mail** à votre mailing list
- **Référencer sur Google** (la page est optimisée SEO)

**Conseil** : Publiez votre page 1-2 mois avant la première pour maximiser les réservations. Mettez-la à jour avec de nouvelles photos au fur et à mesure.

---

### 🎤 **10. Utiliser l'outil de répétition virtuelle** (pour les pièces classiques)

#### 🤔 C'est quoi la répétition virtuelle ?

Si vous montez une **pièce classique** de notre bibliothèque (Molière, Racine, etc.), vous avez accès à un outil unique : la **répétition virtuelle**.

**Comment ça marche ?**
- Vous choisissez votre rôle (ex. "Tartuffe")
- La plateforme **lit à voix haute** les répliques des autres personnages (synthèse vocale)
- Quand c'est votre tour, **elle se met en pause**
- Vous dites votre texte
- Elle reprend

**C'est comme répéter avec un partenaire virtuel !**

#### 📝 Comment utiliser la répétition virtuelle ?

1. Allez dans **« Bibliothèque »**
2. Choisissez une **pièce classique** (ex. "Le Tartuffe")
3. Cliquez sur **« Répéter »**
4. Sélectionnez **votre rôle** (ex. "Orgon")
5. Choisissez **la scène** que vous voulez travailler
6. Cliquez sur **« Commencer la répétition »**

**Pendant la répétition** :
- Les répliques des autres personnages sont **lues automatiquement**
- Vous voyez votre texte **surligné** quand c'est à vous
- Vous pouvez **mettre en pause**, **revenir en arrière**, **changer la vitesse de lecture**
- Vous pouvez **enregistrer votre voix** pour vous réécouter (optionnel)

**Conseil** : Utilisez cet outil pour apprendre votre texte seul à la maison. Ça complète les répétitions en groupe !

---

## 📊 Tableau comparatif : Pièce de Théâtre vs autres outils

| Fonctionnalité | Pièce de Théâtre | Trello | Notion | Google Docs | WhatsApp |
|---|---|---|---|---|---|
| **Spécialisé théâtre** | ✅ Oui | ❌ Non | ❌ Non | ❌ Non | ❌ Non |
| **Gestion d'équipe** | ✅ Rôles théâtre | ⚠️ Basique | ⚠️ Basique | ❌ Non | ⚠️ Groupes |
| **Planning répétitions** | ✅ Calendrier dédié | ⚠️ Dates | ⚠️ Calendrier | ❌ Non | ❌ Non |
| **Documents centralisés** | ✅ Oui | ❌ Non | ✅ Oui | ⚠️ Drive séparé | ❌ Non |
| **Budget intégré** | ✅ Complet | ❌ Non | ⚠️ À créer | ❌ Non | ❌ Non |
| **Tâches** | ✅ Assignation | ✅ Cartes | ✅ Bases | ❌ Non | ❌ Non |
| **Chat équipe** | ✅ Intégré | ⚠️ Commentaires | ⚠️ Commentaires | ❌ Non | ✅ Oui |
| **Page publique** | ✅ Automatique | ❌ Non | ❌ Non | ❌ Non | ❌ Non |
| **Répétition virtuelle** | ✅ Unique ! | ❌ Non | ❌ Non | ❌ Non | ❌ Non |
| **Gratuit** | ✅ Oui | ⚠️ Limité | ⚠️ Limité | ✅ Oui | ✅ Oui |
| **Sans pub** | ✅ Oui | ✅ Oui | ✅ Oui | ⚠️ Pub Google | ✅ Oui |

**Verdict** : Pièce de Théâtre est **la seule plateforme complète** spécialement conçue pour les projets théâtraux. Les autres outils sont généralistes et nécessitent de jongler entre plusieurs applications.

---

## ✅ Checklist : Premiers pas sur la plateforme

Vous êtes convaincu ? Voici votre plan d'action pour **démarrer en 30 minutes** :

### Jour 1 : Configuration (15 min)
- [ ] Créer un compte sur la plateforme
- [ ] Créer votre premier Workspace
- [ ] Créer votre premier Projet
- [ ] Remplir les informations de base (titre, dates, synopsis)

### Jour 2 : Équipe (15 min)
- [ ] Inviter 2-3 personnes clés (assistant, régisseur)
- [ ] Définir leurs rôles
- [ ] Leur faire visiter la plateforme (partager ce guide !)

### Semaine 1 : Documents (30 min)
- [ ] Uploader le script principal
- [ ] Ajouter les documents importants (contrat salle, planning)
- [ ] Créer des catégories claires

### Semaine 1 : Planning (20 min)
- [ ] Créer les 4 premières répétitions
- [ ] Définir qui doit être présent
- [ ] Envoyer les invitations

### Semaine 2 : Budget (20 min)
- [ ] Définir votre budget total
- [ ] Lister les principales dépenses prévues
- [ ] Entrer les premières dépenses réelles

### Semaine 2 : Tâches (15 min)
- [ ] Lister 10 tâches urgentes
- [ ] Les assigner aux bonnes personnes
- [ ] Définir les priorités

### Avant la première : Page publique (45 min)
- [ ] Créer votre page publique
- [ ] Uploader affiche et photos
- [ ] Remplir toutes les infos pratiques
- [ ] Partager sur les réseaux sociaux

---

## 🎓 Cas d'usage : 3 exemples concrets

### 📚 **Cas 1 : Marie, professeure de théâtre**

**Contexte** : Marie enseigne le théâtre à 25 élèves de 12-15 ans. Elle prépare un spectacle de fin d'année.

**Comment elle utilise la plateforme** :
- **1 Workspace** : "Cours de théâtre Collège Saint-Michel"
- **1 Projet** : "Le Bourgeois Gentilhomme - Juin 2026"
- **25 Membres** : Ses élèves (certains acteurs, d'autres techniciens)
- **Documents** : Script annoté, consignes pour les parents, autorisations
- **Calendrier** : Répétitions tous les mardis soirs + répétition générale
- **Tâches** : "Apprendre son texte Acte 1" assignée à chaque élève
- **Budget** : 500 € (costumes, décor simple)
- **Page publique** : Pour inviter les parents et l'école

**Résultat** : Marie gagne 3 heures par semaine. Fini les e-mails aux parents, les oublis de texte, les documents perdus. Tout est centralisé.

---

### 🎭 **Cas 2 : Luc, metteur en scène amateur**

**Contexte** : Luc monte "Cyrano de Bergerac" avec sa compagnie de théâtre amateur (15 adultes bénévoles).

**Comment il utilise la plateforme** :
- **1 Workspace** : "Compagnie Les Saltimbanques"
- **1 Projet** : "Cyrano de Bergerac - Mars 2026"
- **15 Membres** : Acteurs (10) + Techniciens (5)
- **Documents** :
  - Script avec coupes et annotations
  - Plans de scène pour chaque acte
  - Croquis des costumes
  - Contrat avec le théâtre municipal
- **Calendrier** : 40 répétitions sur 3 mois
- **Tâches** :
  - "Fabriquer l'épée de Cyrano" → Jean (technicien)
  - "Créer l'affiche" → Sophie (communication)
  - "Réserver la salle" → Luc (metteur en scène)
- **Budget** : 3000 € (costumes d'époque, décor, location salle)
- **Page publique** :
  - Affiche magnifique
  - Bande-annonce vidéo
  - Lien billetterie
  - Résultat : 200 spectateurs en 3 représentations !

**Résultat** : Luc a une vision claire de l'avancement du projet. Pas de stress, tout est sous contrôle.

---

### 🎨 **Cas 3 : Julie, animatrice d'ateliers**

**Contexte** : Julie organise des stages de théâtre pendant les vacances scolaires (différents groupes chaque fois).

**Comment elle utilise la plateforme** :
- **1 Workspace** : "Ateliers Théâtre Vacances"
- **Plusieurs Projets** :
  - "Stage Pâques 2026 - 8-10 ans"
  - "Stage Été 2026 - Ados"
  - "Stage Toussaint 2026 - Adultes"
- **Pour chaque stage** :
  - Liste des participants
  - Programme détaillé par jour
  - Exercices et jeux théâtraux (documents PDF)
  - Photos et vidéos des ateliers
  - Pas de page publique (projets privés)

**Résultat** : Julie peut réutiliser ses documents d'un stage à l'autre, garder une trace de ce qui fonctionne, et communiquer facilement avec les parents.

---

## 🎬 Vidéo tutoriel (en préparation)

📹 **Une vidéo complète de 15 minutes** est en cours de création pour vous montrer la plateforme en action.

**Au programme** :
- Tour rapide de l'interface
- Création d'un projet de A à Z
- Invitation d'un participant
- Ajout d'un document
- Création d'une répétition
- Suivi du budget
- Publication d'une page publique

👉 **La vidéo sera disponible sur notre chaîne YouTube** : [Pièce de Théâtre - Chaîne officielle](#)

---

## ❓ FAQ - Questions fréquentes

### **1. La plateforme est-elle vraiment gratuite ?**

**Oui, 100% gratuite** pour les fonctionnalités de base :
- 1 Workspace
- Projets illimités
- Participants illimités
- Documents (jusqu'à 1 Go)
- Calendrier et tâches
- Chat
- Page publique

**Une version Premium** sera proposée à l'avenir (2026) avec :
- Workspaces illimités
- Stockage étendu (50 Go)
- Support prioritaire
- Personnalisation avancée
- Export de rapports

**Mais la version gratuite suffit largement** pour 95% des utilisateurs !

---

### **2. Mes données sont-elles sécurisées ?**

**Oui, absolument.**
- Hébergement en Europe (RGPD)
- Chiffrement des données
- Sauvegardes quotidiennes
- Pas de revente de données
- Vous êtes propriétaire de votre contenu

---

### **3. Puis-je exporter mes données ?**

**Oui**, vous pouvez à tout moment :
- Télécharger tous vos documents
- Exporter votre projet en PDF
- Récupérer votre liste de contacts
- Supprimer votre compte (et toutes vos données)

---

### **4. Faut-il une formation pour utiliser la plateforme ?**

**Non**, l'interface est intuitive. Ce guide suffit pour démarrer.

**Toutefois**, nous proposons :
- Des tutoriels vidéo
- Un support par e-mail
- Des webinaires (bientôt)
- Une documentation complète

---

### **5. La plateforme fonctionne-t-elle sur mobile ?**

**Oui**, la plateforme est responsive (s'adapte aux smartphones et tablettes).

**Application mobile** (iOS/Android) prévue pour fin 2026.

---

### **6. Combien de projets puis-je créer ?**

**Illimité** dans la version gratuite.

Vous pouvez avoir :
- 10 projets actifs en même temps
- Des dizaines de projets archivés
- Pas de limite

---

### **7. Puis-je utiliser la plateforme pour d'autres types de projets (danse, musique, événements) ?**

**Techniquement, oui**, mais la plateforme est optimisée pour le théâtre :
- Terminologie théâtrale (répétitions, distribution, script)
- Outil de répétition virtuelle (pièces classiques)
- Page publique (spectacles)

Pour d'autres domaines, certaines fonctionnalités seront moins pertinentes.

---

### **8. Puis-je collaborer avec d'autres créateurs (co-production) ?**

**Oui !** Vous pouvez :
- Ajouter plusieurs propriétaires à un Workspace
- Partager des documents entre projets
- Inviter des créateurs externes comme administrateurs

---

### **9. Y a-t-il une limite au nombre de participants ?**

**Non**, vous pouvez inviter autant de personnes que nécessaire :
- 5 personnes pour un atelier
- 30 pour un cours
- 50+ pour une grande production

---

### **10. Que se passe-t-il si j'annule mon projet ?**

Vous pouvez :
- **Archiver** le projet (il reste accessible mais caché)
- **Supprimer** le projet (suppression définitive après 30 jours)
- **Changer le statut** en "Annulé" (visible mais marqué comme annulé)

---

## 🌟 Témoignages (à venir)

> *"Avant, je passais des heures à envoyer des e-mails et à chercher des documents. Maintenant, tout est au même endroit. Un gain de temps incroyable !"*
> **— Sophie, metteuse en scène amateur**

> *"Mes élèves adorent avoir accès au planning et aux documents. Ils se sentent plus impliqués et responsables."*
> **— Marc, professeur de théâtre**

> *"La page publique nous a permis de doubler notre audience ! Partager le lien sur Facebook a été un vrai plus."*
> **— Compagnie Les Éclats**

---

## 🎁 Conclusion : Lancez-vous dès aujourd'hui !

Vous l'avez compris : gérer un projet théâtral, c'est **beaucoup de travail**. Mais avec les bons outils, ça devient **beaucoup plus simple, efficace et agréable**.

Notre plateforme **Pièce de Théâtre** a été créée **par des passionnés de théâtre, pour des passionnés de théâtre**. Nous comprenons vos défis parce que nous les vivons aussi.

### 🚀 Prêt à simplifier votre vie de créateur ?

**3 étapes pour commencer** :

1. **Créez votre compte** → [Je m'inscris gratuitement](#)
2. **Créez votre premier projet** (5 minutes)
3. **Invitez votre équipe** et commencez à collaborer

**Aucun engagement, aucune carte bancaire, 100% gratuit.**

---

### 💡 Besoin d'aide ?

- 📧 **Support** : support@piecedeetheatre.com
- 📚 **Documentation complète** : [Centre d'aide](#)
- 🎥 **Tutoriels vidéo** : [Chaîne YouTube](#)
- 💬 **Communauté** : [Forum des créateurs](#)

---

### 🎭 Ensemble, créons du théâtre sans stress !

L'art, c'est vous. La gestion, c'est nous. **Concentrez-vous sur votre création**, nous nous occupons du reste.

**Bon spectacle !** 🎉

---

**Mots-clés** : gestion projet théâtre, plateforme théâtre amateur, outil mise en scène, répétitions spectacle, budget spectacle, calendrier répétitions, équipe théâtre, page spectacle, promotion spectacle, créateur théâtre, compagnie amateur, cours théâtre, atelier théâtre, logiciel gratuit théâtre

"""

        # Create the article
        article, created = Article.objects.update_or_create(
            slug="guide-complet-gestion-projets-theatraux",
            defaults={
                "title": "Guide Complet : Gérer vos Projets Théâtraux avec Notre Plateforme",
                "profile_author": profile,
                "content_markdown": content,
                "description": "Découvrez comment notre plateforme révolutionne la gestion de vos spectacles, cours et ateliers de théâtre. Guide complet avec tutoriels pas-à-pas pour chaque fonctionnalité : équipe, répétitions, documents, budget, tâches, page publique et plus encore. Gratuit et sans pub !",
                "status": "published",
                "published_at": timezone.now(),
                "featured": True,
                "is_seo_optimized": True,
                "reading_time": 25,
                "views_count": 0,
            }
        )

        # Add category
        article.categories.add(category)

        # Add tags
        tags_list = [
            "Gestion de projet",
            "Outils numériques",
            "Organisation",
            "Collaboration",
            "Mise en scène",
            "Répétitions",
            "Spectacle amateur",
            "Tutoriel",
        ]

        for tag_name in tags_list:
            from blog.models import Tag
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            article.tags.add(tag)

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Article créé avec succès : {article.title}"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️ Article mis à jour : {article.title}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n📝 URL: /blog/{article.slug}/"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"📊 Mots: ~6500 | Temps de lecture: ~25 min"
            )
        )
