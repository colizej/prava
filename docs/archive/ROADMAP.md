# PRAVA.be — Roadmap de développement

> Créé le 27 février 2026
> Dernière mise à jour : 27 février 2026

---

## État actuel du projet

### Ce qui est fait ✅

| Composant | Détails |
|-----------|---------|
| **Réglementation** | 122 articles du Code de la route importés, 520 images inline, 5 Titres (catégories) |
| **Page d'accueil** | 5 cartes catégories + 9 cartes thèmes (2 internes, 7 externes) + bannière panneaux |
| **CSS/UI** | Tailwind v4.2.1, notifications stylisées, galerie de panneaux, tables zebra |
| **Liens internes** | 31 liens smart-routing dans les notifications d'articles |
| **Examens app** | Models (Question, AnswerOption, TestAttempt, ExamCategory), views, quiz UI Alpine.js — **tout prêt** |
| **Accounts app** | UserProfile, DailyQuota, auth views — **prêt** |
| **Blog app** | Models, views, sitemaps — **1 article** |
| **Infra** | Django 5.x, Python 3.14, SQLite3, Git sur GitHub |

### Ce qui manque ❌

| Composant | Problème |
|-----------|----------|
| **Examens** | **0 questions** dans la base → quiz est inutilisable |
| **Panneaux** | **0 panneaux** dans TrafficSign (table vide) |
| **Théorie** | Pas de section « cours » pédagogique |
| **Blog** | Seulement 1 article → pas de SEO |
| **Thèmes** | 7 des 9 thèmes pointent vers codedelaroute.be |
| **Monétisation** | Pas de Stripe/Mollie, pas de paywall |

### Données scrapées disponibles

| Source | Contenu | Quantité |
|--------|---------|----------|
| **permisdeconduire-online.be** | Questions d'examen avec réponses et explications | **54 questions** (45 QCM, 7 oui/non, 2 numériques) |
| **readytoroad.be** | Cours théoriques structurés | **13 catégories, 54 leçons**, 91 images |
| **codedelaroute.be** | Code de la route complet (déjà importé) | 122 articles, 93 images |
| **permis24.be** | Rien (paywall total) | 0 |

---

## Plan d'action par étapes

### Étape 1 — Lancer le module Examens (PRIORITÉ HAUTE)

**Objectif :** Passer de 0 à ~250+ questions → quiz fonctionnel.

**Durée estimée :** 1-2 sessions de travail

#### 1.1 Importer les 54 questions scrapées

- **Source :** `data/sites/permisdeconduire-online.be/output/exam_questions_complete.json`
- **Format :** 45 QCM (A/B/C) + 7 oui/non + 2 numériques, toutes avec explications
- **Actions :**
  - Écrire un script d'import `scripts/import_questions.py`
  - Créer les ExamCategory correspondantes (catégoriser par thème)
  - Mapper les questions aux catégories
  - Télécharger les 54 images de questions depuis `examen.gratisrijbewijsonline.be`
  - Vérifier la qualité des données

#### 1.2 Générer des questions depuis le Code de la route

- **Source :** 122 articles dans la DB + images de panneaux
- **Méthode :** Script qui génère des questions basées sur les articles clés :
  - Vitesse : « Quelle est la vitesse maximale en agglomération ? » → Art. 11
  - Panneaux : « Que signifie ce panneau ? » → Art. 65-71
  - Priorités : « Qui a la priorité dans cette situation ? » → Art. 12
  - Stationnement : « Où est-il interdit de stationner ? » → Art. 24-25
  - Dépassement : « Quand est-il interdit de dépasser ? » → Art. 16-17
- **Objectif :** ~150-200 questions supplémentaires
- **Qualité :** Chaque question liée à son code_article dans la DB

#### 1.3 Créer les catégories d'examen

Catégories proposées (alignées sur readytoroad.be + examens officiels) :

| Catégorie | Icône | Thèmes couverts |
|-----------|-------|-----------------|
| Voie publique | 🛣️ | Définitions, usagers, types de voies |
| Vitesse et freinage | ⚡ | Limitations, distances, zones 30 |
| Priorités | 🔺 | Carrefours, ronds-points, trams |
| Dépassement | ↔️ | Règles, interdictions, croisement |
| Signalisation | 🚦 | Panneaux, feux, marquages |
| Stationnement | 🅿️ | Arrêt, zones, disque bleu |
| Obligations | 📋 | Ceinture, GSM, alcool, documents |
| Situation de conduite | 🚗 | Autoroute, tunnel, météo, nuit |

