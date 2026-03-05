from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Count, Q
from django.contrib import messages

from .models import Glossary, ContactMessage
from apps.examens.models import ExamCategory, Question
from apps.blog.models import BlogPost


def home(request):
    """Page d'accueil."""
    categories = ExamCategory.objects.filter(is_active=True).annotate(
        question_count=Count('questions', filter=Q(questions__is_active=True))
    ).order_by('order')[:8]

    total_questions = Question.objects.filter(is_active=True).count()

    recent_posts = BlogPost.objects.filter(
        is_published=True
    ).order_by('-published_at')[:3]

    context = {
        'categories': categories,
        'total_questions': total_questions,
        'recent_posts': recent_posts,
    }
    return render(request, 'main/home.html', context)


def about(request):
    """Page À propos."""
    return render(request, 'main/about.html')


def contact(request):
    """Page de contact."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message_text = request.POST.get('message', '').strip()

        if all([name, email, subject, message_text]):
            ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message_text,
            )
            messages.success(request, 'Votre message a été envoyé avec succès!')
            return redirect('main:contact')
        else:
            messages.error(request, 'Veuillez remplir tous les champs.')

    return render(request, 'main/contact.html')


def pricing(request):
    """Redirect to the shop pricing page."""
    from django.shortcuts import redirect
    return redirect('shop:pricing')


def _old_pricing(request):  # kept for reference
    """Page des tarifs (static — replaced by shop)."""
    plans = [
        {
            'name': 'Gratuit',
            'price': '0€',
            'period': '',
            'features': [
                '15 questions par jour',
                'Accès aux catégories de base',
                'Statistiques basiques',
            ],
            'cta': "Commencer gratuitement",
            'highlighted': False,
        },
        {
            'name': 'Journalier',
            'price': '1,99€',
            'period': '/ jour',
            'features': [
                'Questions illimitées',
                'Mode examen',
                'Toutes les catégories',
                'Statistiques détaillées',
            ],
            'cta': 'Acheter',
            'highlighted': False,
        },
        {
            'name': 'Hebdomadaire',
            'price': '4,99€',
            'period': '/ semaine',
            'features': [
                'Questions illimitées',
                'Mode examen',
                'Toutes les catégories',
                'Statistiques détaillées',
                'Sans publicité',
            ],
            'cta': 'Acheter',
            'highlighted': False,
        },
        {
            'name': 'Mensuel',
            'price': '9,99€',
            'period': '/ mois',
            'features': [
                'Questions illimitées',
                'Mode examen',
                'Toutes les catégories',
                'Statistiques détaillées',
                'Sans publicité',
                'Support prioritaire',
            ],
            'cta': 'Choisir',
            'highlighted': True,
        },
        {
            'name': 'Trimestriel',
            'price': '19,99€',
            'period': '/ 3 mois',
            'features': [
                'Tout du mensuel',
                '33% d\'économie',
                'Accès prioritaire aux nouveautés',
            ],
            'cta': 'Meilleure offre',
            'highlighted': False,
        },
    ]
    return render(request, 'main/pricing.html', {'plans': plans})


def glossary(request):
    """Page glossaire / termes."""
    terms = Glossary.objects.all()

    # Filter by category
    category = request.GET.get('category')
    if category:
        terms = terms.filter(category=category)

    # Search
    q = request.GET.get('q')
    if q:
        terms = terms.filter(
            Q(term__icontains=q) |
            Q(term_nl__icontains=q) |
            Q(term_ru__icontains=q) |
            Q(definition__icontains=q)
        )

    categories = Glossary.objects.values_list(
        'category', flat=True
    ).distinct().order_by('category')

    context = {
        'terms': terms,
        'categories': categories,
        'selected_category': category,
        'search_query': q or '',
    }
    return render(request, 'main/glossary.html', context)


def robots_txt(request):
    """robots.txt pour SEO."""
    lines = [
        'User-agent: *',
        'Allow: /',
        '',
        'Sitemap: https://permisready.be/sitemap.xml',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')
