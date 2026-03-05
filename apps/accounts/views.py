from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Avg, Count, Q

from .models import UserProfile, DailyQuota
from .forms import CustomUserCreationForm, UserProfileForm
from apps.examens.models import TestAttempt, StudyList, SavedQuestion, Question
from apps.shop.models import Order


def register(request):
    """Inscription d'un nouvel utilisateur."""
    if request.user.is_authenticated:
        return redirect('main:home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Bienvenue! Votre compte a été créé.')
            return redirect('main:home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Connexion."""
    if request.user.is_authenticated:
        return redirect('main:home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'main:home')
            return redirect(next_url)
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')

    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    """Déconnexion."""
    logout(request)
    messages.info(request, 'Vous avez été déconnecté.')
    return redirect('main:home')


@login_required
def profile(request):
    """Page de profil utilisateur."""
    profile = request.user.profile

    # Recent test attempts
    recent_attempts = TestAttempt.objects.filter(
        user=request.user
    ).order_by('-started_at')[:10]

    # Stats
    stats = TestAttempt.objects.filter(user=request.user).aggregate(
        total_tests=Count('id'),
        avg_score=Avg('percentage'),
    )

    # Daily quota
    can_answer, quota = DailyQuota.can_answer(request.user)

    # Saved questions — per list with counts
    study_lists = StudyList.objects.filter(is_active=True).annotate(
        user_count=Count(
            'saved_questions',
            filter=Q(saved_questions__user=request.user)
        )
    ).order_by('order')
    saved_total = SavedQuestion.objects.filter(user=request.user).count()

    # Category breakdown for saved questions
    saved_question_ids = SavedQuestion.objects.filter(
        user=request.user
    ).values_list('question_id', flat=True)
    saved_by_category = (
        Question.objects.filter(id__in=saved_question_ids)
        .values('category__name', 'category__icon')
        .annotate(cnt=Count('id'))
        .order_by('-cnt')[:5]
    )

    # Purchase history
    orders = Order.objects.filter(
        user=request.user
    ).select_related('plan').order_by('-created_at')[:20]

    context = {
        'profile': profile,
        'recent_attempts': recent_attempts,
        'stats': stats,
        'can_answer': can_answer,
        'quota': quota,
        'study_lists': study_lists,
        'saved_total': saved_total,
        'saved_by_category': saved_by_category,
        'orders': orders,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit(request):
    """Modifier le profil."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil mis à jour!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user.profile)

    return render(request, 'accounts/profile_edit.html', {'form': form})


@login_required
def dashboard(request):
    """Tableau de bord utilisateur."""
    profile = request.user.profile
    can_answer, quota = DailyQuota.can_answer(request.user)

    # Stats summary
    total_tests = TestAttempt.objects.filter(user=request.user).count()
    passed_tests = TestAttempt.objects.filter(user=request.user, passed=True).count()

    context = {
        'profile': profile,
        'can_answer': can_answer,
        'quota': quota,
        'total_tests': total_tests,
        'passed_tests': passed_tests,
    }
    return render(request, 'accounts/dashboard.html', context)
