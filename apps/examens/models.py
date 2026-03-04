import uuid
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone


class ExamCategory(models.Model):
    """Catégorie de questions d'examen."""
    name = models.CharField('Nom (FR)', max_length=150)
    name_nl = models.CharField('Naam (NL)', max_length=150, blank=True)
    name_ru = models.CharField('Название (RU)', max_length=150, blank=True)

    slug = models.SlugField(unique=True)
    icon = models.CharField('Icône', max_length=50, blank=True)
    description = models.TextField('Description (FR)', blank=True)
    description_nl = models.TextField('Beschrijving (NL)', blank=True)
    description_ru = models.TextField('Описание (RU)', blank=True)

    order = models.IntegerField('Ordre', default=0)
    is_active = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Catégorie examen'
        verbose_name_plural = 'Catégories examen'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('examens:category', kwargs={'slug': self.slug})

    def get_name(self, lang='fr'):
        if lang == 'nl' and self.name_nl:
            return self.name_nl
        if lang == 'ru' and self.name_ru:
            return self.name_ru
        return self.name

    @property
    def active_questions_count(self):
        return self.questions.filter(is_active=True).count()


class Question(models.Model):
    """Question d'examen."""
    DIFFICULTY_CHOICES = [
        (1, 'Facile'),
        (2, 'Moyen'),
        (3, 'Difficile'),
    ]

    category = models.ForeignKey(
        ExamCategory, on_delete=models.CASCADE,
        related_name='questions', verbose_name='Catégorie'
    )
    code_article = models.ForeignKey(
        'reglementation.CodeArticle', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='questions',
        verbose_name='Article du code'
    )
    traffic_sign = models.ForeignKey(
        'reglementation.TrafficSign', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='questions',
        verbose_name='Panneau'
    )

    # Question text
    text = models.TextField('Question (FR)')
    text_nl = models.TextField('Vraag (NL)', blank=True)
    text_ru = models.TextField('Вопрос (RU)', blank=True)

    # Image
    image = models.ImageField('Image', upload_to='questions/', blank=True)
    image_prompt = models.TextField('Prompt image', blank=True,
                                    help_text='Description pour génération d\'image (AI)')
    image_sign_code = models.CharField('Code panneau', max_length=20, blank=True,
                                       help_text='Ex: C43, F5 — panneau suggéré pour l\'image')

    # Explanation
    explanation = models.TextField('Explication (FR)', blank=True)
    explanation_nl = models.TextField('Uitleg (NL)', blank=True)
    explanation_ru = models.TextField('Объяснение (RU)', blank=True)

    # Metadata
    difficulty = models.IntegerField('Difficulté', choices=DIFFICULTY_CHOICES, default=2)
    is_active = models.BooleanField('Actif', default=True)
    is_official = models.BooleanField('Question officielle', default=False,
                                      help_text='Provient d\'un examen officiel')
    source = models.CharField('Source', max_length=200, blank=True)
    tags = models.JSONField('Tags', default=list, blank=True)

    # Statistics
    times_answered = models.IntegerField('Fois répondu', default=0)
    times_correct = models.IntegerField('Fois correct', default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['category', 'difficulty', '-created_at']

    def __str__(self):
        return f'Q{self.id}: {self.text[:80]}...' if len(self.text) > 80 else f'Q{self.id}: {self.text}'

    def get_text(self, lang='fr'):
        if lang == 'nl' and self.text_nl:
            return self.text_nl
        if lang == 'ru' and self.text_ru:
            return self.text_ru
        return self.text

    def get_explanation(self, lang='fr'):
        if lang == 'nl' and self.explanation_nl:
            return self.explanation_nl
        if lang == 'ru' and self.explanation_ru:
            return self.explanation_ru
        return self.explanation

    @property
    def success_rate(self):
        if self.times_answered == 0:
            return 0
        return round(self.times_correct / self.times_answered * 100, 1)

    @property
    def correct_option(self):
        return self.options.filter(is_correct=True).first()

    def record_answer(self, is_correct):
        self.times_answered += 1
        if is_correct:
            self.times_correct += 1
        self.save(update_fields=['times_answered', 'times_correct'])


class AnswerOption(models.Model):
    """Option de réponse pour une question."""
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE,
        related_name='options', verbose_name='Question'
    )
    letter = models.CharField('Lettre', max_length=2, help_text='A, B, C, D')

    text = models.CharField('Réponse (FR)', max_length=500)
    text_nl = models.CharField('Antwoord (NL)', max_length=500, blank=True)
    text_ru = models.CharField('Ответ (RU)', max_length=500, blank=True)

    is_correct = models.BooleanField('Correcte', default=False)
    order = models.IntegerField('Ordre', default=0)

    class Meta:
        verbose_name = 'Option de réponse'
        verbose_name_plural = 'Options de réponse'
        ordering = ['order', 'letter']

    def __str__(self):
        return f'{self.letter}. {self.text[:50]}'

    def get_text(self, lang='fr'):
        if lang == 'nl' and self.text_nl:
            return self.text_nl
        if lang == 'ru' and self.text_ru:
            return self.text_ru
        return self.text


