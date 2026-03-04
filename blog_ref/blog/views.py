from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import F, Count, Q
from django.core.paginator import Paginator
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.cache import never_cache
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.utils import timezone
from django.core.cache import cache
from .models import Article, Category, Tag, ArticleComment, BlogSettings
from .forms import CommentForm


def get_published_articles_queryset():
    """
    Helper: Return queryset of published articles visible to users.
    Shows articles where status='published' AND (published_at is in past OR null).
    """
    now = timezone.now()
    return Article.objects.filter(
        status='published'
    ).filter(
        Q(published_at__lte=now) | Q(published_at__isnull=True)
    )

@never_cache
def article_detail(request, slug):
    # Try to find article first - ALWAYS fetch fresh from DB
    now = timezone.now()
    try:
        if request.user.is_staff:
            article = Article.objects.select_related('profile_author').get(slug=slug)
        else:
            article = Article.objects.select_related('profile_author').get(slug=slug, status='published')
            # Check if published_at allows viewing
            if article.published_at and article.published_at > now:
                raise Article.DoesNotExist
    except Article.DoesNotExist:
        # If no article found, try to find a product (play)
        from profiles.models import Play
        try:
            play = Play.objects.get(slug=slug, status='published')
            # Check if published_at allows viewing (unless user is staff)
            if not request.user.is_staff:
                if play.published_at and play.published_at > now:
                    raise Play.DoesNotExist
            # Redirect to play detail view
            from profiles.views import play_detail as profiles_play_detail
            return profiles_play_detail(request, slug)
        except Play.DoesNotExist:
            # Neither article nor play found
            raise Http404("Page not found")

    session_key = f'viewed_article_{article.pk}'
    if not request.session.get(session_key):
        Article.objects.filter(pk=article.pk).update(views=F('views') + 1)
        article.refresh_from_db()
        request.session[session_key] = True

    # Навигация внутри категории (если есть категория)
    prev_article = None
    next_article = None

    if article.category:
        # Предыдущая статья (более старая) в той же категории
        prev_article = get_published_articles_queryset().filter(
            category=article.category,
            published_at__lt=article.published_at
        ).order_by('-published_at').first()

        # Следующая статья (более новая) в той же категории
        next_article = get_published_articles_queryset().filter(
            category=article.category,
            published_at__gt=article.published_at
        ).order_by('published_at').first()
    else:
        # Если нет категории, навигация по всем статьям
        prev_article = get_published_articles_queryset().filter(
            published_at__lt=article.published_at
        ).order_by('-published_at').first()

        next_article = get_published_articles_queryset().filter(
            published_at__gt=article.published_at
        ).order_by('published_at').first()

    # Get approved comments for this article (root level only, replies fetched via template)
    comments = article.comments.filter(
        status='approved',
        parent__isnull=True
    ).select_related('author_profile').prefetch_related('replies').order_by('created_at')

    # Comment form
    comment_form = CommentForm()

    # Pre-fill name/email from cookies for unregistered users
    if not request.user.is_authenticated:
        comment_form.initial['author_name'] = request.COOKIES.get('comment_author_name', '')
        comment_form.initial['author_email'] = request.COOKIES.get('comment_author_email', '')

    # Check if user has liked this article
    from .models import ArticleLike
    user_has_liked = False
    if request.user.is_authenticated:
        user_has_liked = ArticleLike.objects.filter(article=article, user=request.user).exists()
    else:
        # Create session if it doesn't exist
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        if session_key:
            user_has_liked = ArticleLike.objects.filter(article=article, session_key=session_key).exists()

    context = {
        'article': article,
        'prev_article': prev_article,
        'next_article': next_article,
        'comments': comments,
        'comment_form': comment_form,
        'comments_count': article.comments.filter(status='approved').count(),
        'user_has_liked': user_has_liked,
    }

    # Use unified template for both blog articles and technical pages
    # is_page flag controls which sections are displayed
    return render(request, 'blog/article_detail.html', context)


