from django.contrib import admin
from django.utils.html import format_html, escape
from django.utils.safestring import mark_safe
from .models import ExamCategory, Question, AnswerOption, TestAttempt, StudyList, SavedQuestion


@admin.register(StudyList)
class StudyListAdmin(admin.ModelAdmin):
    list_display = ('icon', 'name', 'slug', 'saved_count', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

    @admin.display(description='Questions sauv.')
    def saved_count(self, obj):
        return obj.saved_questions.count()


@admin.register(SavedQuestion)
class SavedQuestionAdmin(admin.ModelAdmin):
    list_display = ('user', 'question_short', 'study_list', 'saved_at')
    list_filter = ('study_list', 'saved_at')
    search_fields = ('user__username', 'question__text')
    readonly_fields = ('saved_at',)
    raw_id_fields = ('question',)

    @admin.display(description='Question')
    def question_short(self, obj):
        return f'Q{obj.question_id}: {obj.question.text[:60]}'


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 3
    min_num = 2
    fields = ('letter', 'text', 'text_nl', 'text_ru', 'is_correct', 'order')


@admin.register(ExamCategory)
class ExamCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_nl', 'name_ru', 'slug', 'active_questions_count', 'order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('order', 'is_active')
    search_fields = ('name', 'name_nl', 'name_ru')

    @admin.display(description='Questions')
    def active_questions_count(self, obj):
        return obj.active_questions_count


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'short_text', 'category', 'difficulty_badge',
        'is_active', 'is_official', 'success_rate_display',
        'times_answered',
    )
    list_filter = ('category', 'difficulty', 'is_active', 'is_official', 'source')
    search_fields = ('text', 'text_nl', 'text_ru', 'explanation')
    list_editable = ('is_active', 'is_official')
    readonly_fields = ('times_answered', 'times_correct', 'success_rate_display', 'created_at', 'updated_at', 'card_preview')
    inlines = [AnswerOptionInline]

    fieldsets = (
        ('Aperçu de la carte', {
            'fields': ('card_preview',),
        }),
        ('Question FR', {
            'fields': ('text', 'image', 'image_caption', 'explanation'),
        }),
        ('Question NL', {
            'fields': ('text_nl', 'explanation_nl'),
            'classes': ('collapse',),
        }),
        ('Question RU', {
            'fields': ('text_ru', 'explanation_ru'),
            'classes': ('collapse',),
        }),
        ('Classification', {
            'fields': ('category', 'difficulty', 'code_article', 'traffic_sign', 'tags'),
        }),
        ('État', {
            'fields': ('is_active', 'is_official', 'source'),
        }),
        ('Statistiques', {
            'fields': ('times_answered', 'times_correct', 'success_rate_display', 'created_at', 'updated_at'),
        }),
    )

    @admin.display(description='Question')
    def short_text(self, obj):
        return obj.text[:80] + '...' if len(obj.text) > 80 else obj.text

    @admin.display(description='Difficulté')
    def difficulty_badge(self, obj):
        colors = {1: '🟢', 2: '🟡', 3: '🔴'}
        labels = {1: 'Facile', 2: 'Moyen', 3: 'Difficile'}
        return f'{colors.get(obj.difficulty, "⚪")} {labels.get(obj.difficulty, "?")}'

    @admin.display(description='Taux réussite')
    def success_rate_display(self, obj):
        return f'{obj.success_rate}%'

    @admin.display(description='Aperçu')
    def card_preview(self, obj):
        if not obj.pk:
            return '—  Enregistrez d\'abord la question.'
        from django.urls import reverse
        url = reverse('examens:question_preview', args=[obj.pk])
        return format_html(
            '<a href="{}" target="_blank" style="'
            'display: inline-flex; align-items: center; gap: 8px; '
            'background: #2563eb; color: #fff; padding: 8px 20px; '
            'border-radius: 8px; font-weight: 600; font-size: 13px; '
            'text-decoration: none; transition: background 0.2s;'
            '">'
            '👁 Voir la carte sur le site'
            '</a>',
            url,
        )


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'test_type', 'category', 'score',
        'total_questions', 'percentage', 'passed', 'started_at',
    )
    list_filter = ('test_type', 'passed', 'category', 'started_at')
    search_fields = ('user__username',)
    readonly_fields = (
        'uuid', 'user', 'test_type', 'category', 'answers_data',
        'score', 'total_questions', 'percentage', 'passed',
        'started_at', 'completed_at', 'time_spent',
    )
