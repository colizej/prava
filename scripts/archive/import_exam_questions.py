#!/usr/bin/env python3
"""
Import exam questions into PRAVA database.

Phase 1: Import 54 scraped questions from permisdeconduire-online.be
Phase 2: Generate questions from Code de la route articles

Usage:
    cd /Users/colizej/Documents/webApp/prava
    python3 manage.py shell < scripts/import_exam_questions.py

    OR:
    python3 scripts/import_exam_questions.py
"""
import os, sys, re, json, django

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
django.setup()

from apps.examens.models import ExamCategory, Question, AnswerOption
from apps.reglementation.models import CodeArticle

# ============================================================================
# EXAM CATEGORIES
# ============================================================================

CATEGORIES = [
    {
        'name': 'La voie publique',
        'name_nl': 'De openbare weg',
        'name_ru': 'Дорога общего пользования',
        'slug': 'voie-publique',
        'icon': 'road',
        'description': 'Définitions, types de voies, usagers, chaussée, trottoir, accotements.',
        'order': 1,
    },
    {
        'name': 'Vitesse et freinage',
        'name_nl': 'Snelheid en remmen',
        'name_ru': 'Скорость и торможение',
        'slug': 'vitesse-freinage',
        'icon': 'speedometer',
        'description': 'Limitations de vitesse, zones 30, distances de freinage, autoroute.',
        'order': 2,
    },
    {
        'name': 'Priorités',
        'name_nl': 'Voorrang',
        'name_ru': 'Приоритет',
        'slug': 'priorites',
        'icon': 'priority',
        'description': 'Règles de priorité, carrefours, ronds-points, trams.',
        'order': 3,
    },
    {
        'name': 'Dépassement et croisement',
        'name_nl': 'Inhalen en kruisen',
        'name_ru': 'Обгон и разъезд',
        'slug': 'depassement',
        'icon': 'overtake',
        'description': 'Règles de dépassement, interdictions, croisement.',
        'order': 4,
    },
    {
        'name': 'Signalisation',
        'name_nl': 'Verkeersborden',
        'name_ru': 'Дорожные знаки',
        'slug': 'signalisation',
        'icon': 'sign',
        'description': 'Panneaux de danger, interdiction, obligation, indication, feux.',
        'order': 5,
    },
    {
        'name': 'Arrêt et stationnement',
        'name_nl': 'Stilstaan en parkeren',
        'name_ru': 'Остановка и стоянка',
        'slug': 'arret-stationnement',
        'icon': 'parking',
        'description': 'Règles d\'arrêt, de stationnement, zones bleues, interdictions.',
        'order': 6,
    },
    {
        'name': 'Obligations du conducteur',
        'name_nl': 'Verplichtingen van de bestuurder',
        'name_ru': 'Обязанности водителя',
        'slug': 'obligations',
        'icon': 'checklist',
        'description': 'Ceinture, GSM, alcool, documents, éclairage, clignotants.',
        'order': 7,
    },
    {
        'name': 'Situations de conduite',
        'name_nl': 'Rijsituaties',
        'name_ru': 'Дорожные ситуации',
        'slug': 'situations',
        'icon': 'car',
        'description': 'Autoroute, tunnel, rond-point, piétons, cyclistes, conditions météo.',
        'order': 8,
    },
]


def create_categories():
    """Create or update exam categories."""
    created = 0
    for cat_data in CATEGORIES:
        cat, is_new = ExamCategory.objects.update_or_create(
            slug=cat_data['slug'],
            defaults=cat_data,
        )
        if is_new:
            created += 1
    print(f"Categories: {created} created, {len(CATEGORIES) - created} updated.")
    return {c.slug: c for c in ExamCategory.objects.all()}


# ============================================================================
# PHASE 1: Import 54 scraped questions
# ============================================================================

def parse_mc_options(question_text):
    """
    Parse multiple choice options from question text.
    Returns (clean_text, [(letter, text), ...])

    Formats:
        "... A. Answer1.\nB. Answer2.\nC. Answer3."
        "... A. Answer1\nB. Answer2\nC. Answer3"
    """
    # Split options: find the first "A." or "\nA." pattern
    pattern = r'\n\s*A\.\s+'
    m = re.search(pattern, question_text)
    if not m:
        # Try without newline
        pattern = r'\s{2,}A\.\s+'
        m = re.search(pattern, question_text)

    if not m:
        return question_text.strip(), []

    clean_text = question_text[:m.start()].strip()
    options_text = question_text[m.start():].strip()

    # Parse individual options
    options = []
    parts = re.split(r'\n\s*([A-D])\.\s+', options_text)
    # parts[0] is before first match (empty or "A. text")
    # Then alternating: letter, text, letter, text...

    # Handle first part which starts with "A. ..."
    first_match = re.match(r'([A-D])\.\s+(.*)', parts[0].strip())
    if first_match:
        options.append((first_match.group(1), first_match.group(2).strip().rstrip('.')))
        parts = parts[1:]

    i = 0
    while i < len(parts) - 1:
        letter = parts[i].strip()
        text = parts[i + 1].strip().rstrip('.')
        if letter and text:
            options.append((letter, text))
        i += 2

    return clean_text, options