def article_list(request):
    # Exclude technical pages from blog listing
    qs = get_published_articles_queryset().filter(is_page=False).select_related(
        'category', 'profile_author'
    ).prefetch_related('tags')

    # Filtering by category and tags via GET params: ?category=<slug>&tags=slug1,slug2
    category_slug = request.GET.get('category')
    tags_param = request.GET.get('tags', '')
    current_category = None
    selected_tags = []

    if category_slug:
        current_category = Category.objects.filter(slug=category_slug).first()
        if current_category:
            qs = qs.filter(category=current_category)

    if tags_param:
        tag_slugs = [s.strip() for s in tags_param.split(',') if s.strip()]
        if tag_slugs:
            selected_tags = list(Tag.objects.filter(slug__in=tag_slugs))
            # Filter articles that have ANY of the selected tags (OR logic)
            qs = qs.filter(tags__in=selected_tags).distinct()

    # Get featured articles (separate from regular articles)
    featured_articles = qs.filter(is_featured=True).order_by('featured_order', '-published_at')[:3]

    # Regular articles (non-featured) ordered by published date
    regular_articles = qs.filter(is_featured=False).order_by('-published_at')

    # Get all categories with article counts (excluding technical pages)
    categories_with_counts = Category.objects.annotate(
        article_count=Count('articles', filter=Q(articles__status='published', articles__is_page=False))
    ).filter(article_count__gt=0).order_by('name')

    # Get all tags with article counts (excluding technical pages)
    tags_with_counts = Tag.objects.annotate(
        article_count=Count('articles', filter=Q(articles__status='published', articles__is_page=False))
    ).filter(article_count__gt=0).order_by('name')

    # Group tags by category for modal - optimized query
    # Get all articles with their tags and categories in one query
    from django.db.models import Prefetch

    articles_for_tags = get_published_articles_queryset().filter(
        is_page=False
    ).select_related('category').prefetch_related('tags')

    # Build tag to category mapping
    tag_category_mapping = {}
    for article in articles_for_tags:
        if article.category:
            for tag in article.tags.all():
                if tag.id not in tag_category_mapping:
                    tag_category_mapping[tag.id] = {}
                cat_id = article.category.id
                if cat_id not in tag_category_mapping[tag.id]:
                    tag_category_mapping[tag.id][cat_id] = {
                        'category': article.category,
                        'count': 0
                    }
                tag_category_mapping[tag.id][cat_id]['count'] += 1

    # Group tags by their most common category
    tags_by_category = {}
    for tag in tags_with_counts:
        # Find most common category for this tag
        if tag.id in tag_category_mapping and tag_category_mapping[tag.id]:
            most_common = max(tag_category_mapping[tag.id].values(), key=lambda x: x['count'])
            category = most_common['category']
        else:
            category = None

        category_key = category.id if category else 'general'
        category_name = category.name if category else 'Général'

        if category_key not in tags_by_category:
            tags_by_category[category_key] = {
                'name': category_name,
                'category': category,
                'tags': []
            }
        tags_by_category[category_key]['tags'].append(tag)

    # Sort categories by name, with "Général" at the end
    sorted_categories = sorted(
        tags_by_category.values(),
        key=lambda x: (x['name'] == 'Général', x['name'])
    )

    # Pagination: 12 articles per page (3 columns × 4 rows)
    paginator = Paginator(regular_articles, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get blog settings for SEO content
    blog_settings = BlogSettings.get_settings()

    context = {
        'featured_articles': featured_articles,
        'articles': page_obj.object_list,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'current_category': current_category,
        'selected_tags': selected_tags,
        'categories': categories_with_counts,
        'tags': tags_with_counts,
        'tags_by_category': sorted_categories,
        'blog_settings': blog_settings,
    }
    return render(request, 'blog/article_list.html', context)


def category_detail(request, slug):
    """Display articles for a specific category with dedicated SEO-optimized page."""
    category = get_object_or_404(Category, slug=slug)

    # Get published articles in this category (exclude technical pages)
    qs = get_published_articles_queryset().filter(
        is_page=False,
        category=category
    ).select_related('category', 'profile_author').prefetch_related('tags')

    # Handle tag filtering
    tags_param = request.GET.get('tags', '')
    selected_tags = []

    if tags_param:
        tag_slugs = [s.strip() for s in tags_param.split(',') if s.strip()]
        if tag_slugs:
            selected_tags = list(Tag.objects.filter(slug__in=tag_slugs))
            qs = qs.filter(tags__in=selected_tags).distinct()

    # Get featured articles in this category
    featured_articles = qs.filter(is_featured=True).order_by('featured_order', '-published_at')[:3]

    # Regular articles (non-featured) ordered by published date
    regular_articles = qs.filter(is_featured=False).order_by('-published_at')

    # Get all categories with article counts for sidebar
    categories_with_counts = Category.objects.annotate(
        article_count=Count('articles', filter=Q(articles__status='published', articles__is_page=False))
    ).filter(article_count__gt=0).order_by('name')

    # Get tags used in this category
    tags_with_counts = Tag.objects.filter(
        articles__category=category,
        articles__status='published',
        articles__is_page=False
    ).annotate(
        article_count=Count('articles', filter=Q(articles__status='published', articles__is_page=False))
    ).filter(article_count__gt=0).order_by('name').distinct()

    # Group tags by category for modal - optimized query
    # Since we're already in a category view, most tags will belong to this category
    # Get all articles in this category with their tags in one query
    articles_for_tags = Article.objects.filter(
        status='published',
        is_page=False,
        category=category
    ).prefetch_related('tags')

    # Build tag to category mapping (will mostly be the current category)
    tag_category_mapping = {}
    for article in articles_for_tags:
        for tag in article.tags.all():
            if tag.id not in tag_category_mapping:
                tag_category_mapping[tag.id] = {
                    'category': category,
                    'count': 0
                }
            tag_category_mapping[tag.id]['count'] += 1

    # Group tags by category
    tags_by_category = {}
    for tag in tags_with_counts:
        # Find category for this tag
        if tag.id in tag_category_mapping:
            tag_category = tag_category_mapping[tag.id]['category']
        else:
            tag_category = None

        category_key = tag_category.id if tag_category else 'general'
        category_name = tag_category.name if tag_category else 'Général'

        if category_key not in tags_by_category:
            tags_by_category[category_key] = {
                'name': category_name,
                'category': tag_category,
                'tags': []
            }
        tags_by_category[category_key]['tags'].append(tag)

    # Sort categories by name, with "Général" at the end
    sorted_categories = sorted(
        tags_by_category.values(),
        key=lambda x: (x['name'] == 'Général', x['name'])
    )

    # Pagination: 12 articles per page
    paginator = Paginator(regular_articles, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'featured_articles': featured_articles,
        'articles': page_obj.object_list,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'current_category': category,
        'selected_tags': selected_tags,
        'categories': categories_with_counts,
        'tags': tags_with_counts,
        'tags_by_category': sorted_categories,
    }
    return render(request, 'blog/category_detail.html', context)


def home(request):
    # Exclude technical pages from home page
    qs = get_published_articles_queryset().filter(is_page=False).order_by('-published_at')[:10]
    return render(request, 'base.html', {'articles': qs})


def get_client_ip(request):
    """Get the client's IP address from the request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@require_POST
def like_article(request, slug):
    """Toggle like for an article (authenticated users or session-based for anonymous)."""
    from .models import ArticleLike

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    try:
        article = get_object_or_404(Article, slug=slug, status='published')

        # Get or create session for anonymous users
        if not request.session.session_key:
            request.session.create()

        ip_address = get_client_ip(request)

        if request.user.is_authenticated:
            # For authenticated users - only use user field, session_key is NULL
            like, created = ArticleLike.objects.get_or_create(
                article=article,
                user=request.user,
                defaults={'ip_address': ip_address, 'session_key': None}
            )
            if not created:
                # Unlike if already liked
                like.delete()
                Article.objects.filter(pk=article.pk).update(likes=F('likes') - 1)
                article.refresh_from_db()
                return JsonResponse({'success': True, 'liked': False, 'likes': article.likes})
            else:
                # Add like
                Article.objects.filter(pk=article.pk).update(likes=F('likes') + 1)
                article.refresh_from_db()
                return JsonResponse({'success': True, 'liked': True, 'likes': article.likes})
        else:
            # For anonymous users - only use session_key, user is null
            session_key = request.session.session_key
            like, created = ArticleLike.objects.get_or_create(
                article=article,
                user=None,
                session_key=session_key,
                defaults={'ip_address': ip_address}
            )
            if not created:
                # Unlike if already liked
                like.delete()
                Article.objects.filter(pk=article.pk).update(likes=F('likes') - 1)
                article.refresh_from_db()
                return JsonResponse({'success': True, 'liked': False, 'likes': article.likes})
            else:
                # Add like
                Article.objects.filter(pk=article.pk).update(likes=F('likes') + 1)
                article.refresh_from_db()
                return JsonResponse({'success': True, 'liked': True, 'likes': article.likes})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def add_comment(request, slug):
    """Add a new comment to an article with rate limiting."""
    article = get_object_or_404(Article, slug=slug, status='published')

    # Rate limiting: max 3 comments per 10 minutes from same IP
    ip_address = get_client_ip(request)
    cache_key = f'comment_rate_{ip_address}'
    comment_count = cache.get(cache_key, 0)

    if comment_count >= 3:
        messages.error(request, "Trop de commentaires. Veuillez patienter quelques minutes.")
        return redirect(f'/{slug}/#comments')

    # Extra strict rate limit for THIS SPECIFIC article (to fight targeted spam)
    article_cache_key = f'comment_rate_{ip_address}_{article.id}'
    article_comment_count = cache.get(article_cache_key, 0)

    if article_comment_count >= 1:  # Max 1 comment per 10 min per article from same IP
        messages.error(request, "Vous avez déjà commenté cet article récemment.")
        return redirect(f'/{slug}/#comments')

    # For authenticated users, pre-fill name/email from profile before validation
    post_data = request.POST.copy()
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        post_data['author_name'] = request.user.profile.display_name
        post_data['author_email'] = request.user.profile.email or request.user.email

    form = CommentForm(post_data)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.article = article
        comment.ip_address = ip_address
        comment.user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]

        # If user is authenticated, link to profile and auto-approve
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            comment.author_profile = request.user.profile
            comment.author_name = request.user.profile.display_name
            comment.author_email = request.user.profile.email or request.user.email

            # Authenticated users get auto-approved comments
            comment.status = 'approved'
            comment.moderated_at = timezone.now()

            # Staff users as moderators
            if request.user.is_staff:
                comment.moderated_by = request.user

        # Check for duplicate comment (same text within last hour)
        recent_duplicate = ArticleComment.objects.filter(
            article=article,
            comment=comment.comment,
            created_at__gte=timezone.now() - timezone.timedelta(hours=1)
        ).exists()

        if recent_duplicate:
            messages.error(request, "Ce commentaire a déjà été posté récemment.")
            return redirect(f'/{slug}/#comments')

        # Check for similar comments (fuzzy matching to catch spam variations)
        import difflib
        recent_comments = ArticleComment.objects.filter(
            article=article,
            created_at__gte=timezone.now() - timezone.timedelta(hours=24)
        ).values_list('comment', flat=True)[:20]

        for recent in recent_comments:
            similarity = difflib.SequenceMatcher(None, comment.comment.lower(), recent.lower()).ratio()
            if similarity > 0.85:  # 85% similar = likely spam variation
                messages.error(request, "Un commentaire similaire a déjà été posté.")
                return redirect(f'/{slug}/#comments')

        comment.save()

        # Increment rate limit counters
        cache.set(cache_key, comment_count + 1, 600)  # 10 minutes global
        cache.set(article_cache_key, article_comment_count + 1, 600)  # 10 minutes per article

        # Notify admin if comment needs moderation
        if comment.status == 'pending':
            try:
                from django.core.mail import send_mail
                from django.conf import settings

                admin_subject = f"💬 Nouveau commentaire à modérer - {article.title}"
                admin_message = f"""
Nouveau commentaire en attente de modération:

Article: {article.title}
Auteur: {comment.author_name}
Email: {comment.author_email}
Date: {comment.created_at.strftime('%d/%m/%Y %H:%M')}

Commentaire:
{comment.comment}

Modérer dans l'admin:
{settings.BASE_URL}/admin/blog/articlecomment/{comment.id}/change/
                """.strip()

                send_mail(
                    subject=admin_subject,
                    message=admin_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.ADMIN_EMAIL],
                    fail_silently=True,
                )
            except Exception as e:
                logger.error(f"Failed to send admin notification for comment {comment.id}: {str(e)}")

        # Set cookies for unregistered users (remember name/email)
        response = redirect(f'/{slug}/#comments')
        if not request.user.is_authenticated:
            response.set_cookie('comment_author_name', comment.author_name, max_age=2592000)  # 30 days
            response.set_cookie('comment_author_email', comment.author_email, max_age=2592000)

        if comment.status == 'approved':
            messages.success(request, "Votre commentaire a été publié.")
        else:
            messages.success(request, "Votre commentaire a été soumis et sera publié après modération.")

        return response
    else:
        # Form has errors, redirect back with error messages
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, error)
        return redirect(f'/{slug}/#comments')