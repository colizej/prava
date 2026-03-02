from django import forms
from apps.examens.models import Question, AnswerOption, ExamCategory


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
