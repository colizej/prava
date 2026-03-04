import json
import subprocess
import sys
from pathlib import Path

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from apps.examens.models import AnswerOption, ExamCategory, Question, TestAttempt
from apps.reglementation.models import CodeArticle, RuleCategory

from .forms import AnswerOptionFormSet, QuestionFilterForm, QuestionForm

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# ─── Access decorator ─────────────────────────────────────────────────────────

def dashboard_view(view_func):
    """Shortcut: require staff login."""
    return staff_member_required(view_func, login_url='/accounts/login/')


# ─── Dashboard index ──────────────────────────────────────────────────────────

@dashboard_view
def index(request):
    ctx = {
        'title': 'Dashboard',
        'stats': {
            'articles': CodeArticle.objects.count(),
            'categories': RuleCategory.objects.count(),
            'questions': Question.objects.count(),
            'questions_active': Question.objects.filter(is_active=True).count(),
            'exam_categories': ExamCategory.objects.count(),
            'attempts': TestAttempt.objects.count(),
            'blog_posts': BlogPost.objects.count(),
            'blog_published': BlogPost.objects.filter(is_published=True).count(),
        },
        'recent_questions': Question.objects.select_related('category').order_by('-created_at')[:10],
        'scripts': [
            {
                'id': '01_scrape',
                'label': '01 — Scrape',
                'description': 'Télécharge les articles depuis le site officiel',
                'color': 'blue',
            },
            {
                'id': '02_translate',
                'label': '02 — Translate',
                'description': 'Traduit les articles en NL/RU',
                'color': 'purple',
            },
            {
                'id': '03_process',
                'label': '03 — Process',
                'description': 'Enrichit le contenu (HTML, définitions…)',
                'color': 'yellow',
            },
            {
                'id': '04_questions',
                'label': '04 — Questions',
                'description': 'Génère les questions d\'examen',
                'color': 'orange',
            },
            {
                'id': '05_import',
                'label': '05 — Import DB',
                'description': 'Importe les articles et questions dans la BDD',
                'color': 'green',
            },
        ],
    }
    return render(request, 'dashboard/index.html', ctx)


# ─── Script runner ────────────────────────────────────────────────────────────

