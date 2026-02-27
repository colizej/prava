from django.contrib import admin
from django.utils.html import format_html, escape
from django.utils.safestring import mark_safe
from .models import ExamCategory, Question, AnswerOption, TestAttempt


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
            'fields': ('text', 'image', 'explanation'),
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

    @admin.display(description='Aperçu de la carte')
    def card_preview(self, obj):
        if not obj.pk:
            return '—  Enregistrez d\'abord la question pour voir l\'aperçu.'

        options = obj.options.all().order_by('order')
        if not options.exists():
            return '—  Ajoutez des options de réponse pour voir l\'aperçu.'

        # Build options HTML
        options_html = ''
        for opt in options:
            if opt.is_correct:
                border = 'border-left: 4px solid #22c55e;'
                bg = 'background: #f0fdf4;'
                badge_bg = 'background: #22c55e; color: #fff;'
                icon = ' ✓'
            else:
                border = 'border-left: 4px solid #e5e7eb;'
                bg = 'background: #fff;'
                badge_bg = 'background: #f3f4f6; color: #6b7280;'
                icon = ''
            options_html += f'''
            <div style="{border} {bg} padding: 12px 16px; border-radius: 8px; margin-bottom: 8px; display: flex; align-items: center;">
                <span style="{badge_bg} width: 28px; height: 28px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-weight: 600; font-size: 13px; margin-right: 12px; flex-shrink: 0;">{escape(opt.letter)}</span>
                <span style="color: #111827; font-size: 14px;">{escape(opt.text)}{icon}</span>
            </div>'''

        # Image block
        image_html = ''
        if obj.image:
            image_html = f'''
            <div style="flex: 0 0 45%; display: flex; align-items: flex-start; justify-content: center;">
                <img src="{obj.image.url}" style="max-width: 100%; max-height: 280px; object-fit: contain; border-radius: 8px; border: 1px solid #e5e7eb; background: #f9fafb; padding: 8px;">
            </div>'''

        # Explanation
        explanation_html = ''
        if obj.explanation:
            explanation_html = f'''
            <div style="margin-top: 12px; padding: 12px 16px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px;">
                <div style="font-weight: 600; color: #166534; font-size: 13px; margin-bottom: 4px;">💡 Explication</div>
                <div style="color: #374151; font-size: 13px; line-height: 1.5;">{escape(obj.explanation)}</div>
            </div>'''

        # Code reference
        ref_html = ''
        if obj.code_article:
            ref_html = f'''
            <div style="margin-top: 8px;">
                <a href="/admin/reglementation/codearticle/{obj.code_article.pk}/change/" style="font-size: 13px; color: #2563eb;">📖 {escape(obj.code_article.article_number)}</a>
            </div>'''

        # Difficulty badge
        diff_colors = {1: ('#22c55e', 'Facile'), 2: ('#eab308', 'Moyen'), 3: ('#ef4444', 'Difficile')}
        d_color, d_label = diff_colors.get(obj.difficulty, ('#9ca3af', '?'))
        diff_html = f'<span style="background: {d_color}; color: #fff; font-size: 11px; padding: 2px 8px; border-radius: 9999px; font-weight: 600;">{d_label}</span>'

        # Category badge
        cat_html = ''
        if obj.category:
            cat_html = f'<span style="background: #eff6ff; color: #2563eb; font-size: 11px; padding: 2px 8px; border-radius: 9999px; font-weight: 600; margin-left: 6px;">{escape(obj.category.name)}</span>'

        # Assemble the card
        layout_style = 'display: flex; gap: 24px;' if obj.image else ''
        question_width = 'flex: 1; min-width: 0;' if obj.image else ''

        return mark_safe(f'''
        <div style="max-width: 800px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            <div style="background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,.08);">
                <div style="margin-bottom: 12px;">{diff_html}{cat_html}</div>
                <div style="{layout_style}">
                    <div style="{question_width}">
                        <h3 style="font-size: 16px; font-weight: 600; color: #111827; margin: 0 0 20px 0; line-height: 1.5;">{escape(obj.text)}</h3>
                        <div>{options_html}</div>
                    </div>
                    {image_html}
                </div>
                {explanation_html}
                {ref_html}
            </div>
        </div>
        ''')


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
