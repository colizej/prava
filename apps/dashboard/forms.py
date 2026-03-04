from django import forms
import re
from apps.examens.models import Question, AnswerOption, ExamCategory
from apps.reglementation.models import CodeArticle


def _article_group_choices():
    """Build sorted choices of top-level article groups (e.g. '6' from '6.1.2', '22bis' from '22bis.1')."""
    numbers = CodeArticle.objects.values_list('article_number', flat=True).distinct()
    groups = set()
    for n in numbers:
        # '6.1.2'.split('.') → ['6', '1', '2'] → first part is group '6'
        parts = n.split('.')
        groups.add(parts[0].strip())

    def _sort_key(g):
        # Sort numerically by leading digits, then alphabetically for suffixes like '7bis'
        m = re.match(r'^(\d+)', g)
        return (int(m.group(1)) if m else float('inf'), g)

    sorted_groups = sorted(groups, key=_sort_key)
    return [('', 'Tous les articles')] + [(g, g) for g in sorted_groups]


class QuestionFilterForm(forms.Form):
    """Filter form for the questions list."""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Rechercher…',
            'class': 'w-full rounded-lg border-gray-300 shadow-sm text-sm focus:ring-blue-500',
        }),
    )
    category = forms.ModelChoiceField(
        queryset=ExamCategory.objects.all(),
        required=False,
        empty_label='Toutes les catégories',
        widget=forms.Select(attrs={
            'class': 'rounded-lg border-gray-300 shadow-sm text-sm focus:ring-blue-500',
        }),
    )
    article_group = forms.ChoiceField(
        choices=[],  # populated dynamically in __init__
        required=False,
        widget=forms.Select(attrs={
            'class': 'rounded-lg border-gray-300 shadow-sm text-sm focus:ring-blue-500',
        }),
    )
    difficulty = forms.ChoiceField(
        choices=[('', 'Toutes difficultés'), ('1', 'Facile'), ('2', 'Moyen'), ('3', 'Difficile')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'rounded-lg border-gray-300 shadow-sm text-sm focus:ring-blue-500',
        }),
    )
    is_active = forms.ChoiceField(
        choices=[('', 'Tous'), ('1', 'Actif'), ('0', 'Inactif')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'rounded-lg border-gray-300 shadow-sm text-sm focus:ring-blue-500',
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['article_group'].choices = _article_group_choices()


FIELD_CLASS = 'w-full rounded-lg border-gray-300 shadow-sm text-sm focus:ring-blue-500 focus:border-blue-500'
TEXTAREA_CLASS = FIELD_CLASS + ' resize-y'


class QuestionForm(forms.ModelForm):
    """Create / edit a Question."""

    class Meta:
        model = Question
        fields = [
            'category', 'code_article', 'traffic_sign',
            'text', 'text_nl', 'text_ru',
            'explanation', 'explanation_nl', 'explanation_ru',
            'difficulty', 'is_active', 'is_official', 'source', 'image', 'image_alt', 'image_caption',
        ]
        widgets = {
            'category': forms.Select(attrs={'class': FIELD_CLASS}),
            'code_article': forms.Select(attrs={'class': FIELD_CLASS}),
            'traffic_sign': forms.Select(attrs={'class': FIELD_CLASS}),
            'text': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 3}),
            'text_nl': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
            'text_ru': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
            'explanation': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
            'explanation_nl': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
            'explanation_ru': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
            'difficulty': forms.Select(attrs={'class': FIELD_CLASS}),
            'source': forms.TextInput(attrs={'class': FIELD_CLASS}),
            'image_alt': forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': 'Texte alternatif (SEO)'}),
            'image_caption': forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': 'Légende affichée sous l\'image'}),
        }


class AnswerOptionForm(forms.ModelForm):
    class Meta:
        model = AnswerOption
        fields = ['letter', 'text', 'text_nl', 'text_ru', 'is_correct', 'order']
        widgets = {
            'letter': forms.TextInput(attrs={'class': 'w-12 rounded border-gray-300 text-sm text-center', 'maxlength': 2}),
            'text': forms.TextInput(attrs={'class': FIELD_CLASS}),
            'text_nl': forms.TextInput(attrs={'class': FIELD_CLASS}),
            'text_ru': forms.TextInput(attrs={'class': FIELD_CLASS}),
            'order': forms.HiddenInput(),
        }