---

### Étape 2 — Importer les cours théoriques

**Objectif :** Section « Apprendre » avec contenu pédagogique (pas le texte de loi, mais des explications).

**Durée estimée :** 1-2 sessions

#### 2.1 Créer le modèle de données

Options :
- **Option A :** Nouvelle app `cours/` avec Lesson, LessonCategory
- **Option B :** Réutiliser le blog avec une catégorie « Cours théorique »
- **Recommandé :** Option A — app dédiée, plus propre

#### 2.2 Importer les 54 leçons

- **Source :** `data/sites/readytoroad.be/output/lessons_data_complete.json`
- **13 catégories :**
  1. La voie publique (7 leçons)
  2. Usagers et conducteurs (3)
  3. Les véhicules (8)
  4. La vitesse et le freinage (2)
  5. Dépassement et croisement (3)
  6. Les priorités (6)
  7. Obligations et interdictions (2)
  8. Arrêt et stationnement (4)
  9. Divers (4)
  10. Fautes graves (1)
  11. Les panneaux (7)
  12. Moto (3)
  13. Cyclomoteurs (4)
- **91 images** déjà téléchargées dans `data/sites/readytoroad.be/output/images/`

#### 2.3 Templates et navigation

- Page index cours avec catégories
- Page leçon avec contenu, images, navigation précédent/suivant
- Lier les leçons aux questions d'examen correspondantes (cross-reference)

---

### Étape 3 — Enrichir le blog (SEO)

**Objectif :** Attirer du trafic organique via Google.

**Durée estimée :** progressive, 1 article par session

#### Articles prioritaires :

1. « Comment obtenir le permis de conduire en Belgique — Guide complet 2026 »
2. « Examen théorique du permis de conduire : tout ce qu'il faut savoir »
3. « 10 erreurs fréquentes à l'examen du permis de conduire »
4. « Les panneaux de signalisation en Belgique — Guide illustré »
5. « Permis de conduire provisoire en Belgique : modèle 3, 18 mois, 36 mois »
6. « Vitesse maximale en Belgique : zones, amendes, tolérances »
7. « Code de la route belge : les changements en 2026 »
8. « Permis de conduire pour étrangers en Belgique »

#### SEO technique :
- Sitemaps déjà configurés (blog + réglementation)
- Ajouter meta descriptions, Open Graph tags
- Ajouter des liens internes vers réglementation et quiz

---

### Étape 4 — Panneaux de signalisation (TrafficSign)

**Objectif :** Catalogue interactif des panneaux belges.

**Durée estimée :** 1-2 sessions

- Les images sont déjà dans `media/signs/` et `media/reglementation/`
- Écrire un script d'import pour peupler TrafficSign
- Catégoriser : danger, interdiction, obligation, indication, priorité
- Lier aux articles du Code de la route (Art. 65-71)
- Ajouter un mode « quiz panneaux » (reconnaissance visuelle)

---

### Étape 5 — Monétisation (Phase 2)

**Objectif :** Modèle freemium — gratuit limité, premium illimité.

**Durée estimée :** 2-3 sessions

#### Modèle freemium :
- **Gratuit :** 5 questions/jour, accès aux cours, accès au Code de la route
- **Premium (€9.99/mois ou €29.99/an) :** Quiz illimité, mode examen, statistiques détaillées, pas de pub

#### Technique :
- DailyQuota existe déjà dans accounts
- Intégrer Mollie (préféré en Belgique) ou Stripe
- Pages pricing, checkout, confirmation
- Webhooks pour activer/désactiver premium

---

### Étape 6 — Contenu additionnel (Phase 3)

**Objectif :** Importer d'autres lois belges pour couvrir les 9 thèmes.

#### 6.1 Permis de conduire (AR 23 mars 1998)

- **Taille :** ~92 articles, 20 annexes, 3 variantes régionales par article
- **Complexité :** HAUTE — nécessite extension du modèle de données
- **Prérequis :** Modèle `Regulation` parent (pour séparer Code de la route / Permis de conduire)
- **Priorité :** Après que le produit principal fonctionne

#### 6.2 Autres lois (Conditions techniques, Transport, Assurance...)

