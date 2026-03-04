"""
Views for article management by authorized authors.
Separate from public blog views for cleaner organization.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils.text import slugify
from django.http import HttpResponseForbidden
from .models import Article, ArticleImage
from .forms import ArticleForm, ArticleImageFormSet


def check_article_permission(user):
    """Check if user has permission to write articles."""
    if user.is_staff:
        return True

    try:
        profile = user.profile
        return profile.can_write_articles
    except:
        return False


@login_required
def article_create(request):
    """Create a new article (requires can_write_articles permission)."""

    # Check permission
    if not check_article_permission(request.user):
        messages.error(request, "Vous n'avez pas la permission de créer des articles.")
        return redirect('profiles:dashboard')

    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, user_profile=request.user.profile)
        formset = ArticleImageFormSet(request.POST, request.FILES)

        if form.is_valid() and formset.is_valid():
            article = form.save(commit=False)

            # Set author
            article.profile_author = request.user.profile

            # Auto-generate slug if not provided
            if not article.slug:
                base_slug = slugify(article.title)[:200]
                slug = base_slug
                i = 1
                while Article.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{i}"
                    i += 1
                article.slug = slug

            # Set status based on user role
            if not request.user.is_staff:
                # Non-staff users must go through moderation
                if article.status == 'published':
                    article.status = 'review'
                    messages.warning(request, "Votre article a été soumis pour modération.")

            article.save()
            form.save_m2m()  # Save tags relationship

            # Save images
            formset.instance = article
            formset.save()

            # Send notification to admin if article is pending review
            if article.status == 'review':
                notify_admin_new_article(article)

            messages.success(request, f"Article '{article.title}' créé avec succès!")
            return redirect('profiles:dashboard')
    else:
        form = ArticleForm(user_profile=request.user.profile)
        formset = ArticleImageFormSet()

    return render(request, 'blog/article_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Nouvelle article',
        'submit_text': 'Créer l\'article'
    })


@login_required
def article_edit(request, slug):
    """Edit an existing article (author or staff only)."""

    article = get_object_or_404(Article, slug=slug)

    # Check permission: must be author or staff
    if article.profile_author != request.user.profile and not request.user.is_staff:
        return HttpResponseForbidden("Vous n'avez pas la permission de modifier cet article.")

    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article, user_profile=request.user.profile)
        formset = ArticleImageFormSet(request.POST, request.FILES, instance=article)

        if form.is_valid() and formset.is_valid():
            article = form.save(commit=False)

            # Non-staff users changing to published triggers review
            if not request.user.is_staff and article.status == 'published':
                article.status = 'review'
                messages.warning(request, "Votre article a été soumis pour modération.")
                notify_admin_new_article(article, is_edit=True)

            article.save()
            form.save_m2m()

            # Save images
            formset.save()

            messages.success(request, f"Article '{article.title}' modifié avec succès!")
            return redirect('profiles:dashboard')
    else:
        form = ArticleForm(instance=article, user_profile=request.user.profile)
        formset = ArticleImageFormSet(instance=article)

    return render(request, 'blog/article_form.html', {
        'form': form,
        'formset': formset,
        'article': article,
        'title': f'Modifier: {article.title}',
        'submit_text': 'Enregistrer les modifications'
    })


@login_required
def article_delete(request, slug):
    """Delete an article (author or staff only)."""

    article = get_object_or_404(Article, slug=slug)

    # Check permission
    if article.profile_author != request.user.profile and not request.user.is_staff:
        return HttpResponseForbidden("Vous n'avez pas la permission de supprimer cet article.")

    if request.method == 'POST':
        title = article.title
        article.delete()
        messages.success(request, f"Article '{title}' supprimé avec succès.")
        return redirect('profiles:dashboard')

    return render(request, 'blog/article_confirm_delete.html', {'article': article})


def notify_admin_new_article(article, is_edit=False):
    """Send email notification to admin when article is submitted for review."""

    try:
        subject = f"{'Modification' if is_edit else 'Nouvel'} article en attente de modération"
        message = f"""
Un article a été {'modifié et' if is_edit else ''} soumis pour modération:

Titre: {article.title}
Auteur: {article.profile_author.display_name}
Slug: {article.slug}

Veuillez vérifier et approuver l'article dans l'admin Django:
{settings.BASE_URL}/admin/blog/article/{article.pk}/change/

"""

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
            fail_silently=True,
        )
    except Exception as e:
        # Log error but don't fail the request
        print(f"Failed to send admin notification: {e}")
