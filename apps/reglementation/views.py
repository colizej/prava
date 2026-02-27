from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count

from .models import RuleCategory, CodeArticle, TrafficSign


def index(request):
    """Page principale réglementation."""
    categories = RuleCategory.objects.filter(is_active=True).annotate(
        articles_count=Count('articles')
    ).order_by('order')

    context = {
        'categories': categories,
    }
    return render(request, 'reglementation/index.html', context)


def category_detail(request, slug):
    """Articles d'une catégorie."""
    category = get_object_or_404(RuleCategory, slug=slug, is_active=True)
    articles = category.articles.all()

    # Free access check
    if not request.user.is_authenticated or not (
        hasattr(request.user, 'profile') and request.user.profile.has_active_premium
    ):
        articles = articles.filter(is_free=True)

    paginator = Paginator(articles, 20)
    page = request.GET.get('page')
    articles_page = paginator.get_page(page)

    context = {
        'category': category,
        'articles': articles_page,
    }
    return render(request, 'reglementation/category.html', context)


def article_detail(request, slug):
    """Détail d'un article du code."""
    article = get_object_or_404(CodeArticle, slug=slug)

    # Premium check
    if not article.is_free:
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect('accounts:login')
        if not request.user.profile.has_active_premium:
            return redirect('main:pricing')

    # Related questions from examens
    related_questions = article.questions.filter(is_active=True)[:5]

    # Next/previous
    next_article = CodeArticle.objects.filter(
        order__gt=article.order
    ).order_by('order').first()
    prev_article = CodeArticle.objects.filter(
        order__lt=article.order
    ).order_by('-order').first()

    context = {
        'article': article,
        'related_questions': related_questions,
        'next_article': next_article,
        'prev_article': prev_article,
    }
    return render(request, 'reglementation/article.html', context)


def signs_list(request):
    """Liste de tous les panneaux de signalisation."""
    sign_types = TrafficSign.SIGN_TYPES
    signs = TrafficSign.objects.all()

    context = {
        'sign_types': sign_types,
        'signs': signs,
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