class TestAttempt(models.Model):
    """Tentative de test par un utilisateur."""
    TEST_TYPES = [
        ('practice', 'Entraînement'),
        ('exam', 'Examen simulé'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_attempts')
    test_type = models.CharField('Type', max_length=20, choices=TEST_TYPES, default='practice')
    category = models.ForeignKey(
        ExamCategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='attempts'
    )

    # Results
    answers_data = models.JSONField('Données des réponses', default=list)
    score = models.IntegerField('Score', default=0)
    total_questions = models.IntegerField('Total questions', default=0)
    percentage = models.DecimalField('Pourcentage', max_digits=5, decimal_places=2, default=0)
    passed = models.BooleanField('Réussi', default=False)

    # Timing
    started_at = models.DateTimeField('Début', auto_now_add=True)
    completed_at = models.DateTimeField('Fin', blank=True, null=True)
    time_spent = models.IntegerField('Temps (sec)', default=0)

    class Meta:
        verbose_name = 'Tentative de test'
        verbose_name_plural = 'Tentatives de test'
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.user.username} — {self.test_type} — {self.percentage}%'

    def get_absolute_url(self):
        return reverse('examens:results', kwargs={'uuid': self.uuid})

    def calculate_results(self):
        """Calcule les résultats à partir des données de réponse."""
        if not self.answers_data:
            return

        correct = sum(1 for a in self.answers_data if a.get('is_correct'))
        total = len(self.answers_data)

        self.score = correct
        self.total_questions = total
        self.percentage = round(correct / total * 100, 2) if total > 0 else 0
        self.passed = self.percentage >= 80  # 80% pour réussir en Belgique
        self.completed_at = timezone.now()

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.time_spent = int(delta.total_seconds())

        self.save()


# ─── Saved Questions (Révisions) ──────────────────────────────────────────────

class StudyList(models.Model):
    """Liste de révision gérée par l'admin (ex: 'À revoir', 'Difficile')."""
    name = models.CharField('Nom', max_length=100)
    slug = models.SlugField('Slug', unique=True)
    icon = models.CharField('Icône (emoji)', max_length=10, default='📌')
    description = models.CharField('Description', max_length=200, blank=True)
    order = models.PositiveSmallIntegerField('Ordre', default=0)
    is_active = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Liste de révision'
        verbose_name_plural = 'Listes de révision'
        ordering = ['order', 'name']

    def __str__(self):
        return f'{self.icon} {self.name}'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('examens:my_list_slug', kwargs={'list_slug': self.slug})


class SavedQuestion(models.Model):
    """Question sauvegardée par un utilisateur dans une liste de révision."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='saved_questions'
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='saved_by'
    )
    study_list = models.ForeignKey(
        StudyList, on_delete=models.CASCADE, related_name='saved_questions'
    )
    saved_at = models.DateTimeField('Sauvegardé le', auto_now_add=True)

    class Meta:
        verbose_name = 'Question sauvegardée'
        verbose_name_plural = 'Questions sauvegardées'
        unique_together = ['user', 'question', 'study_list']
        ordering = ['-saved_at']

    def __str__(self):
        return f'{self.user.username} → Q{self.question_id} [{self.study_list}]'