def categorize_scraped_question(q):
    """Map a scraped question to an ExamCategory slug based on content analysis."""
    text = q.get('question_text', '').lower()
    explanation = q.get('explanation', '').lower()
    combined = text + ' ' + explanation

    # Signalisation keywords
    if any(w in combined for w in ['signal', 'panneau', 'feux', 'marque routière',
                                     'bande de circulation', 'flèche', 'ligne blanche',
                                     'zone piétonne', 'sens interdit']):
        return 'signalisation'

    # Vitesse
    if any(w in combined for w in ['vitesse', 'km/h', 'zone 30', 'autoroute',
                                     'freinage', 'distance']):
        return 'vitesse-freinage'

    # Priorité
    if any(w in combined for w in ['priorité', 'céder', 'carrefour', 'rond-point',
                                     'tram', 'tirette']):
        return 'priorites'

    # Dépassement
    if any(w in combined for w in ['dépasser', 'dépassement', 'croisement',
                                     'croiser', 'file']):
        return 'depassement'

    # Stationnement
    if any(w in combined for w in ['stationn', 'arrêt', 'parking', 'disque',
                                     'zone bleue', 'portière']):
        return 'arret-stationnement'

    # Obligations
    if any(w in combined for w in ['ceinture', 'gsm', 'téléphone', 'alcool',
                                     'casque', 'document', 'permis provisoire',
                                     'volant', 'rétroviseur', 'feux', 'phare',
                                     'éclairage']):
        return 'obligations'

    # Situations
    if any(w in combined for w in ['tunnel', 'passage à niveau', 'piéton',
                                     'cycliste', 'pluie', 'brouillard', 'nuit',
                                     'accident', 'panne']):
        return 'situations'

    # Default: voie publique (most general)
    return 'voie-publique'


def import_scraped_questions(categories):
    """Import 54 scraped questions from permisdeconduire-online.be."""
    json_path = os.path.join(BASE_DIR, 'data/sites/permisdeconduire-online.be/output/exam_questions_complete.json')
    data = json.load(open(json_path))
    questions = data['questions']

    imported = 0
    skipped = 0

    for q in questions:
        qid = q['question_id']
        source_tag = f'permisdeconduire-online:{qid}'

        # Skip if already imported
        if Question.objects.filter(source=source_tag).exists():
            skipped += 1
            continue

        answer_type = q['answer_type']
        raw_text = q['question_text']
        correct_answer = q['correct_answer'].strip().lower()
        explanation = q.get('explanation', '')
        image_url = q.get('image_url', '')

        # Categorize
        cat_slug = categorize_scraped_question(q)
        category = categories.get(cat_slug, categories.get('voie-publique'))

        # Determine difficulty
        difficulty = 2  # default medium
        if answer_type == 'yes_no':
            difficulty = 1  # easier
        elif answer_type == 'numeric':
            difficulty = 2

        # Parse options depending on type
        if answer_type == 'multiple_choice':
            clean_text, options_parsed = parse_mc_options(raw_text)
            if not options_parsed:
                # Fallback: try to extract from raw text
                clean_text = raw_text.strip()
                options_parsed = []
        elif answer_type == 'yes_no':
            clean_text = raw_text.strip()
            options_parsed = [('A', 'Oui'), ('B', 'Non')]
            correct_answer = 'a' if correct_answer == 'oui' else 'b'
        elif answer_type == 'numeric':
            # Extract the actual question part
            clean_text = raw_text.replace('Entrez un nombre :', '').replace('Entrez un nombre:', '').strip()
            options_parsed = []  # No options for numeric — we'll convert to MC
        else:
            clean_text = raw_text.strip()
            options_parsed = []

        # For numeric questions, convert to multiple choice with plausible answers
        if answer_type == 'numeric' and correct_answer.isdigit():
            correct_val = int(correct_answer)
            if correct_val == 70:
                options_parsed = [('A', '50 km/h'), ('B', '70 km/h'), ('C', '90 km/h')]
                correct_answer = 'b'
            elif correct_val == 90:
                options_parsed = [('A', '70 km/h'), ('B', '90 km/h'), ('C', '120 km/h')]
                correct_answer = 'b'
            elif correct_val == 120:
                options_parsed = [('A', '90 km/h'), ('B', '100 km/h'), ('C', '120 km/h')]
                correct_answer = 'c'
            else:
                # Generic numeric conversion
                options_parsed = [
                    ('A', str(max(0, correct_val - 20))),
                    ('B', str(correct_val)),
                    ('C', str(correct_val + 20)),
                ]
                correct_answer = 'b'

        # Create question
        question = Question.objects.create(
            category=category,
            text=clean_text,
            explanation=explanation,
            difficulty=difficulty,
            is_active=True,
            is_official=False,
            source=source_tag,
            tags=['scraped', 'permisdeconduire-online'],
        )

        # Create options
        for i, (letter, text) in enumerate(options_parsed):
            AnswerOption.objects.create(
                question=question,
                letter=letter,
                text=text,
                is_correct=(letter.lower() == correct_answer),
                order=i,
            )

        imported += 1

    print(f"Scraped questions: {imported} imported, {skipped} skipped (already exist).")
    return imported


# ============================================================================
# PHASE 2: Generate questions from Code de la route
# ============================================================================

# Manually curated questions based on the Belgian Code de la route
# Each question references the exact article number

