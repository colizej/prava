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
            'difficulty', 'is_active', 'is_official', 'source', 'image',
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
