#!/usr/bin/env python3
"""Fill Dutch and Russian translations into .po files."""
import re
import sys

NL = {
    "Tableau de bord": "Dashboard",
    "Tests passés": "Uitgevoerde tests",
    "Tests réussis": "Geslaagde tests",
    "Questions": "Vragen",
    "Taux de réussite": "Slaagpercentage",
    "S'entraîner": "Oefenen",
    "Répondez à des questions par catégorie": "Beantwoord vragen per categorie",
    "Catégories": "Categorieën",
    "Explorez toutes les catégories de questions": "Verken alle vraagcategorieën",
    "Connexion": "Aanmelden",
    "Nom d'utilisateur": "Gebruikersnaam",
    "Mot de passe": "Wachtwoord",
    "Se connecter": "Aanmelden",
    "Pas encore de compte ?": "Nog geen account?",
    "S'inscrire": "Registreren",
    "Mon profil": "Mijn profiel",
    "Modifier le profil": "Profiel bewerken",
    "Déconnexion": "Afmelden",
    "Réussite": "Succes",
    "À revoir": "Te herzien",
    "Quota du jour": "Daglimiet",
    "Derniers tests": "Recente tests",
    "Mes révisions": "Mijn herzieningen",
    "Voir tout →": "Alles zien →",
    "Pratiquer": "Oefenen",
    "Thèmes sauvegardés": "Opgeslagen thema's",
    "Aucune question sauvegardée. Après un test, utilisez 🔖 pour marquer les questions difficiles.":
        "Geen vragen opgeslagen. Gebruik na een test 🔖 om moeilijke vragen te markeren.",
    "Enregistrer": "Opslaan",
    "Inscription": "Registratie",
    "Créer un compte": "Account aanmaken",
    "Déjà un compte ?": "Al een account?",
    "Blog": "Blog",
    "Conseils, guides et actualités pour réussir votre examen théorique du permis de conduire en Belgique.":
        "Tips, gidsen en nieuws voor uw theoretisch rijexamen in België.",
    "Tous": "Alle",
    "Aucun article publié pour le moment.": "Nog geen artikelen gepubliceerd.",
    "Recherche": "Zoeken",
    "Rechercher...": "Zoeken...",
    "Aucun résultat trouvé.": "Geen resultaten gevonden.",
    "Examens": "Examens",
    "Entraînez-vous par catégorie ou simulez un examen théorique complet. Signalisation, priorité, code de la route et plus.":
        "Oefen per categorie of simuleer een volledig theoretisch examen. Verkeersborden, voorrang, verkeersregels en meer.",
    "Tests & Examens": "Tests & Examens",
    "Entraînez-vous par thème ou simulez un vrai examen.": "Oefen per thema of simuleer een echt examen.",
    "Entraînement par thème": "Oefenen per thema",
    "Toutes les questions →": "Alle vragen →",
    "Aucune catégorie disponible pour le moment.": "Nog geen categorieën beschikbaar.",
    "Voir la liste": "Lijst bekijken",
    "Aucune liste de révision disponible pour le moment.": "Nog geen herzieningslijsten beschikbaar.",
    "Simulation d'examen": "Examensimulatie",
    "Examen complet": "Volledig examen",
    "50 questions tirées au sort dans toutes les catégories. Chronomètre de 30 minutes. Comme le vrai examen.":
        "50 willekeurige vragen uit alle categorieën. Stopwatch van 30 minuten. Zoals het echte examen.",
    "questions": "vragen",
    "Résultats détaillés": "Gedetailleerde resultaten",
    "Démarrer l'examen": "Examen starten",
    "Passer à Premium": "Upgrade naar Premium",
    "Se connecter pour passer l'examen": "Aanmelden voor het examen",
    "Historique": "Geschiedenis",
    "Historique des tests": "Testgeschiedenis",
    "Aucun test effectué.": "Nog geen tests gedaan.",
    "Commencez maintenant!": "Begin nu!",
    "Aucune liste disponible pour le moment.": "Nog geen lijst beschikbaar.",
    "Pratiquer ce test": "Deze test oefenen",
    "Retirer de la liste": "Uit lijst verwijderen",
    "Votre liste est vide": "Uw lijst is leeg",
    "Après un test, cliquez sur 🔖 sur les questions difficiles pour les ajouter ici.":
        "Na een test, klik op 🔖 bij moeilijke vragen om ze hier toe te voegen.",
    "Commencer un entraînement": "Een oefening starten",
    "Réglementation": "Verkeersregels",
    "Code de la route belge complet par thème. Règles de circulation, signalisation, permis de conduire et plus encore.":
        "Volledig Belgisch verkeersreglement per thema. Rijregels, verkeersborden, rijbewijs en meer.",
    "Code de la route belge organisé par thèmes. Sélectionnez un thème pour consulter les articles.":
        "Belgisch verkeersreglement per thema. Selecteer een thema om de artikelen te raadplegen.",
    "article": "artikel",
    "Aucune catégorie disponible.": "Nog geen categorieën beschikbaar.",
    "Textes législatifs de référence": "Referentie wetgevende teksten",
    "Lois et arrêtés royaux belges complémentaires au code de la route":
        "Belgische wetten en koninklijke besluiten aanvullend op het verkeersreglement",
    "Réglementation par thème": "Verkeersregels per thema",
    "Toute la réglementation routière belge classée par domaine":
        "Alle Belgische verkeersregels geclassificeerd per domein",
    "Panneaux de signalisation": "Verkeersborden",
    "Consultez tous les panneaux de signalisation routière belges, classés par type.":
        "Bekijk alle Belgische verkeersborden, gerangschikt per type.",
    "Voir les panneaux": "Borden bekijken",
    "Préparation Permis de Conduire Belgique": "Voorbereiding Rijbewijs België",
    "Préparez votre examen théorique du permis de conduire en Belgique avec plus de 1000 questions. Entraînement gratuit, mode examen, réglementation complète.":
        "Bereid je theoretisch rijexamen voor in België met meer dan 1000 vragen. Gratis oefenen, examenmodus, volledig verkeersreglement.",
    "Réussissez votre examen théorique du permis de conduire":
        "Slaag voor uw theoretisch rijexamen",
    "Commencer l'entraînement": "Begin met oefenen",
    "Voir les tarifs": "Tarieven bekijken",
    "Langues": "Talen",
    "Gratuit de base": "Basis gratis",
    "Catégories de questions": "Vraagcategorieën",
    "Voir toutes les catégories →": "Alle categorieën zien →",
    "Mobile First": "Mobiel Eerst",
    "Révisez n'importe où depuis votre smartphone. Application optimisée pour mobile.":
        "Leer overal, op uw smartphone. Geoptimaliseerd voor mobiel.",
    "Suivi de progression": "Voortgangsbeheer",
    "Suivez vos résultats, identifiez vos points faibles et améliorez-vous.":
        "Volg uw resultaten, identificeer zwakke punten en verbeter uzelf.",
    "Multilingue": "Meertalig",
    "Disponible en Français, Nederlands et Русский pour les expatriés.":
        "Beschikbaar in het Frans, Nederlands en Russisch voor expats.",
    "Derniers articles": "Laatste artikelen",
    "Voir tous les articles →": "Alle artikelen zien →",
    "Prêt à commencer ?": "Klaar om te beginnen?",
    "Inscrivez-vous gratuitement et commencez votre préparation dès maintenant.":
        "Registreer gratis en begin nu met uw voorbereiding.",
    "Créer un compte gratuit": "Gratis account aanmaken",
    "S'entraîner maintenant": "Nu oefenen",
    "Tarifs": "Tarieven",
    "Découvrez nos tarifs pour la préparation à l'examen théorique du permis de conduire. Accès gratuit ou premium.":
        "Ontdek onze tarieven voor de voorbereiding op het theoretisch rijexamen. Gratis of premium toegang.",
    "Nos tarifs": "Onze tarieven",
    "Choisissez le plan qui vous convient. Commencez gratuitement et passez à Premium quand vous êtes prêt.":
        "Kies het plan dat bij u past. Begin gratis en upgrade naar Premium wanneer u klaar bent.",
    "Populaire": "Populair",
    "Page non trouvée": "Pagina niet gevonden",
    "404 — Page non trouvée": "404 — Pagina niet gevonden",
    "La page que vous recherchez n'existe pas ou a été déplacée.":
        "De pagina die u zoekt bestaat niet of is verplaatst.",
    "Retour à l'accueil": "Terug naar de startpagina",
    "Erreur serveur": "Serverfout",
    "500 — Erreur serveur": "500 — Serverfout",
    "Une erreur inattendue s'est produite. Veuillez réessayer plus tard.":
        "Er is een onverwachte fout opgetreden. Probeer het later opnieuw.",
    "Langue :": "Taal:",
    "Navigation": "Navigatie",
    "Préparation à l'examen théorique du permis de conduire en Belgique. Plus de 1000 questions pour réussir votre examen.":
        "Voorbereiding op het theoretisch rijexamen in België. Meer dan 1000 vragen om te slagen voor uw examen.",
    "Informations": "Informatie",
    "Tous droits réservés.": "Alle rechten voorbehouden.",
    "Glossaire": "Woordenlijst",
    "Glossaire des termes": "Woordenlijst van termen",
    "Rechercher un terme...": "Een term zoeken...",
    "Aucun terme trouvé.": "Geen term gevonden.",
    "À propos": "Over ons",
    "Contact": "Contact",
    "Contactez-nous": "Neem contact op",
    "Nom": "Naam",
    "Email": "E-mail",
    "Sujet": "Onderwerp",
    "Message": "Bericht",
    "Envoyer": "Verzenden",
    "Mes révisions": "Mijn herzieningen",
    "Voir tout →": "Alles zien →",
}