GENERATED_QUESTIONS = [
    # === VITESSE (Art. 10-11) ===
    {
        'text': 'Quelle est la vitesse maximale autorisée en agglomération ?',
        'options': [('A', '30 km/h'), ('B', '50 km/h'), ('C', '70 km/h')],
        'correct': 'B',
        'explanation': 'En agglomération, la vitesse est limitée à 50 km/h (Art. 11.1.1°). Dans certaines zones, comme les zones 30, la limitation peut être réduite.',
        'article': 'Art. 11',
        'category': 'vitesse-freinage',
        'difficulty': 1,
    },
    {
        'text': 'Quelle est la vitesse maximale autorisée hors agglomération sur une route ordinaire ?',
        'options': [('A', '70 km/h'), ('B', '90 km/h'), ('C', '120 km/h')],
        'correct': 'A',
        'explanation': 'Hors agglomération, la vitesse est limitée à 70 km/h en Région wallonne et à Bruxelles (90 km/h en Flandre sur certaines routes). La règle générale est 70 km/h (Art. 11.1.2°).',
        'article': 'Art. 11',
        'category': 'vitesse-freinage',
        'difficulty': 1,
    },
    {
        'text': 'Quelle est la vitesse maximale autorisée sur les autoroutes en Belgique ?',
        'options': [('A', '100 km/h'), ('B', '120 km/h'), ('C', '130 km/h')],
        'correct': 'B',
        'explanation': 'Sur les autoroutes belges, la vitesse maximale est de 120 km/h (Art. 11.1.3°).',
        'article': 'Art. 11',
        'category': 'vitesse-freinage',
        'difficulty': 1,
    },
    {
        'text': 'Quelle est la vitesse maximale dans une zone 30 ?',
        'options': [('A', '20 km/h'), ('B', '30 km/h'), ('C', '50 km/h')],
        'correct': 'B',
        'explanation': 'Dans les zones délimitées par les signaux d\'entrée et de sortie de zone 30, la vitesse est limitée à 30 km/h (Art. 22quater).',
        'article': 'Art. 22quater',
        'category': 'vitesse-freinage',
        'difficulty': 1,
    },
    {
        'text': 'Quelle est la vitesse maximale dans une zone résidentielle ?',
        'options': [('A', '10 km/h'), ('B', '20 km/h'), ('C', '30 km/h')],
        'correct': 'B',
        'explanation': 'Dans les zones résidentielles et les zones de rencontre, la vitesse est limitée à 20 km/h (Art. 22bis).',
        'article': 'Art. 22bis',
        'category': 'vitesse-freinage',
        'difficulty': 1,
    },
    {
        'text': 'Quelle est la vitesse maximale autorisée sur une route pour automobiles ?',
        'options': [('A', '90 km/h'), ('B', '100 km/h'), ('C', '120 km/h')],
        'correct': 'C',
        'explanation': 'La vitesse maximale sur les routes pour automobiles est de 120 km/h (Art. 22).',
        'article': 'Art. 22',
        'category': 'vitesse-freinage',
        'difficulty': 2,
    },
    {
        'text': 'Quelle est la vitesse minimale autorisée sur l\'autoroute ?',
        'options': [('A', '50 km/h'), ('B', '70 km/h'), ('C', 'Il n\'y a pas de vitesse minimale fixée')],
        'correct': 'B',
        'explanation': 'Sur les autoroutes, les véhicules qui ne peuvent pas atteindre au moins 70 km/h en palier ne sont pas admis (Art. 21.1).',
        'article': 'Art. 21',
        'category': 'vitesse-freinage',
        'difficulty': 2,
    },
    {
        'text': 'Un conducteur doit adapter sa vitesse en fonction de quels facteurs ?',
        'options': [
            ('A', 'Uniquement la signalisation routière'),
            ('B', 'La densité de la circulation, les conditions météo, l\'état de la route et le chargement'),
            ('C', 'Uniquement la présence d\'autres véhicules'),
        ],
        'correct': 'B',
        'explanation': 'Le conducteur doit régler sa vitesse en fonction des circonstances : présence d\'autres usagers, conditions atmosphériques, état et caractéristiques de la route, chargement du véhicule (Art. 10.1).',
        'article': 'Art. 10',
        'category': 'vitesse-freinage',
        'difficulty': 2,
    },
    {
        'text': 'À l\'approche d\'un passage pour piétons non réglé par des signaux lumineux, un conducteur doit :',
        'options': [
            ('A', 'Accélérer pour passer rapidement'),
            ('B', 'Ralentir et s\'arrêter si des piétons traversent ou s\'apprêtent à traverser'),
            ('C', 'Klaxonner pour avertir les piétons'),
        ],
        'correct': 'B',
        'explanation': 'Le conducteur qui approche d\'un passage pour piétons doit ralentir. Il doit céder le passage aux piétons qui s\'y engagent ou manifestent l\'intention de s\'y engager (Art. 40.4.2).',
        'article': 'Art. 40',
        'category': 'vitesse-freinage',
        'difficulty': 2,
    },

    # === PRIORITÉS (Art. 12, 14) ===
    {
        'text': 'À un carrefour sans signalisation, quelle est la règle de priorité par défaut ?',
        'options': [
            ('A', 'Priorité à gauche'),
            ('B', 'Priorité à droite'),
            ('C', 'Le premier arrivé passe en premier'),
        ],
        'correct': 'B',
        'explanation': 'Le conducteur est tenu de céder le passage au conducteur venant de sa droite, sauf signalisation contraire (Art. 12.1).',
        'article': 'Art. 12',
        'category': 'priorites',
        'difficulty': 1,
    },
    {
        'text': 'Un conducteur qui sort d\'un chemin de terre doit céder le passage :',
        'options': [
            ('A', 'Uniquement aux véhicules venant de droite'),
            ('B', 'À tous les usagers circulant sur la voie publique'),
            ('C', 'Uniquement aux piétons'),
        ],
        'correct': 'B',
        'explanation': 'Le conducteur qui débouche d\'un chemin de terre, d\'un lieu non ouvert à la circulation publique, ou d\'une propriété riveraine, doit céder le passage à tous les usagers (Art. 12.4).',
        'article': 'Art. 12',
        'category': 'priorites',
        'difficulty': 1,
    },
    {
        'text': 'Le conducteur qui tourne à gauche doit céder le passage :',
        'options': [
            ('A', 'Uniquement aux véhicules venant en sens inverse'),
            ('B', 'Aux véhicules venant en sens inverse et aux piétons et cyclistes qui traversent'),
            ('C', 'À personne, il a la priorité'),
        ],
        'correct': 'B',
        'explanation': 'Le conducteur qui effectue un virage à gauche doit céder le passage aux véhicules venant en sens inverse et aux piétons traversant la chaussée (Art. 12.4 et Art. 19.4).',
        'article': 'Art. 12',
        'category': 'priorites',
        'difficulty': 2,
    },
    {
        'text': 'Qu\'est-ce que la « tirette » (zipper) ?',
        'options': [
            ('A', 'Un système de stationnement alterné'),
            ('B', 'L\'obligation de laisser passer alternativement un véhicule de chaque file lors d\'un rétrécissement'),
            ('C', 'Un signal de danger'),
        ],
        'correct': 'B',
        'explanation': 'Lorsqu\'une bande de circulation se termine, les conducteurs qui circulent sur la bande qui subsiste doivent céder le passage à tour de rôle aux conducteurs de l\'autre bande (Art. 12bis).',
        'article': 'Art. 12bis',
        'category': 'priorites',
        'difficulty': 2,
    },
    {
        'text': 'Un conducteur peut-il s\'engager dans un carrefour s\'il risque d\'y être immobilisé ?',
        'options': [
            ('A', 'Oui, s\'il a la priorité'),
            ('B', 'Oui, si le feu est vert'),
            ('C', 'Non, même si le feu est vert ou s\'il a la priorité'),
        ],
        'correct': 'C',
        'explanation': 'Aucun conducteur ne peut s\'engager dans un carrefour s\'il est évident que la densité de la circulation est telle qu\'il sera immobilisé dans le carrefour (Art. 14.1).',
        'article': 'Art. 14',
        'category': 'priorites',
        'difficulty': 2,
    },
    {
        'text': 'Le tramway a-t-il toujours la priorité ?',
        'options': [
            ('A', 'Oui, dans tous les cas'),
            ('B', 'Non, uniquement lorsque la signalisation le prévoit'),
            ('C', 'Non, mais il a la priorité dans la plupart des situations'),
        ],
        'correct': 'C',
        'explanation': 'Le tramway bénéficie d\'une priorité de passage dans la plupart des cas, mais il doit respecter les feux de signalisation et ne jouit pas de la priorité en toute circonstance (Art. 12.3).',
        'article': 'Art. 12',
        'category': 'priorites',
        'difficulty': 2,
    },

    # === DÉPASSEMENT (Art. 16-17) ===
    {
        'text': 'Par quel côté doit-on dépasser en principe ?',
        'options': [
            ('A', 'Par la droite'),
            ('B', 'Par la gauche'),
            ('C', 'Indifféremment à droite ou à gauche'),
        ],
        'correct': 'B',
        'explanation': 'En principe, le dépassement se fait par la gauche (Art. 16.1). Le dépassement par la droite est autorisé dans certains cas spécifiques (Art. 16.5).',
        'article': 'Art. 16',
        'category': 'depassement',
        'difficulty': 1,
    },
    {
        'text': 'Quand est-il autorisé de dépasser par la droite ?',
        'options': [
            ('A', 'Quand le conducteur devant roule lentement'),
            ('B', 'Quand le conducteur devant signale qu\'il va tourner à gauche'),
            ('C', 'Quand on circule sur l\'autoroute'),
        ],
        'correct': 'B',
        'explanation': 'Le dépassement par la droite est autorisé lorsque le conducteur qui précède a signalé l\'intention de tourner à gauche et s\'est déporté vers la gauche (Art. 16.5).',
        'article': 'Art. 16',
        'category': 'depassement',
        'difficulty': 2,
    },
    {
        'text': 'Quand est-il interdit de dépasser ?',
        'options': [
            ('A', 'À l\'approche d\'un sommet de côte et dans un virage lorsque la visibilité est insuffisante'),
            ('B', 'Uniquement en agglomération'),
            ('C', 'Uniquement sur une autoroute'),
        ],
        'correct': 'A',
        'explanation': 'Le dépassement est interdit notamment à l\'approche du sommet d\'une côte et dans les virages, lorsque la visibilité est insuffisante, sauf si le dépassement peut s\'effectuer sans franchir une ligne blanche continue (Art. 17.2).',
        'article': 'Art. 17',
        'category': 'depassement',
        'difficulty': 2,
    },
    {
        'text': 'Avant de dépasser, le conducteur doit vérifier que :',
        'options': [
            ('A', 'Aucun véhicule ne le suit de trop près'),
            ('B', 'Le véhicule qui le précède n\'a pas signalé l\'intention de dépasser et que la voie est libre'),
            ('C', 'Les deux conditions ci-dessus'),
        ],
        'correct': 'C',
        'explanation': 'Le conducteur qui veut dépasser doit s\'assurer qu\'il peut le faire sans danger : aucun conducteur derrière n\'a commencé un dépassement, le conducteur devant n\'a pas signalé l\'intention de dépasser, et la voie est libre (Art. 16.3).',
        'article': 'Art. 16',
        'category': 'depassement',
        'difficulty': 2,
    },
    {
        'text': 'Est-il interdit de dépasser à un passage pour piétons ?',
        'options': [
            ('A', 'Non, sauf si des piétons traversent'),
            ('B', 'Oui, il est interdit de dépasser à un passage pour piétons'),
            ('C', 'Non, le dépassement y est toujours autorisé'),
        ],
        'correct': 'B',
        'explanation': 'Le dépassement est interdit aux passages pour piétons et aux passages pour cyclistes et conducteurs de cyclomoteurs à deux roues (Art. 17.2.4°).',
        'article': 'Art. 17',
        'category': 'depassement',
        'difficulty': 2,
    },

    # === SIGNALISATION (Art. 60-77) ===
    {
        'text': 'Que signifie un feu clignotant orange ?',
        'options': [
            ('A', 'Interdiction de passer'),
            ('B', 'Le conducteur peut continuer avec prudence en respectant les règles de priorité'),
            ('C', 'Obligation de s\'arrêter'),
        ],
        'correct': 'B',
        'explanation': 'Le feu orange clignotant signifie que le conducteur peut passer mais doit redoubler de prudence et respecter les règles de priorité (Art. 64.1).',
        'article': 'Art. 64',
        'category': 'signalisation',
        'difficulty': 1,
    },
    {
        'text': 'Que signifie un feu rouge fixe ?',
        'options': [
            ('A', 'Obligation de s\'arrêter'),
            ('B', 'Ralentir et passer avec prudence'),
            ('C', 'Passer si la voie est libre'),
        ],
        'correct': 'A',
        'explanation': 'Le feu rouge interdit le passage. Le conducteur doit s\'arrêter (Art. 61.1.1°).',
        'article': 'Art. 61',
        'category': 'signalisation',
        'difficulty': 1,
    },
    {
        'text': 'Que signifie un feu vert avec une flèche orange clignotante ?',
        'options': [
            ('A', 'Interdiction de tourner dans la direction de la flèche'),
            ('B', 'Vous pouvez tourner dans la direction de la flèche en cédant le passage aux piétons et cyclistes'),
            ('C', 'Le feu va passer au rouge'),
        ],
        'correct': 'B',
        'explanation': 'La flèche orange clignotante indique que le conducteur peut tourner dans la direction de la flèche, mais doit céder le passage aux piétons et cyclistes (Art. 61.4).',
        'article': 'Art. 61',
        'category': 'signalisation',
        'difficulty': 2,
    },
    {
        'text': 'Que devez-vous faire lorsque le feu passe à l\'orange fixe ?',
        'options': [
            ('A', 'Accélérer pour passer avant le rouge'),
            ('B', 'S\'arrêter, sauf si l\'arrêt compromet la sécurité'),
            ('C', 'Continuer à la même vitesse'),
        ],
        'correct': 'B',
        'explanation': 'Le feu orange fixe interdit le passage. Toutefois, le conducteur qui ne peut plus s\'arrêter dans des conditions de sécurité suffisantes peut franchir le feu (Art. 61.1.2°).',
        'article': 'Art. 61',
        'category': 'signalisation',
        'difficulty': 1,
    },
    {
        'text': 'Les signaux de danger sont de quelle forme ?',
        'options': [
            ('A', 'Ronde'),
            ('B', 'Carrée'),
            ('C', 'Triangulaire, pointe vers le haut'),
        ],
        'correct': 'C',
        'explanation': 'Les signaux de danger sont de forme triangulaire avec la pointe dirigée vers le haut, à fond blanc avec un bord rouge (Art. 66).',
        'article': 'Art. 66',
        'category': 'signalisation',
        'difficulty': 1,
    },
    {
        'text': 'Les signaux d\'interdiction sont de quelle forme ?',
        'options': [
            ('A', 'Triangulaire'),
            ('B', 'Ronde à fond blanc avec bord rouge'),
            ('C', 'Carrée bleue'),
        ],
        'correct': 'B',
        'explanation': 'Les signaux d\'interdiction sont de forme ronde à fond blanc avec un bord rouge (Art. 68).',
        'article': 'Art. 68',
        'category': 'signalisation',
        'difficulty': 1,
    },
    {
        'text': 'Les signaux d\'obligation sont de quelle forme ?',
        'options': [
            ('A', 'Ronde à fond bleu avec symbole blanc'),
            ('B', 'Triangulaire'),
            ('C', 'Carrée à fond blanc'),
        ],
        'correct': 'A',
        'explanation': 'Les signaux d\'obligation sont de forme ronde à fond bleu avec un symbole blanc (Art. 69).',
        'article': 'Art. 69',
        'category': 'signalisation',
        'difficulty': 1,
    },
    {
        'text': 'Que signifie une ligne blanche continue sur la chaussée ?',
        'options': [
            ('A', 'Interdiction de la franchir ou de la chevaucher'),
            ('B', 'Possibilité de la franchir pour dépasser'),
            ('C', 'Limitation de vitesse'),
        ],
        'correct': 'A',
        'explanation': 'Il est interdit de franchir une ligne continue ou de rouler dessus (Art. 72.2).',
        'article': 'Art. 72',
        'category': 'signalisation',
        'difficulty': 1,
    },
    {
        'text': 'Qu\'indique une ligne discontinue blanche sur la chaussée ?',
        'options': [
            ('A', 'Interdiction de dépasser'),
            ('B', 'Séparation des bandes de circulation, franchissement autorisé'),
            ('C', 'Zone de stationnement'),
        ],
        'correct': 'B',
        'explanation': 'Les lignes discontinues blanches séparent les bandes de circulation. Elles peuvent être franchies pour dépasser ou changer de direction (Art. 72.3).',
        'article': 'Art. 72',
        'category': 'signalisation',
        'difficulty': 1,
    },

    # === ARRÊT ET STATIONNEMENT (Art. 23-27) ===
    {
        'text': 'Quelle est la différence entre l\'arrêt et le stationnement ?',
        'options': [
            ('A', 'Il n\'y a pas de différence'),
            ('B', 'L\'arrêt est limité au temps nécessaire pour embarquer/débarquer des personnes ou charger/décharger'),
            ('C', 'L\'arrêt dure moins de 5 minutes'),
        ],
        'correct': 'B',
        'explanation': 'Un véhicule est « à l\'arrêt » quand il est immobilisé pendant le temps requis pour l\'embarquement ou le débarquement de personnes ou de choses. Au-delà, c\'est du stationnement (Art. 2.22-23).',
        'article': 'Art. 2',
        'category': 'arret-stationnement',
        'difficulty': 1,
    },
    {
        'text': 'Où est-il interdit de stationner ?',
        'options': [
            ('A', 'Sur les trottoirs et les passerelles'),
            ('B', 'À moins de 5 mètres d\'un carrefour'),
            ('C', 'Les deux réponses sont correctes'),
        ],
        'correct': 'C',
        'explanation': 'Il est interdit de stationner sur les trottoirs (Art. 24.1°), et à moins de 5 mètres du prolongement du bord le plus rapproché de la chaussée transversale à un carrefour (Art. 24.2°).',
        'article': 'Art. 24',
        'category': 'arret-stationnement',
        'difficulty': 2,
    },
    {
        'text': 'Est-il interdit de s\'arrêter sur un passage pour piétons ?',
        'options': [
            ('A', 'Non, on peut s\'y arrêter brièvement'),
            ('B', 'Oui, l\'arrêt et le stationnement y sont interdits'),
            ('C', 'Non, s\'il n\'y a pas de piétons'),
        ],
        'correct': 'B',
        'explanation': 'Il est interdit de mettre un véhicule à l\'arrêt ou en stationnement sur les passages pour piétons et à moins de 5 mètres en deçà de ces passages (Art. 24.1°).',
        'article': 'Art. 24',
        'category': 'arret-stationnement',
        'difficulty': 1,
    },
    {
        'text': 'À quelle distance minimale d\'un carrefour est-il interdit de stationner ?',
        'options': [
            ('A', '3 mètres'),
            ('B', '5 mètres'),
            ('C', '10 mètres'),
        ],
        'correct': 'B',
        'explanation': 'Il est interdit de stationner à moins de 5 mètres du prolongement du bord le plus rapproché de la chaussée transversale (Art. 24.2°).',
        'article': 'Art. 24',
        'category': 'arret-stationnement',
        'difficulty': 2,
    },
    {
        'text': 'Que signifie un disque de stationnement (zone bleue) ?',
        'options': [
            ('A', 'Stationnement interdit'),
            ('B', 'Stationnement gratuit à durée limitée avec utilisation du disque'),
            ('C', 'Stationnement payant'),
        ],
        'correct': 'B',
        'explanation': 'La zone bleue indique un stationnement à durée limitée. Le conducteur doit placer un disque de stationnement visible derrière le pare-brise (Art. 27).',
        'article': 'Art. 27',
        'category': 'arret-stationnement',
        'difficulty': 1,
    },
    {
        'text': 'Les véhicules doivent être rangés :',
        'options': [
            ('A', 'En toute circonstance parallèlement au bord de la chaussée'),
            ('B', 'Le plus à droite possible, parallèlement au bord de la chaussée'),
            ('C', 'Perpendiculairement au trottoir'),
        ],
        'correct': 'B',
        'explanation': 'Les véhicules à l\'arrêt ou en stationnement doivent être rangés le plus à droite possible par rapport au sens de leur marche (Art. 23.1).',
        'article': 'Art. 23',
        'category': 'arret-stationnement',
        'difficulty': 2,
    },

    # === OBLIGATIONS DU CONDUCTEUR (Art. 8, 35-36, 44) ===
    {
        'text': 'Le port de la ceinture de sécurité est-il obligatoire en Belgique ?',
        'options': [
            ('A', 'Oui, pour le conducteur et tous les passagers'),
            ('B', 'Oui, uniquement pour le conducteur'),
            ('C', 'Non, c\'est facultatif'),
        ],
        'correct': 'A',
        'explanation': 'Le conducteur et les passagers doivent porter la ceinture de sécurité (Art. 35.1.1).',
        'article': 'Art. 35',
        'category': 'obligations',
        'difficulty': 1,
    },
    {
        'text': 'Est-il permis d\'utiliser un téléphone portable tenu en main en conduisant ?',
        'options': [
            ('A', 'Oui, pour les appels courts'),
            ('B', 'Non, c\'est interdit'),
            ('C', 'Oui, si le véhicule est à l\'arrêt dans un embouteillage'),
        ],
        'correct': 'B',
        'explanation': 'Il est interdit au conducteur d\'utiliser un téléphone portable tenu en main (Art. 8.4). Un kit mains-libres est autorisé.',
        'article': 'Art. 8',
        'category': 'obligations',
        'difficulty': 1,
    },
    {
        'text': 'Les enfants de moins de 1,35 m doivent être transportés :',
        'options': [
            ('A', 'Sur la banquette arrière sans dispositif spécial'),
            ('B', 'Dans un dispositif de retenue adapté (siège enfant)'),
            ('C', 'Avec la seule ceinture de sécurité'),
        ],
        'correct': 'B',
        'explanation': 'Les enfants de moins de 1,35 m doivent être transportés dans un dispositif de retenue pour enfants adapté à leur taille et à leur poids (Art. 35.1.1).',
        'article': 'Art. 35',
        'category': 'obligations',
        'difficulty': 1,
    },
    {
        'text': 'Le port du casque est obligatoire pour :',
        'options': [
            ('A', 'Les conducteurs et passagers de motos et cyclomoteurs'),
            ('B', 'Uniquement les conducteurs de motos'),
            ('C', 'Tous les usagers de la route'),
        ],
        'correct': 'A',
        'explanation': 'Le casque de protection est obligatoire pour les conducteurs et passagers de motocyclettes et de cyclomoteurs (Art. 36).',
        'article': 'Art. 36',
        'category': 'obligations',
        'difficulty': 1,
    },
    {
        'text': 'Le conducteur doit-il toujours être en état de conduire son véhicule ?',
        'options': [
            ('A', 'Oui, il doit être en mesure d\'effectuer toutes les manœuvres nécessaires'),
            ('B', 'Non, sa responsabilité est limitée'),
            ('C', 'Oui, uniquement en agglomération'),
        ],
        'correct': 'A',
        'explanation': 'Tout conducteur doit être en état de conduire et posséder les qualités physiques requises. Il doit être constamment en mesure d\'effectuer les manœuvres qui lui incombent (Art. 8.3).',
        'article': 'Art. 8',
        'category': 'obligations',
        'difficulty': 1,
    },
    {
        'text': 'Le nombre de passagers dans une voiture :',
        'options': [
            ('A', 'N\'est pas limité'),
            ('B', 'Ne peut dépasser le nombre de places mentionné au certificat d\'immatriculation'),
            ('C', 'Est limité à 5 personnes'),
        ],
        'correct': 'B',
        'explanation': 'Le nombre de personnes transportées ne peut dépasser le nombre de places mentionné au certificat d\'immatriculation (Art. 44).',
        'article': 'Art. 44',
        'category': 'obligations',
        'difficulty': 2,
    },
    {
        'text': 'Quand les feux de croisement (codes) doivent-ils être allumés ?',
        'options': [
            ('A', 'Uniquement la nuit'),
            ('B', 'La nuit et de jour par temps de brouillard, pluie forte, ou chute de neige'),
            ('C', 'Uniquement quand la visibilité est inférieure à 50 m'),
        ],
        'correct': 'B',
        'explanation': 'Les feux de croisement doivent être utilisés la nuit et de jour en cas de visibilité réduite (brouillard, pluie forte, chute de neige) (Art. 30).',
        'article': 'Art. 30',
        'category': 'obligations',
        'difficulty': 2,
    },

    # === SITUATIONS DE CONDUITE (Art. 21, 40-43, 52) ===
    {
        'text': 'Sur l\'autoroute, le conducteur doit emprunter :',
        'options': [
            ('A', 'La bande de droite, sauf pour dépasser'),
            ('B', 'N\'importe quelle bande'),
            ('C', 'Toujours la bande du milieu'),
        ],
        'correct': 'A',
        'explanation': 'Sur les autoroutes, les véhicules doivent emprunter la bande de droite. Les bandes de gauche sont réservées au dépassement (Art. 9.3 et 21).',
        'article': 'Art. 21',
        'category': 'situations',
        'difficulty': 1,
    },
    {
        'text': 'En cas d\'accident avec blessés, que devez-vous faire ?',
        'options': [
            ('A', 'Quitter les lieux si vous n\'êtes pas responsable'),
            ('B', 'Prévenir les services de secours, sécuriser les lieux, porter assistance'),
            ('C', 'Déplacer les blessés vers le trottoir'),
        ],
        'correct': 'B',
        'explanation': 'En cas d\'accident ayant causé des blessures, le conducteur doit appeler les services de secours, ne pas quitter les lieux, assurer la sécurité et porter assistance aux blessés (Art. 52).',
        'article': 'Art. 52',
        'category': 'situations',
        'difficulty': 1,
    },
    {
        'text': 'Un piéton qui s\'engage sur un passage pour piétons lorsque le feu est vert pour les voitures :',
        'options': [
            ('A', 'A toujours la priorité'),
            ('B', 'N\'a pas la priorité mais le conducteur doit rester prudent'),
            ('C', 'Doit être verbalisé'),
        ],
        'correct': 'B',
        'explanation': 'Les piétons doivent respecter les feux. Cependant, le conducteur doit toujours faire preuve de prudence à l\'égard des piétons (Art. 40 et 42).',
        'article': 'Art. 40',
        'category': 'situations',
        'difficulty': 2,
    },
    {
        'text': 'Les cyclistes peuvent-ils circuler à deux de front ?',
        'options': [
            ('A', 'Non, jamais'),
            ('B', 'Oui, en dehors des agglomérations uniquement'),
            ('C', 'Oui, en agglomération et sur les pistes cyclables ; hors agglomération ils doivent se mettre en file si un véhicule approche'),
        ],
        'correct': 'C',
        'explanation': 'Les cyclistes peuvent circuler à deux de front. Hors agglomération, ils doivent se mettre en file indienne à l\'approche d\'un véhicule venant de l\'arrière (Art. 43.1).',
        'article': 'Art. 43',
        'category': 'situations',
        'difficulty': 2,
    },
    {
        'text': 'Comment doit-on se comporter quand un bus scolaire s\'arrête avec les feux clignotants ?',
        'options': [
            ('A', 'Continuer à rouler normalement'),
            ('B', 'Ralentir et s\'arrêter si nécessaire pour laisser monter/descendre les enfants'),
            ('C', 'Klaxonner pour signaler votre présence'),
        ],
        'correct': 'B',
        'explanation': 'Lorsqu\'un véhicule affecté au transport scolaire est à l\'arrêt avec ses feux clignotants, les conducteurs venant des deux sens doivent ralentir et s\'arrêter si nécessaire (Art. 39bis).',
        'article': 'Art. 39bis',
        'category': 'situations',
        'difficulty': 1,
    },
    {
        'text': 'Les véhicules prioritaires (police, pompiers, ambulances) en mission urgente :',
        'options': [
            ('A', 'Doivent toujours respecter les feux rouges'),
            ('B', 'Peuvent déroger aux règles de circulation lorsqu\'ils utilisent leurs avertisseurs spéciaux'),
            ('C', 'N\'ont aucun privilège'),
        ],
        'correct': 'B',
        'explanation': 'Les véhicules prioritaires utilisant leurs avertisseurs sonores et lumineux spéciaux peuvent déroger aux règles de la circulation. Les autres conducteurs doivent leur céder le passage (Art. 37 et 38).',
        'article': 'Art. 37',
        'category': 'situations',
        'difficulty': 1,
    },
    {
        'text': 'Que devez-vous faire lorsque votre véhicule tombe en panne sur l\'autoroute ?',
        'options': [
            ('A', 'Attendre dans le véhicule'),
            ('B', 'Allumer les feux de détresse, placer le triangle de danger et quitter le véhicule par la droite'),
            ('C', 'Essayer de pousser le véhicule sur la bande d\'arrêt d\'urgence'),
        ],
        'correct': 'B',
        'explanation': 'En cas de panne, le conducteur doit signaler l\'immobilisation de son véhicule avec les feux de détresse et un triangle de danger. Les occupants doivent quitter le véhicule et se mettre en sécurité (Art. 51).',
        'article': 'Art. 51',
        'category': 'situations',
        'difficulty': 1,
    },

    # === VOIE PUBLIQUE (Art. 1-2, 7, 9) ===
    {
        'text': 'Que comprend la « voie publique » au sens du code de la route ?',
        'options': [
            ('A', 'Uniquement la chaussée'),
            ('B', 'La chaussée, les trottoirs, les accotements, les pistes cyclables et les bermes'),
            ('C', 'Uniquement la chaussée et les trottoirs'),
        ],
        'correct': 'B',
        'explanation': 'La voie publique comprend l\'ensemble de l\'espace accessible au public : chaussée, trottoirs, accotements, passages pour piétons, pistes cyclables, bermes, etc. (Art. 2.1).',
        'article': 'Art. 2',
        'category': 'voie-publique',
        'difficulty': 1,
    },
    {
        'text': 'Que signifie le terme « agglomération » dans le code de la route ?',
        'options': [
            ('A', 'Un ensemble de bâtiments'),
            ('B', 'L\'espace délimité par les signaux F1 et F3'),
            ('C', 'Uniquement les villes de plus de 10.000 habitants'),
        ],
        'correct': 'B',
        'explanation': 'L\'agglomération est l\'espace délimité par des signaux de début (F1) et de fin (F3) d\'agglomération, portant le nom de la localité (Art. 2.12).',
        'article': 'Art. 2',
        'category': 'voie-publique',
        'difficulty': 2,
    },
    {
        'text': 'Le code de la route s\'applique-t-il sur les parkings de supermarchés ?',
        'options': [
            ('A', 'Non, ce sont des propriétés privées'),
            ('B', 'Oui, s\'ils sont accessibles au public'),
            ('C', 'Uniquement pour le stationnement'),
        ],
        'correct': 'B',
        'explanation': 'Le code de la route s\'applique sur la voie publique, définie comme tout l\'espace ouvert à la circulation publique, y compris les parkings accessibles au public (Art. 1 et 2).',
        'article': 'Art. 1',
        'category': 'voie-publique',
        'difficulty': 2,
    },
    {
        'text': 'Un « usager » au sens du code de la route est :',
        'options': [
            ('A', 'Uniquement les conducteurs de véhicules à moteur'),
            ('B', 'Toute personne qui utilise la voie publique'),
            ('C', 'Les piétons et les cyclistes uniquement'),
        ],
        'correct': 'B',
        'explanation': 'Un « usager » est toute personne qui utilise la voie publique : conducteurs (voitures, motos, vélos), piétons, cavaliers, etc. (Art. 2.2).',
        'article': 'Art. 2',
        'category': 'voie-publique',
        'difficulty': 1,
    },
    {
        'text': 'Les injonctions des agents qualifiés (police) ont-elles la priorité sur les signaux routiers ?',
        'options': [
            ('A', 'Non, les signaux routiers ont toujours la priorité'),
            ('B', 'Oui, les injonctions des agents qualifiés prévalent sur les signaux'),
            ('C', 'Cela dépend de la situation'),
        ],
        'correct': 'B',
        'explanation': 'Les injonctions faites par les agents qualifiés prévalent sur les signaux routiers ordinaires et les règles de circulation (Art. 4 et 6).',
        'article': 'Art. 6',
        'category': 'voie-publique',
        'difficulty': 2,
    },
    {
        'text': 'Sur une chaussée à double sens de circulation sans marquage, les conducteurs doivent circuler :',
        'options': [
            ('A', 'Au milieu de la chaussée'),
            ('B', 'Le plus à droite possible'),
            ('C', 'N\'importe où si la route est libre'),
        ],
        'correct': 'B',
        'explanation': 'Le conducteur doit circuler le plus à droite possible de la chaussée (Art. 9.1).',
        'article': 'Art. 9',
        'category': 'voie-publique',
        'difficulty': 1,
    },
]


