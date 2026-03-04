import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Count, Q

from .models import ExamCategory, Question, TestAttempt, StudyList, SavedQuestion
from apps.accounts.models import DailyQuota


def categories(request):
    """Liste des catégories d'examen."""
    cats = ExamCategory.objects.filter(is_active=True).annotate(
        question_count=Count('questions', filter=Q(questions__is_active=True))
    ).order_by('order')

    # Study lists with per-user saved counts
    if request.user.is_authenticated:
        study_lists = StudyList.objects.filter(is_active=True).annotate(
            user_count=Count(
                'saved_questions',
                filter=Q(saved_questions__user=request.user)
            )
        ).order_by('order')
    else:
        study_lists = StudyList.objects.none()

    context = {
        'categories': cats,
        'study_lists': study_lists,
    }
    return render(request, 'examens/categories.html', context)


@login_required
def practice(request, category_slug=None):
    """Mode entraînement."""
    # Check quota
    can_answer, quota = DailyQuota.can_answer(request.user)
    if not can_answer:
        return redirect('main:pricing')

    # Get questions
    questions = Question.objects.filter(is_active=True).prefetch_related('options')

    category = None
    if category_slug:
        category = get_object_or_404(ExamCategory, slug=category_slug, is_active=True)
        questions = questions.filter(category=category)

    # Random 20 questions
    questions = questions.order_by('?')[:20]

    # Serialize for Alpine.js
    questions_data = []
    for q in questions:
        questions_data.append({
            'id': q.id,
            'text': q.text,
            'image': q.image.url if q.image else None,
            'options': [
                {
                    'letter': opt.letter,
                    'text': opt.text,
                    'is_correct': opt.is_correct,
                }
                for opt in q.options.all()
            ],
            'explanation': q.explanation,
            'code_reference': {
                'article': q.code_article.article_number,
                'url': q.code_article.get_absolute_url(),
            } if q.code_article else None,
        })

    # Store test type in session
    request.session['test_type'] = 'practice'
    request.session['category_id'] = category.id if category else None

    context = {
        'category': category,
        'questions_json': json.dumps(questions_data),
        'time_limit': 0,  # No time limit
        'test_type': 'practice',
    }
    return render(request, 'examens/quiz.html', context)


@login_required
def exam_mode(request):
    """Mode examen simulé (50 questions, 30 minutes)."""
    # Premium only (staff/superuser bypass)
    if not request.user.is_staff and not request.user.profile.has_active_premium:
        return redirect('main:pricing')

    questions = Question.objects.filter(
        is_active=True
    ).prefetch_related('options').order_by('?')[:50]

    questions_data = []
    for q in questions:
        questions_data.append({
            'id': q.id,
            'text': q.text,
            'image': q.image.url if q.image else None,
            'options': [
                {
                    'letter': opt.letter,
                    'text': opt.text,
                    'is_correct': opt.is_correct,
                }
                for opt in q.options.all()
            ],
            'explanation': q.explanation,
            'code_reference': {
                'article': q.code_article.article_number,
                'url': q.code_article.get_absolute_url(),
            } if q.code_article else None,
        })

    request.session['test_type'] = 'exam'
    request.session['category_id'] = None

    context = {
        'questions_json': json.dumps(questions_data),
        'time_limit': 1800,  # 30 minutes
        'test_type': 'exam',
    }
    return render(request, 'examens/quiz.html', context)


@login_required
def results(request, uuid):
    """Page de résultats."""
    attempt = get_object_or_404(TestAttempt, uuid=uuid, user=request.user)

    # Get detailed question data
    question_ids = [a['question_id'] for a in attempt.answers_data if 'question_id' in a]
    questions_map = {
        q.id: q for q in Question.objects.filter(
            id__in=question_ids
        ).prefetch_related('options')
    }

    detailed_results = []
    for answer in attempt.answers_data:
        q = questions_map.get(answer.get('question_id'))
        if q:
            detailed_results.append({
                'question': q,
                'selected': answer.get('selected_option'),
                'is_correct': answer.get('is_correct'),
                'time_spent': answer.get('time_spent', 0),
            })

    # Saved questions state for bookmark buttons
    default_list = StudyList.objects.filter(is_active=True).order_by('order').first()
    saved_ids = set()
    if default_list:
        saved_ids = set(
            SavedQuestion.objects.filter(
                user=request.user,
                study_list=default_list,
                question_id__in=question_ids,
            ).values_list('question_id', flat=True)
        )

    context = {
        'attempt': attempt,
        'detailed_results': detailed_results,
        'default_list': default_list,
        'saved_ids_json': json.dumps(list(saved_ids)),
    }
    return render(request, 'examens/results.html', context)


@login_required
def history(request):
    """Historique des tentatives."""
    attempts = TestAttempt.objects.filter(
        user=request.user
    ).select_related('category').order_by('-started_at')[:50]

    context = {
        'attempts': attempts,
    }
    return render(request, 'examens/history.html', context)


# ============================================================================
# API Endpoints
# ============================================================================