- Scraping depuis codedelaroute.be/fr/reglementation/theme/*
- 7 thèmes restants → 47 lois au total (Politique criminelle en a le plus)
- Travail progressif, une loi à la fois

---

## [2026-02-28] Новый контентный пайплайн и механики (A → B)

### A. Новый пайплайн контента (JSON → импорт)

- [x] Разработан универсальный шаблон JSON для одной статьи/определения (см. _TEMPLATE.json)
- [x] Включены переводы (FR, NL, RU), SEO-метаданные на 3 языках, кросс-ссылки, изображения, вопросы
- [x] Для каждого определения минимум 3 вопроса (на FR, NL, RU), с промптом для генерации картинки
- [x] Валидация через _schema.json, инструкция по заполнению (_INSTRUCTIONS.md)
- [ ] Парсер для автоматического сбора данных с codedelaroute.be (FR, NL) и генерации RU через LLM
- [ ] Импорт новых JSON-файлов в БД через management-команду
- [ ] Ревью-флоу: статус draft/reviewed/approved, ревью в админке
- [ ] История изменений и версионирование контента

### B. Новые механики для retention и монетизации

- [ ] Личная подборка вопросов (BookmarkedQuestion): добавлять/удалять, проходить мини-тесты, отмечать как изучено
- [ ] Умный дневной лимит: 20 новых вопросов в день, всегда разные (карантин 30 дней)
- [ ] Стрик (streak): бейджи за ежедневное прохождение, email/push-уведомления
- [ ] Прогресс по темам: визуализация изученных тем, слабые места
- [ ] Экзамен: режим с таймером, случайная выборка, проходной балл
- [ ] Аналитика: статистика по дистракторам, ошибки, рекомендации
- [ ] Гибкая монетизация: лимиты, премиум, расширенная статистика

### C. Документация и инструкции

- [x] _TEMPLATE.json — шаблон структуры
- [x] _schema.json — JSON Schema для валидации
- [x] _INSTRUCTIONS.md — инструкция по заполнению и импорту
- [ ] Инструкция по парсингу и генерации переводов
- [ ] Примеры для каждой категории/темы

---

## Следующие шаги (март 2026)

1. Реализовать парсер/скрапер для автоматического сбора и генерации JSON-файлов по новому шаблону
2. Импортировать первые 10-20 статей/определений с вопросами и картинками
3. Обновить модели Django под новую структуру (Definition, BookmarkedQuestion, etc.)
4. Внедрить личную подборку и дневной лимит в UI
5. Запустить ревью-флоу и аналитику ошибок
6. Обновить документацию и провести тестирование

---

## Ordre de priorité résumé

```
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║  1. EXAMENS        ← le plus urgent, transforme le produit    ║
    ║     Import 54 Q + Génération ~200 Q                          ║
    ║                                                               ║
    ║  2. COURS THÉORIE  ← contenu pédagogique, UX complète        ║
    ║     Import 54 leçons + 91 images                             ║
    ║                                                               ║
    ║  3. BLOG SEO       ← trafic organique, progressif            ║
    ║     8+ articles ciblés                                       ║
    ║                                                               ║
    ║  4. PANNEAUX       ← quiz visuel, valeur ajoutée             ║
    ║     Import + catalogue + quiz                                ║
    ║                                                               ║
    ║  5. MONÉTISATION   ← quand le produit est complet            ║
    ║     Mollie/Stripe, freemium                                  ║
    ║                                                               ║
    ║  6. LOIS EXTERNES  ← expansion du contenu                    ║
    ║     Permis de conduire et autres arrêtés                     ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
```

---

## Métriques de succès

| Étape | KPI | Cible |
|-------|-----|-------|
| 1 | Questions dans DB | 250+ |
| 2 | Leçons importées | 54 |
| 3 | Articles blog | 8+ |
| 4 | Panneaux dans DB | 100+ |
| 5 | Paiement fonctionnel | Oui/Non |
| 6 | Lois importées | 2+ |

---

## Stack technique rappel

- **Backend :** Django 5.x, Python 3.14
- **DB :** SQLite3 (dev) → PostgreSQL (prod)
- **Frontend :** Django Templates + Tailwind CSS v4.2.1 + Alpine.js
- **Build :** `make css` (Tailwind CLI)
- **Git :** github.com:colizej/prava.git, branche main
- **Commits :** `git commit -F /tmp/commit_msg.txt` (multiline)