def import_generated_questions(categories):
    """Import manually generated questions from Code de la route."""
    # Build article lookup: article_number -> CodeArticle
    article_map = {}
    for art in CodeArticle.objects.all():
        article_map[art.article_number] = art

    imported = 0
    skipped = 0

    for q_data in GENERATED_QUESTIONS:
        source_tag = f"generated:cdr:{q_data['article']}:{hash(q_data['text']) % 100000}"

        # Skip if already imported (by text match)
        if Question.objects.filter(text=q_data['text']).exists():
            skipped += 1
            continue

        category = categories.get(q_data['category'], categories.get('voie-publique'))

        # Try to find the referenced article
        code_article = article_map.get(q_data['article'])

        question = Question.objects.create(
            category=category,
            code_article=code_article,
            text=q_data['text'],
            explanation=q_data['explanation'],
            difficulty=q_data.get('difficulty', 2),
            is_active=True,
            is_official=False,
            source=source_tag,
            tags=['generated', 'code-de-la-route'],
        )

        # Create options
        correct_letter = q_data['correct'].upper()
        for i, (letter, text) in enumerate(q_data['options']):
            AnswerOption.objects.create(
                question=question,
                letter=letter,
                text=text,
                is_correct=(letter.upper() == correct_letter),
                order=i,
            )

        imported += 1

    print(f"Generated questions: {imported} imported, {skipped} skipped (already exist).")
    return imported


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("PRAVA — Import Exam Questions")
    print("=" * 60)

    # Step 1: Create categories
    print("\n--- Creating Exam Categories ---")
    categories = create_categories()

    # Step 2: Import scraped questions
    print("\n--- Phase 1: Importing 54 scraped questions ---")
    scraped_count = import_scraped_questions(categories)

    # Step 3: Import generated questions
    print("\n--- Phase 2: Importing generated questions ---")
    generated_count = import_generated_questions(categories)

    # Summary
    print("\n" + "=" * 60)
    total_q = Question.objects.filter(is_active=True).count()
    total_opts = AnswerOption.objects.count()
    total_cats = ExamCategory.objects.filter(is_active=True).count()

    print(f"SUMMARY:")
    print(f"  Categories:      {total_cats}")
    print(f"  Total questions:  {total_q}")
    print(f"  Total options:    {total_opts}")
    print(f"  New scraped:      {scraped_count}")
    print(f"  New generated:    {generated_count}")

    # Per category
    print("\nQuestions per category:")
    for cat in ExamCategory.objects.filter(is_active=True).order_by('order'):
        count = Question.objects.filter(category=cat, is_active=True).count()
        print(f"  {cat.name}: {count}")

    print("\n" + "=" * 60)
    print("Done!")


if __name__ == '__main__':
    main()