RU = {
    "Tableau de bord": "Личный кабинет",
    "Tests passés": "Пройдено тестов",
    "Tests réussis": "Сдано тестов",
    "Questions": "Вопросы",
    "Taux de réussite": "Процент успеха",
    "S'entraîner": "Тренироваться",
    "Répondez à des questions par catégorie": "Отвечайте на вопросы по категориям",
    "Catégories": "Категории",
    "Explorez toutes les catégories de questions": "Просмотрите все категории вопросов",
    "Connexion": "Войти",
    "Nom d'utilisateur": "Имя пользователя",
    "Mot de passe": "Пароль",
    "Se connecter": "Войти",
    "Pas encore de compte ?": "Нет аккаунта?",
    "S'inscrire": "Зарегистрироваться",
    "Mon profil": "Мой профиль",
    "Modifier le profil": "Редактировать профиль",
    "Déconnexion": "Выйти",
    "Réussite": "Успех",
    "À revoir": "К повторению",
    "Quota du jour": "Дневной лимит",
    "Derniers tests": "Последние тесты",
    "Mes révisions": "Мои повторения",
    "Voir tout →": "Смотреть всё →",
    "Pratiquer": "Практиковать",
    "Thèmes sauvegardés": "Сохранённые темы",
    "Aucune question sauvegardée. Après un test, utilisez 🔖 pour marquer les questions difficiles.":
        "Вопросов нет. После теста нажмите 🔖 на сложных вопросах, чтобы добавить их сюда.",
    "Enregistrer": "Сохранить",
    "Inscription": "Регистрация",
    "Créer un compte": "Создать аккаунт",
    "Déjà un compte ?": "Уже есть аккаунт?",
    "Blog": "Блог",
    "Conseils, guides et actualités pour réussir votre examen théorique du permis de conduire en Belgique.":
        "Советы, руководства и новости для сдачи теоретического экзамена в Бельгии.",
    "Tous": "Все",
    "Aucun article publié pour le moment.": "Статьи пока не опубликованы.",
    "Recherche": "Поиск",
    "Rechercher...": "Поиск...",
    "Aucun résultat trouvé.": "Результаты не найдены.",
    "Examens": "Экзамены",
    "Entraînez-vous par catégorie ou simulez un examen théorique complet. Signalisation, priorité, code de la route et plus.":
        "Тренируйтесь по категориям или имитируйте полный теоретический экзамен. Знаки, приоритет, ПДД и многое другое.",
    "Tests & Examens": "Тесты и экзамены",
    "Entraînez-vous par thème ou simulez un vrai examen.": "Тренируйтесь по теме или имитируйте настоящий экзамен.",
    "Entraînement par thème": "Тренировка по теме",
    "Toutes les questions →": "Все вопросы →",
    "Aucune catégorie disponible pour le moment.": "Категорий пока нет.",
    "Voir la liste": "Просмотреть список",
    "Aucune liste de révision disponible pour le moment.": "Списков для повторения пока нет.",
    "Simulation d'examen": "Симуляция экзамена",
    "Examen complet": "Полный экзамен",
    "50 questions tirées au sort dans toutes les catégories. Chronomètre de 30 minutes. Comme le vrai examen.":
        "50 случайных вопросов из всех категорий. Таймер 30 минут. Как на настоящем экзамене.",
    "questions": "вопросов",
    "Résultats détaillés": "Подробные результаты",
    "Démarrer l'examen": "Начать экзамен",
    "Passer à Premium": "Перейти на Premium",
    "Se connecter pour passer l'examen": "Войдите чтобы сдать экзамен",
    "Historique": "История",
    "Historique des tests": "История тестов",
    "Aucun test effectué.": "Тестов ещё нет.",
    "Commencez maintenant!": "Начните сейчас!",
    "Aucune liste disponible pour le moment.": "Списков пока нет.",
    "Pratiquer ce test": "Пройти этот тест",
    "Retirer de la liste": "Удалить из списка",
    "Votre liste est vide": "Ваш список пуст",
    "Après un test, cliquez sur 🔖 sur les questions difficiles pour les ajouter ici.":
        "После теста нажмите 🔖 на сложных вопросах, чтобы добавить их сюда.",
    "Commencer un entraînement": "Начать тренировку",
    "Réglementation": "ПДД",
    "Code de la route belge complet par thème. Règles de circulation, signalisation, permis de conduire et plus encore.":
        "Полный Бельгийский ПДД по темам. Правила движения, знаки, водительские права и многое другое.",
    "Code de la route belge organisé par thèmes. Sélectionnez un thème pour consulter les articles.":
        "Бельгийский ПДД по темам. Выберите тему для просмотра статей.",
    "article": "статья",
    "Textes législatifs de référence": "Законодательные тексты",
    "Lois et arrêtés royaux belges complémentaires au code de la route":
        "Бельгийские законы и королевские указы, дополняющие ПДД",
    "Réglementation par thème": "ПДД по темам",
    "Toute la réglementation routière belge classée par domaine":
        "Весь Бельгийский ПДД, классифицированный по областям",
    "Panneaux de signalisation": "Дорожные знаки",
    "Consultez tous les panneaux de signalisation routière belges, classés par type.":
        "Просмотрите все Бельгийские дорожные знаки, классифицированные по типу.",
    "Voir les panneaux": "Смотреть знаки",
    "Préparation Permis de Conduire Belgique": "Подготовка к экзамену на права в Бельгии",
    "Préparez votre examen théorique du permis de conduire en Belgique avec plus de 1000 questions. Entraînement gratuit, mode examen, réglementation complète.":
        "Подготовьтесь к теоретическому экзамену в Бельгии с более чем 1000 вопросами. Бесплатная тренировка, режим экзамена, полный ПДД.",
    "Réussissez votre examen théorique du permis de conduire": "Сдайте теоретический экзамен на права",
    "Commencer l'entraînement": "Начать тренировку",
    "Voir les tarifs": "Посмотреть тарифы",
    "Langues": "Языки",
    "Gratuit de base": "Базовая версия бесплатна",
    "Catégories de questions": "Категории вопросов",
    "Voir toutes les catégories →": "Все категории →",
    "Mobile First": "Мобильная версия",
    "Révisez n'importe où depuis votre smartphone. Application optimisée pour mobile.":
        "Учитесь везде, на вашем смартфоне. Оптимизировано для мобильных.",
    "Suivi de progression": "Отслеживание прогресса",
    "Suivez vos résultats, identifiez vos points faibles et améliorez-vous.":
        "Следите за результатами, выявляйте слабые места и совершенствуйтесь.",
    "Multilingue": "Многоязычность",
    "Disponible en Français, Nederlands et Русский pour les expatriés.":
        "Доступно на французском, нидерландском и русском для экспатов.",
    "Derniers articles": "Последние статьи",
    "Voir tous les articles →": "Все статьи →",
    "Prêt à commencer ?": "Готовы начать?",
    "Inscrivez-vous gratuitement et commencez votre préparation dès maintenant.":
        "Зарегистрируйтесь бесплатно и начните подготовку прямо сейчас.",
    "Créer un compte gratuit": "Создать бесплатный аккаунт",
    "S'entraîner maintenant": "Тренироваться сейчас",
    "Tarifs": "Тарифы",
    "Découvrez nos tarifs pour la préparation à l'examen théorique du permis de conduire. Accès gratuit ou premium.":
        "Узнайте наши тарифы для подготовки к теоретическому экзамену. Бесплатный или premium доступ.",
    "Nos tarifs": "Наши тарифы",
    "Choisissez le plan qui vous convient. Commencez gratuitement et passez à Premium quand vous êtes prêt.":
        "Выберите подходящий план. Начните бесплатно и перейдите на Premium, когда будете готовы.",
    "Populaire": "Популярный",
    "Page non trouvée": "Страница не найдена",
    "404 — Page non trouvée": "404 — Страница не найдена",
    "La page que vous recherchez n'existe pas ou a été déplacée.":
        "Страница, которую вы ищете, не существует или была перемещена.",
    "Retour à l'accueil": "На главную",
    "Erreur serveur": "Ошибка сервера",
    "500 — Erreur serveur": "500 — Ошибка сервера",
    "Une erreur inattendue s'est produite. Veuillez réessayer plus tard.":
        "Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже.",
    "Langue :": "Язык:",
    "Navigation": "Навигация",
    "Préparation à l'examen théorique du permis de conduire en Belgique. Plus de 1000 questions pour réussir votre examen.":
        "Подготовка к теоретическому экзамену на права в Бельгии. Более 1000 вопросов для успешной сдачи.",
    "Informations": "Информация",
    "Tous droits réservés.": "Все права защищены.",
    "Glossaire": "Глоссарий",
    "Glossaire des termes": "Глоссарий терминов",
    "Rechercher un terme...": "Найти термин...",
    "Aucun terme trouvé.": "Термин не найден.",
    "À propos": "О нас",
    "Contact": "Контакт",
    "Contactez-nous": "Свяжитесь с нами",
    "Nom": "Имя",
    "Email": "Электронная почта",
    "Sujet": "Тема",
    "Message": "Сообщение",
    "Envoyer": "Отправить",
}