@staff_member_required(login_url='/accounts/login/')
def run_script(request, script_id):
    """POST: run a pipeline script, return stdout/stderr as JSON."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    allowed = {'01_scrape', '02_translate', '03_process', '04_questions', '05_import'}
    if script_id not in allowed:
        return JsonResponse({'error': f'Unknown script: {script_id}'}, status=400)

    script_path = PROJECT_ROOT / 'scripts' / 'pipeline' / f'{script_id}.py'
    if not script_path.exists():
        return JsonResponse({'error': f'Script not found: {script_path.name}'}, status=404)

    extra_args = []
    if request.content_type == 'application/json':
        try:
            body = json.loads(request.body)
            if body.get('dry_run'):
                extra_args.append('--dry-run')
            if body.get('verbose'):
                extra_args.append('--verbose')
            if body.get('law'):
                extra_args += ['--law', str(body['law'])]
        except (json.JSONDecodeError, AttributeError):
            pass

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)] + extra_args,
            capture_output=True,
            text=True,
            timeout=300,  # 5 min max
            cwd=str(PROJECT_ROOT),
        )
        return JsonResponse({
            'success': result.returncode == 0,
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
        })
    except subprocess.TimeoutExpired:
        return JsonResponse({'error': 'Script timeout (5 min)', 'success': False}, status=504)
    except Exception as exc:
        return JsonResponse({'error': str(exc), 'success': False}, status=500)


# ─── Questions list ───────────────────────────────────────────────────────────

@dashboard_view
def questions_list(request):
    form = QuestionFilterForm(request.GET)
    qs = Question.objects.select_related('category', 'code_article').prefetch_related('options')

    if form.is_valid():
        search = form.cleaned_data.get('search')
        category = form.cleaned_data.get('category')
        article_group = form.cleaned_data.get('article_group')
        difficulty = form.cleaned_data.get('difficulty')
        is_active = form.cleaned_data.get('is_active')

        if search:
            qs = qs.filter(
                Q(text__icontains=search) |
                Q(text_nl__icontains=search) |
                Q(text_ru__icontains=search)
            )

        if category:
            qs = qs.filter(category=category)
        if article_group:
            # Match exact article (e.g. 'Art. 6') OR sub-articles ('Art. 6.1', 'Art. 6.2' …)
            qs = qs.filter(
                Q(code_article__article_number=article_group) |
                Q(code_article__article_number__startswith=article_group + '.')
            )
        if difficulty:
            qs = qs.filter(difficulty=int(difficulty))
        if is_active == '1':
            qs = qs.filter(is_active=True)
        elif is_active == '0':
            qs = qs.filter(is_active=False)

    total = qs.count()
    paginator = Paginator(qs.order_by('-created_at'), 50)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'dashboard/questions_list.html', {
        'title': 'Questions',
        'form': form,
        'page_obj': page,
        'total': total,
    })


# ─── Question detail (read) ───────────────────────────────────────────────────

@dashboard_view
def question_detail(request, pk):
    question = get_object_or_404(Question.objects.prefetch_related('options'), pk=pk)
    return render(request, 'dashboard/question_detail.html', {
        'title': f'Question #{pk}',
        'question': question,
    })


# ─── Question create ──────────────────────────────────────────────────────────

@dashboard_view
def question_create(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST, request.FILES)
        formset = AnswerOptionFormSet(request.POST, prefix='options')
        if form.is_valid() and formset.is_valid():
            question = form.save()
            formset.instance = question
            formset.save()
            messages.success(request, f'Question #{question.pk} créée.')
            return redirect('dashboard:questions')
    else:
        form = QuestionForm()
        formset = AnswerOptionFormSet(prefix='options')

    return render(request, 'dashboard/question_form.html', {
        'title': 'Nouvelle question',
        'form': form,
        'formset': formset,
        'action': 'create',
    })


# ─── Question edit ────────────────────────────────────────────────────────────

@dashboard_view
def question_edit(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.method == 'POST':
        form = QuestionForm(request.POST, request.FILES, instance=question)
        formset = AnswerOptionFormSet(request.POST, instance=question, prefix='options')
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f'Question #{pk} mise à jour.')
            return redirect('dashboard:question_detail', pk=pk)
    else:
        form = QuestionForm(instance=question)
        formset = AnswerOptionFormSet(instance=question, prefix='options')

    return render(request, 'dashboard/question_form.html', {
        'title': f'Modifier Q#{pk}',
        'form': form,
        'formset': formset,
        'action': 'edit',
        'question': question,
    })


# ─── Question delete ──────────────────────────────────────────────────────────

@dashboard_view
def question_delete(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.method == 'POST':
        question.delete()
        messages.success(request, f'Question #{pk} supprimée.')
        return redirect('dashboard:questions')
    return render(request, 'dashboard/question_confirm_delete.html', {
        'title': f'Supprimer Q#{pk}',
        'question': question,
    })


# ─── Toggle active ────────────────────────────────────────────────────────────

@staff_member_required(login_url='/accounts/login/')
def question_toggle_active(request, pk):
    """POST: toggle is_active flag, return JSON."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)
    question = get_object_or_404(Question, pk=pk)
    question.is_active = not question.is_active
    question.save(update_fields=['is_active'])
    return JsonResponse({'is_active': question.is_active, 'pk': pk})


# ─── Blog ─────────────────────────────────────────────────────────────────────

from apps.blog.models import BlogPost, BlogCategory
from .forms import BlogPostForm


@dashboard_view
def blog_list(request):
    q = request.GET.get('q', '').strip()
    posts = BlogPost.objects.select_related('author', 'category').order_by('-created_at')
    if q:
        posts = posts.filter(
            Q(title__icontains=q) | Q(title_ru__icontains=q) | Q(title_nl__icontains=q)
        )
    paginator = Paginator(posts, 20)
    page = request.GET.get('page')
    return render(request, 'dashboard/blog_list.html', {
        'title': 'Articles blog',
        'page_obj': paginator.get_page(page),
        'total': posts.count(),
        'q': q,
    })


@dashboard_view
def blog_create(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, f'Article « {post.title} » créé.')
            return redirect('dashboard:blog_edit', pk=post.pk)
    else:
        form = BlogPostForm()
    return render(request, 'dashboard/blog_form.html', {
        'title': 'Nouvel article',
        'form': form,
        'action': 'create',
    })


@dashboard_view
def blog_edit(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, f'Article « {post.title} » mis à jour.')
            return redirect('dashboard:blog_edit', pk=post.pk)
    else:
        form = BlogPostForm(instance=post)
    return render(request, 'dashboard/blog_form.html', {
        'title': f'Modifier — {post.title}',
        'form': form,
        'post': post,
        'action': 'edit',
    })


@dashboard_view
def blog_delete(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    if request.method == 'POST':
        title = post.title
        post.delete()
        messages.success(request, f'Article « {title} » supprimé.')
        return redirect('dashboard:blog_list')
    return render(request, 'dashboard/blog_confirm_delete.html', {
        'title': f'Supprimer « {post.title} » ?',
        'post': post,
    })
