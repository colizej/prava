from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch

from .models import RuleCategory, CodeArticle, TrafficSign, ArticleImage

# Metadata for non-1975 laws used in index grouping
_LAW_META = {
    '1968': {
        'title': 'Loi du 16 mars 1968 — Police de la circulation routière',
        'short': 'Infractions, peines et déchéance du droit de conduire',
        'color': 'purple',
    },
    '1976': {
        'title': 'AM du 11 octobre 1976 — Dimensions, masse et signalisation',
        'short': 'Dimensions, poids des véhicules et prescriptions de signalisation',
        'color': 'sky',
    },
    '1998': {
        'title': 'AR du 23 mars 1998 — Permis de conduire',
        'short': 'Catégories, conditions médicales, échange et retrait du permis',
        'color': 'green',
    },
    '2005': {
        'title': 'AR du 30 septembre 2005 — Infractions par degré',
        'short': 'Classement des infractions routières en degrés 1 à 4',
        'color': 'orange',
    },
    '2006': {
        'title': 'AR du 10 juillet 2006 — Permis catégorie B',
        'short': 'Formation, examen théorique et pratique, conduite accompagnée',
        'color': 'emerald',
    },
    '1968b': {
        'title': 'AR du 15 mars 1968 — Conditions techniques des véhicules',
        'short': 'Exigences techniques pour voitures, camions et remorques',
        'color': 'slate',
    },
    '1985': {
        'title': 'Loi du 21 juin 1985 — Conditions techniques (loi-cadre)',
        'short': 'Loi-cadre sur les conditions techniques des véhicules de transport',
        'color': 'slate',
    },
    '1989': {
        'title': 'Loi du 21 novembre 1989 — Assurance RC obligatoire',
        'short': 'Assurance obligatoire de la responsabilité des véhicules automoteurs',
        'color': 'amber',
    },
    '2001': {
        'title': 'AR du 20 juillet 2001 — Immatriculation des véhicules',
        'short': 'Conditions et procédures d\'immatriculation, plaques minéralogiques',
        'color': 'amber',
    },
}


def index(request):
    """Page principale réglementation."""
    # AR 1975 categories for the main grid
    categories = RuleCategory.objects.filter(
        is_active=True, law_id='1975'
    ).annotate(articles_count=Count('articles')).order_by('order')

    # Other laws grouped for the "Textes législatifs" section
    extra_qs = list(
        RuleCategory.objects.filter(is_active=True)
        .exclude(law_id='1975')
        .annotate(articles_count=Count('articles'))
        .order_by('law_id', 'order')
    )
    laws_grouped = []
    current_law_id = None
    for cat in extra_qs:
        if cat.law_id != current_law_id:
            current_law_id = cat.law_id
            meta = _LAW_META.get(cat.law_id, {'title': f'Loi {cat.law_id}', 'short': '', 'color': 'gray'})
            laws_grouped.append({
                'law_id': cat.law_id,
                'title': meta['title'],
                'short': meta['short'],
                'color': meta['color'],
                'categories': [],
            })
        laws_grouped[-1]['categories'].append(cat)

    context = {
        'categories': categories,
        'laws_grouped': laws_grouped,
    }
    return render(request, 'reglementation/index.html', context)


def category_detail(request, slug):
    """Articles d'une catégorie."""
    category = get_object_or_404(RuleCategory, slug=slug, is_active=True)
    articles = category.articles.prefetch_related('images').all()

    # Free access check
    if not request.user.is_authenticated or not (
        hasattr(request.user, 'profile') and request.user.profile.has_active_premium
    ):
        articles = articles.filter(is_free=True)

    paginator = Paginator(articles, 20)
    page = request.GET.get('page')
    articles_page = paginator.get_page(page)

    # Sidebar: categories from the same law only
    all_categories = RuleCategory.objects.filter(
        is_active=True, law_id=category.law_id
    ).annotate(articles_count=Count('articles')).order_by('order')

    context = {
        'category': category,
        'articles': articles_page,
        'all_categories': all_categories,
    }
    return render(request, 'reglementation/category.html', context)


def article_detail(request, slug):
    """Détail d'un article du code."""
    article = get_object_or_404(
        CodeArticle.objects.select_related('category').prefetch_related('images'),
        slug=slug
    )

    # Premium check
    if not article.is_free:
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect('accounts:login')
        if not request.user.profile.has_active_premium:
            return redirect('main:pricing')

    # Related questions from examens — all of them with options
    related_questions = []
    if hasattr(article, 'questions'):
        related_questions = list(
            article.questions
            .filter(is_active=True)
            .prefetch_related('options')
            .order_by('difficulty', 'id')
        )

    # Next/previous within same category
    next_article = CodeArticle.objects.filter(
        category=article.category, order__gt=article.order
    ).order_by('order').first()
    prev_article = CodeArticle.objects.filter(
        category=article.category, order__lt=article.order
    ).order_by('-order').first()

    # Table of contents for long articles
    siblings = CodeArticle.objects.filter(
        category=article.category
    ).order_by('order')[:30]

    context = {
        'article': article,
        'related_questions': related_questions,
        'next_article': next_article,
        'prev_article': prev_article,
        'siblings': siblings,
        'is_staff': request.user.is_staff,
    }
    return render(request, 'reglementation/article.html', context)


def signs_list(request):
    """Liste de tous les panneaux de signalisation, organisés par catégorie."""
    EMOJIS = {
        'danger': '⚠️',
        'interdiction': '🚫',
        'obligation': '🔵',
        'indication': 'ℹ️',
        'priorite': '🔶',
        'directionnel': '➡️',
        'additionnel': '➕',
    }
    PREVIEW_LIMIT = 10

    categories = []
    for type_code, type_label in TrafficSign.SIGN_TYPES:
        qs = TrafficSign.objects.filter(sign_type=type_code).order_by('order', 'code')
        total = qs.count()
        if total == 0:
            continue
        categories.append({
            'code': type_code,
            'label': type_label,
            'emoji': EMOJIS.get(type_code, '🪧'),
            'total': total,
            'signs': qs[:PREVIEW_LIMIT],
            'has_more': total > PREVIEW_LIMIT,
        })

    context = {
        'categories': categories,
    }
    return render(request, 'reglementation/signs.html', context)


def signs_by_type(request, sign_type):
    """Panneaux par type."""
    signs = TrafficSign.objects.filter(sign_type=sign_type)
    type_name = dict(TrafficSign.SIGN_TYPES).get(sign_type, sign_type)

    context = {
        'signs': signs,
        'sign_type': sign_type,
        'type_name': type_name,
    }
    return render(request, 'reglementation/signs_type.html', context)