# Also add blocktrans strings (with placeholders)
NL_BLOCKTRANS = {
    "Plus de %(n)s questions d'entraînement, code de la route complet, et mode examen simulé.":
        "Meer dan %(n)s oefenvragen, volledig verkeersreglement en gesimuleerde examenmodus.",
    "%(t)s min de lecture": "%(t)s min lezen",
    "Pourquoi %(SITE_NAME)s ?": "Waarom %(SITE_NAME)s?",
    "À propos de %(SITE_NAME)s": "Over %(SITE_NAME)s",
    "%(SITE_NAME)s est une plateforme de préparation à l'examen théorique du permis de conduire en Belgique.":
        "%(SITE_NAME)s is een platform voor de voorbereiding op het theoretisch rijexamen in België.",
    "Notre mission : vous aider à réussir votre examen grâce à des questions d'entraînement de qualité, disponibles en français, néerlandais et russe.":
        "Onze missie: u helpen slagen voor uw examen met kwaliteitsoefenvragen, beschikbaar in het Frans, Nederlands en Russisch.",
}

RU_BLOCKTRANS = {
    "Plus de %(n)s questions d'entraînement, code de la route complet, et mode examen simulé.":
        "Более %(n)s тренировочных вопросов, полный ПДД и режим симуляции экзамена.",
    "%(t)s min de lecture": "%(t)s мин чтения",
    "Pourquoi %(SITE_NAME)s ?": "Почему %(SITE_NAME)s?",
    "À propos de %(SITE_NAME)s": "О %(SITE_NAME)s",
    "%(SITE_NAME)s est une plateforme de préparation à l'examen théorique du permis de conduire en Belgique.":
        "%(SITE_NAME)s — платформа для подготовки к теоретическому экзамену на права в Бельгии.",
    "Notre mission : vous aider à réussir votre examen grâce à des questions d'entraînement de qualité, disponibles en français, néerlandais et russe.":
        "Наша миссия: помочь вам сдать экзамен с качественными тренировочными вопросами на французском, нидерландском и русском.",
}
NL.update(NL_BLOCKTRANS)
RU.update(RU_BLOCKTRANS)


