from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.forms import inlineformset_factory
from .models import ArticleComment, Article, ArticleImage


class CommentForm(forms.ModelForm):
    """Form for creating article comments with spam protection."""

    # Honeypot field - hidden from users, bots will fill it
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'style': 'display:none !important;',
            'tabindex': '-1',
            'autocomplete': 'off'
        }),
        label=''
    )

    class Meta:
        model = ArticleComment
        fields = ['author_name', 'author_email', 'comment', 'parent']
        widgets = {
            'author_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition',
                'placeholder': 'Votre nom',
                'maxlength': '100'
            }),
            'author_email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition',
                'placeholder': 'Votre email (ne sera pas publié)',
                'maxlength': '254'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition resize-none',
                'placeholder': 'Votre commentaire...',
                'rows': '5',
                'maxlength': '2000'
            }),
            'parent': forms.HiddenInput()
        }
        labels = {
            'author_name': 'Nom',
            'author_email': 'Email',
            'comment': 'Commentaire',
        }

    def clean_website(self):
        """Check honeypot field - if filled, it's a bot."""
        website = self.cleaned_data.get('website', '')
        if website:
            raise ValidationError("Spam detected")
        return website

    def clean_comment(self):
        """Validate comment text."""
        comment = self.cleaned_data.get('comment', '').strip()

        if not comment:
            raise ValidationError("Le commentaire ne peut pas être vide")

        if len(comment) < 10:
            raise ValidationError("Le commentaire doit contenir au moins 10 caractères")

        if len(comment) > 2000:
            raise ValidationError("Le commentaire ne peut pas dépasser 2000 caractères")

        # Check for spam patterns
        import re

        # Count URLs in comment
        url_pattern = r'https?://[^\s]+'
        urls_found = re.findall(url_pattern, comment, re.IGNORECASE)
        if len(urls_found) >= 2:
            raise ValidationError("Trop de liens dans le commentaire")

        spam_patterns = [
            r'(viagra|cialis|casino|poker|lottery|forex|crypto|bitcoin|pharmacy)',  # Spam words
            r'(\w)\1{10,}',  # Repeated characters (aaaaaaaaaa)
            r'\b(click here|buy now|limited offer|act now|hurry up)\b',  # Spam phrases
            r'\$\d+',  # Dollar amounts (often spam)
        ]

        for pattern in spam_patterns:
            if re.search(pattern, comment, re.IGNORECASE):
                raise ValidationError("Contenu suspect détecté")

        return comment

    def clean_author_name(self):
        """Validate author name."""
        name = self.cleaned_data.get('author_name', '').strip()

        if not name:
            raise ValidationError("Le nom est requis")

        if len(name) < 2:
            raise ValidationError("Le nom doit contenir au moins 2 caractères")

        # Check for suspicious patterns
        if name.lower() in ['admin', 'administrator', 'moderator', 'webmaster']:
            raise ValidationError("Ce nom n'est pas autorisé")

        return name

    def clean_author_email(self):
        """Validate email."""
        email = self.cleaned_data.get('author_email', '').strip().lower()

        if not email:
            raise ValidationError("L'email est requis")

        # Check for disposable email domains (extended list)
        import re

        disposable_domains = [
            'tempmail.com', 'throwaway.email', '10minutemail.com',
            'guerrillamail.com', 'mailinator.com', 'maildrop.cc',
            'yopmail.com', 'temp-mail.org', 'fakeinbox.com',
            'sharklasers.com', 'grr.la', 'guerrillamail.info',
            'pokemail.net', 'spam4.me', 'trashmail.com',
            'mytrashmail.com', 'mailnesia.com', 'mailcatch.com'
        ]

        email_domain = email.split('@')[-1] if '@' in email else ''
        if email_domain in disposable_domains:
            raise ValidationError("Les emails temporaires ne sont pas autorisés")

        # Block suspicious email patterns
        if re.search(r'[0-9]{8,}@', email):  # Long numbers in email
            raise ValidationError("Email suspect détecté")

        return email

    def clean(self):
        """
        🛡️ SPAM PROTECTION: Time-trap validation
        Checks form submission timing to detect bots
        """
        cleaned_data = super().clean()

        # Time-trap: Check form submission speed (OPTIONAL - doesn't block if field missing)
        form_rendered_time = self.data.get('form_rendered_time')
        if form_rendered_time:  # Only validate if field exists
            try:
                rendered_timestamp = int(form_rendered_time) / 1000  # Convert ms to seconds
                current_timestamp = timezone.now().timestamp()
                elapsed = current_timestamp - rendered_timestamp

                # Too fast = bot (< 2 seconds for comments)
                if elapsed < 2:
                    raise ValidationError(
                        "Commentaire soumis trop rapidement. Veuillez prendre le temps de le lire."
                    )

                # Too slow = expired form (> 1 hour)
                if elapsed > 3600:
                    raise ValidationError(
                        "Formulaire expiré. Veuillez actualiser la page et réessayer."
                    )
            except (ValueError, TypeError):
                # If timestamp invalid, skip validation (don't block legitimate users)
                pass

        return cleaned_data


class CommentEditForm(forms.ModelForm):
    """Form for editing existing comments (within time limit)."""

    class Meta:
        model = ArticleComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition resize-none',
                'rows': '5',
                'maxlength': '2000'
            })
        }
        labels = {
            'comment': 'Modifier le commentaire',
        }

    def clean_comment(self):
        """Validate edited comment."""
        comment = self.cleaned_data.get('comment', '').strip()

        if not comment:
            raise ValidationError("Le commentaire ne peut pas être vide")

        if len(comment) < 10:
            raise ValidationError("Le commentaire doit contenir au moins 10 caractères")

        return comment


