import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Count, Q

from .models import ExamCategory, Question, TestAttempt
from apps.accounts.models import DailyQuota


def categories(request):
    """Liste des catégories d'examen."""
    cats = ExamCategory.objects.filter(is_active=True).annotate(
        question_count=Count('questions', filter=Q(questions__is_active=True))
    ).order_by('order')

    context = {
        'categories': cats,
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

    context = {
        'attempt': attempt,
        'detailed_results': detailed_results,
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


@require_POST
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