def fill_po(path, translations):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse blocks: each entry is #comments + msgid + msgstr
    # We'll replace empty msgstr "" with translations
    def replace_msgstr(match):
        msgid_raw = match.group(1)
        # Unescape the msgid
        msgid = msgid_raw.replace('\\"', '"').replace('\\n', '\n')
        if msgid in translations:
            trans = translations[msgid]
            # Escape the translation
            trans_escaped = trans.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            return f'msgid "{msgid_raw}"\nmsgstr "{trans_escaped}"'
        return match.group(0)

    # Replace empty msgstr blocks
    result = re.sub(
        r'msgid "([^"]*(?:\\"[^"]*)*)"\nmsgstr ""',
        replace_msgstr,
        content
    )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(result)

    # Count filled translations
    filled = sum(1 for k in translations if f'msgid "{k}"\nmsgstr "' in result and
                 f'msgid "{k}"\nmsgstr ""' not in result)
    print(f"  Filled {filled}/{len(translations)} translations in {path}")


base = '/Users/colizej/Documents/webApp/prava/locale'
print("Filling NL translations...")
fill_po(f'{base}/nl/LC_MESSAGES/django.po', NL)

print("Filling RU translations...")
fill_po(f'{base}/ru/LC_MESSAGES/django.po', RU)

print("Done!")