class ArticleForm(forms.ModelForm):
    """Form for creating and editing articles by authorized users."""

    class Meta:
        model = Article
        fields = [
            'title', 'slug', 'category', 'tags', 'description', 'content_markdown',
            'status', 'meta_title', 'meta_description', 'og_title', 'og_description',
            'is_featured', 'featured_order', 'is_page'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Titre de l\'article',
                'maxlength': '255'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'slug-de-article (auto-généré si vide)',
                'maxlength': '255'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none',
                'placeholder': 'Description courte pour la liste des articles',
                'rows': '6',
                'maxlength': '500',
                'style': 'height: 185px;'
            }),
            'meta_title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Titre pour les moteurs de recherche (50-60 caractères)',
                'maxlength': '255'
            }),
            'content_markdown': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm',
                'placeholder': '# Votre contenu en Markdown\n\nÉcrivez votre article ici...',
                'rows': '20'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'tags': forms.SelectMultiple(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'size': '6',
                'style': 'height: 300px;'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'meta_description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none',
                'placeholder': 'Description pour les moteurs de recherche (150-160 caractères)',
                'rows': '2',
                'maxlength': '512'
            }),
            'og_title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Titre pour les réseaux sociaux',
                'maxlength': '255'
            }),
            'og_description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none',
                'placeholder': 'Description pour les réseaux sociaux',
                'rows': '2',
                'maxlength': '512'
            }),
            'featured_order': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': '0'
            }),
        }
        labels = {
            'title': 'Titre',
            'slug': 'Slug (URL)',
            'category': 'Catégorie',
            'tags': 'Tags',
            'description': 'Description courte',
            'content_markdown': 'Contenu (Markdown)',
            'status': 'Statut',
            'meta_title': 'Meta Title (SEO)',
            'meta_description': 'Meta Description (SEO)',
            'og_title': 'Titre pour les réseaux sociaux',
            'og_description': 'Description pour les réseaux sociaux',
            'is_featured': 'Article mis en avant',
            'featured_order': 'Ordre d\'affichage',
            'is_page': 'Page technique (cachée du blog)'
        }

    def __init__(self, *args, **kwargs):
        self.user_profile = kwargs.pop('user_profile', None)
        super().__init__(*args, **kwargs)

        # Set default markdown template for new articles
        if not self.instance.pk and not self.initial.get('content_markdown'):
            self.initial['content_markdown'] = """---
meta-title:
meta-description:
og-title:
og-description:
---

[toc]

"""        # Make slug optional (will be auto-generated)
        self.fields['slug'].required = False
        self.fields['description'].required = False
        self.fields['featured_order'].required = False

        # Hide admin-only fields for non-staff users
        if self.user_profile and not self.user_profile.user.is_staff:
            # Remove admin-only fields
            self.fields.pop('is_featured', None)
            self.fields.pop('featured_order', None)
            self.fields.pop('is_page', None)

            # Non-staff can only save as draft or request publication
            self.fields['status'].choices = [
                ('draft', 'Brouillon'),
                ('review', 'En révision')
            ]
            self.fields['status'].initial = 'draft'

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise ValidationError("Le titre est obligatoire")
        if len(title) < 10:
            raise ValidationError("Le titre doit contenir au moins 10 caractères")
        return title

    def clean_content_markdown(self):
        content = self.cleaned_data.get('content_markdown', '').strip()
        if not content:
            raise ValidationError("Le contenu est obligatoire")
        if len(content) < 100:
            raise ValidationError("Le contenu doit contenir au moins 100 caractères")
        return content

    def clean_slug(self):
        slug = self.cleaned_data.get('slug', '').strip()
        # If slug is empty, it will be auto-generated in the view
        if slug:
            # Check for uniqueness
            if self.instance.pk:
                # Editing existing article
                if Article.objects.filter(slug=slug).exclude(pk=self.instance.pk).exists():
                    raise ValidationError("Ce slug est déjà utilisé")
            else:
                # Creating new article
                if Article.objects.filter(slug=slug).exists():
                    raise ValidationError("Ce slug est déjà utilisé")
        return slug


class ArticleImageForm(forms.ModelForm):
    """Form for uploading article images with metadata."""

    class Meta:
        model = ArticleImage
        fields = ['image', 'alt', 'caption', 'order']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100',
                'accept': 'image/*'
            }),
            'alt': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm',
                'placeholder': 'Texte alternatif (pour accessibilité et SEO)'
            }),
            'caption': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm',
                'placeholder': 'Légende affichée sous l\'image'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'w-20 px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm',
                'min': '1'
            })
        }
        labels = {
            'image': 'Image',
            'alt': 'Texte alternatif',
            'caption': 'Légende',
            'order': 'Ordre'
        }

    def clean_alt(self):
        alt = self.cleaned_data.get('alt', '').strip()
        if self.cleaned_data.get('image') and not alt:
            raise ValidationError("Le texte alternatif est obligatoire pour l'accessibilité")
        return alt


# Formset for managing multiple article images
ArticleImageFormSet = inlineformset_factory(
    Article,
    ArticleImage,
    form=ArticleImageForm,
    extra=1,  # Show 1 empty form by default
    max_num=10,  # Maximum 10 images per article
    can_delete=True,
    widgets={
        'DELETE': forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500'
        })
    }
)