AnswerOptionFormSet = forms.inlineformset_factory(
    Question, AnswerOption,
    form=AnswerOptionForm,
    fields=['letter', 'text', 'text_nl', 'text_ru', 'is_correct', 'order'],
    extra=4,
    can_delete=True,
    min_num=2,
    validate_min=True,
)


# ─── Blog ──────────────────────────────────────────────────────────────────────

TEXTAREA_MD = 'w-full rounded-lg border border-gray-300 text-sm font-mono h-64 p-3 focus:outline-none focus:ring-2 focus:ring-blue-400'
INPUT_CLASS = 'w-full rounded-lg border border-gray-300 text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400'
TEXTAREA_SHORT = 'w-full rounded-lg border border-gray-300 text-sm h-20 p-3 focus:outline-none focus:ring-2 focus:ring-blue-400'


class BlogPostForm(forms.ModelForm):
    from apps.blog.models import BlogPost

    class Meta:
        from apps.blog.models import BlogPost
        model = BlogPost
        fields = [

            # Content FR
            'title', 'content', 'excerpt',
            # Content NL
            'title_nl', 'content_nl', 'excerpt_nl',
            # Content RU
            'title_ru', 'content_ru', 'excerpt_ru',
            # Meta
            'category', 'slug', 'featured_image', 'featured_image_alt', 'featured_image_caption',
            'is_published',
            # SEO
            'meta_title', 'meta_description', 'og_title', 'og_description',
            'keywords', 'canonical_url', 'no_index',
        ]
        widgets = {
            'title':       forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Titre (FR)'}),
            'title_nl':    forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Titel (NL)'}),
            'title_ru':    forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Заголовок (RU)'}),
            'content':     forms.Textarea(attrs={'class': TEXTAREA_MD, 'placeholder': 'Contenu Markdown (FR)'}),
            'content_nl':  forms.Textarea(attrs={'class': TEXTAREA_MD, 'placeholder': 'Inhoud Markdown (NL)'}),
            'content_ru':  forms.Textarea(attrs={'class': TEXTAREA_MD, 'placeholder': 'Содержание Markdown (RU)'}),
            'excerpt':     forms.Textarea(attrs={'class': TEXTAREA_SHORT, 'placeholder': 'Extrait (FR, max 300 car.)'}),
            'excerpt_nl':  forms.Textarea(attrs={'class': TEXTAREA_SHORT, 'placeholder': 'Uittreksel (NL)'}),
            'excerpt_ru':  forms.Textarea(attrs={'class': TEXTAREA_SHORT, 'placeholder': 'Отрывок (RU)'}),
            'slug':        forms.TextInput(attrs={'class': INPUT_CLASS}),
            'category':    forms.Select(attrs={'class': INPUT_CLASS}),
            'featured_image_alt': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'featured_image_caption': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Légende affichée sous l\'image'}),
            'meta_title':  forms.TextInput(attrs={'class': INPUT_CLASS, 'maxlength': 70}),
            'meta_description': forms.Textarea(attrs={'class': TEXTAREA_SHORT, 'maxlength': 160}),
            'keywords':    forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'mot1, mot2, mot3'}),
            'canonical_url': forms.URLInput(attrs={'class': INPUT_CLASS}),
            'og_title':    forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Open Graph title (FB/LinkedIn)'}),
            'og_description': forms.Textarea(attrs={'class': TEXTAREA_SHORT, 'placeholder': 'Open Graph description'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'rounded border border-gray-300 text-blue-600'}),
            'no_index':    forms.CheckboxInput(attrs={'class': 'rounded border border-gray-300 text-red-500'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Slug auto-generated from title — make optional
        self.fields['slug'].required = False
        self.fields['slug'].widget.attrs.update({'id': 'id_slug', 'placeholder': 'auto-généré depuis le titre FR'})
        self.fields['title'].widget.attrs.update({'id': 'id_title'})
