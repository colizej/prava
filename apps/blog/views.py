from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q

from .models import BlogPost, BlogCategory


def post_list(request):
    """Liste des articles du blog."""
    posts = BlogPost.objects.filter(is_published=True).select_related(
        'author', 'category'
    )

    # Pagination
    paginator = Paginator(posts, 12)
    page = request.GET.get('page')
    posts_page = paginator.get_page(page)

    categories = BlogCategory.objects.all()

    context = {
        'posts': posts_page,
        'categories': categories,
    }
    return render(request, 'blog/list.html', context)


def post_detail(request, slug):
    """Détail d'un article de blog."""
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    post.increment_views()

    # Related posts (same category)
    related_posts = BlogPost.objects.filter(
        is_published=True,
        category=post.category,
    ).exclude(id=post.id)[:3]

    context = {
        'post': post,
        'related_posts': related_posts,
        'article_json_ld': post.article_structured_data(request),
    }
    return render(request, 'blog/detail.html', context)


def category_detail(request, slug):
    """Articles par catégorie."""
    category = get_object_or_404(BlogCategory, slug=slug)
    posts = BlogPost.objects.filter(
        is_published=True,
        category=category,
    ).select_related('author')

    paginator = Paginator(posts, 12)
    page = request.GET.get('page')
    posts_page = paginator.get_page(page)

    context = {
        'category': category,
        'posts': posts_page,
    }
    return render(request, 'blog/category.html', context)


def search(request):
    """Recherche dans le blog."""
    q = request.GET.get('q', '').strip()
    posts = BlogPost.objects.none()

    if q:
        posts = BlogPost.objects.filter(
            is_published=True
        ).filter(
            Q(title__icontains=q) |
            Q(content__icontains=q) |
            Q(title_nl__icontains=q) |
            Q(content_nl__icontains=q) |
            Q(title_ru__icontains=q) |
            Q(content_ru__icontains=q)
        ).select_related('author', 'category')

    paginator = Paginator(posts, 12)
    page = request.GET.get('page')
    posts_page = paginator.get_page(page)

    context = {
        'posts': posts_page,
        'search_query': q,
    }
    return render(request, 'blog/search.html', context)