@require_POST
@login_required
def api_record_answer(request):
    """API: enregistrer une réponse."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    question_id = data.get('question_id')
    is_correct = data.get('is_correct', False)

    try:
        question = Question.objects.get(id=question_id)
        question.record_answer(is_correct)
    except Question.DoesNotExist:
        return JsonResponse({'error': 'Question not found'}, status=404)

    # Update user profile stats
    request.user.profile.increment_stats(is_correct)

    # Update quota
    if not request.user.profile.has_active_premium:
        quota = DailyQuota.get_or_create_today(request.user)
        quota.increment()

    return JsonResponse({'status': 'ok'})


@login_required
@staff_member_required
def question_preview(request, pk):
    """Admin preview: render a single question in the real quiz UI."""
    question = get_object_or_404(Question.objects.prefetch_related('options'), pk=pk)

    questions_data = [{
        'id': question.id,
        'text': question.text,
        'image': question.image.url if question.image else None,
        'options': [
            {
                'letter': opt.letter,
                'text': opt.text,
                'is_correct': opt.is_correct,
            }
            for opt in question.options.all()
        ],
        'explanation': question.explanation,
        'code_reference': {
            'article': question.code_article.article_number,
            'url': question.code_article.get_absolute_url(),
        } if question.code_article else None,
    }]

    context = {
        'category': question.category,
        'questions_json': json.dumps(questions_data),
        'time_limit': 0,
        'test_type': 'preview',
        'is_preview': True,
        'preview_question_id': question.pk,
        'question_timer': 0,
    }
    return render(request, 'examens/quiz.html', context)


@login_required
@require_POST
def api_finish_quiz(request):
    """API: terminer un quiz et sauvegarder les résultats."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    answers = data.get('answers', [])
    test_type = request.session.get('test_type', 'practice')
    category_id = request.session.get('category_id')

    attempt = TestAttempt.objects.create(
        user=request.user,
        test_type=test_type,
        category_id=category_id,
        answers_data=answers,
        total_questions=len(answers),
    )
    attempt.calculate_results()

    return JsonResponse({
        'uuid': str(attempt.uuid),
        'score': attempt.score,
        'total': attempt.total_questions,
        'percentage': float(attempt.percentage),
        'passed': attempt.passed,
        'url': attempt.get_absolute_url(),
    })


# ─── Saved Questions / Révisions ─────────────────────────────────────────────

@require_POST
@login_required
def api_toggle_saved(request):
    """API: ajouter/retirer une question d'une liste de révision."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    question_id = data.get('question_id')
    list_slug = data.get('list_slug')

    try:
        question = Question.objects.get(id=question_id, is_active=True)
    except Question.DoesNotExist:
        return JsonResponse({'error': 'Question not found'}, status=404)

    try:
        study_list = StudyList.objects.get(slug=list_slug, is_active=True)
    except StudyList.DoesNotExist:
        return JsonResponse({'error': 'List not found'}, status=404)

    obj, created = SavedQuestion.objects.get_or_create(
        user=request.user, question=question, study_list=study_list
    )
    if not created:
        obj.delete()
        is_saved = False
    else:
        is_saved = True

    count = SavedQuestion.objects.filter(
        user=request.user, study_list=study_list
    ).count()
    return JsonResponse({'saved': is_saved, 'count': count})


@login_required
def my_list(request, list_slug=None):
    """Page 'Mes révisions' — liste des questions sauvegardées."""
    all_lists = StudyList.objects.filter(is_active=True).order_by('order')
    if not all_lists.exists():
        return render(request, 'examens/my_list.html', {
            'study_list': None, 'all_lists': [], 'saved_items': []
        })

    if list_slug:
        study_list = get_object_or_404(StudyList, slug=list_slug, is_active=True)
    else:
        study_list = all_lists.first()

    saved_items = (
        SavedQuestion.objects
        .filter(user=request.user, study_list=study_list)
        .select_related('question__category')
        .prefetch_related('question__options')
        .order_by('-saved_at')
    )

    # Count per list for badges
    list_counts = {
        sq['study_list_id']: sq['cnt']
        for sq in SavedQuestion.objects.filter(user=request.user)
        .values('study_list_id')
        .annotate(cnt=Count('id'))
    }

    context = {
        'study_list': study_list,
        'all_lists': all_lists,
        'saved_items': saved_items,
        'list_counts': list_counts,
    }
    return render(request, 'examens/my_list.html', context)


@login_required
def practice_saved(request, list_slug=None):
    """Lancer un entraînement avec les questions d'une liste de révision."""
    all_lists = StudyList.objects.filter(is_active=True).order_by('order')
    if list_slug:
        study_list = get_object_or_404(StudyList, slug=list_slug, is_active=True)
    else:
        study_list = get_object_or_404(StudyList, is_active=True)

    questions = (
        Question.objects.filter(
            saved_by__user=request.user,
            saved_by__study_list=study_list,
            is_active=True,
        )
        .prefetch_related('options')
        .distinct()
    )

    if not questions.exists():
        from django.contrib import messages
        messages.warning(request, 'Votre liste de révision est vide.')
        return redirect('examens:my_list')

    questions_data = []
    for q in questions:
        questions_data.append({
            'id': q.id,
            'text': q.text,
            'image': q.image.url if q.image else None,
            'options': [
                {'letter': opt.letter, 'text': opt.text, 'is_correct': opt.is_correct}
                for opt in q.options.all()
            ],
            'explanation': q.explanation,
            'code_reference': {
                'article': q.code_article.article_number,
                'url': q.code_article.get_absolute_url(),
            } if q.code_article else None,
        })

    request.session['test_type'] = 'practice'
    request.session['category_id'] = None

    context = {
        'study_list': study_list,
        'questions_json': json.dumps(questions_data),
        'time_limit': 0,
        'test_type': 'practice_saved',
        'category': None,
    }
    return render(request, 'examens/quiz.html', context)
