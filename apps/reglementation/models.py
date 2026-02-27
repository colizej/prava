from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class RuleCategory(models.Model):
    """Catégorie de réglementation (ex: Signalisation, Priorité, etc.)."""
    name = models.CharField('Nom (FR)', max_length=150)
    name_nl = models.CharField('Naam (NL)', max_length=150, blank=True)
    name_ru = models.CharField('Название (RU)', max_length=150, blank=True)

    slug = models.SlugField(unique=True)
    icon = models.CharField('Icône', max_length=50, blank=True,
                            help_text='Nom de l\'icône (ex: shield, alert-triangle)')
    description = models.TextField('Description (FR)', blank=True)
    description_nl = models.TextField('Beschrijving (NL)', blank=True)
    description_ru = models.TextField('Описание (RU)', blank=True)

    order = models.IntegerField('Ordre', default=0)
    is_active = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Catégorie règles'
        verbose_name_plural = 'Catégories règles'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('reglementation:category', kwargs={'slug': self.slug})

    def get_name(self, lang='fr'):
        if lang == 'nl' and self.name_nl:
            return self.name_nl
        if lang == 'ru' and self.name_ru:
            return self.name_ru
        return self.name


class CodeArticle(models.Model):
    """Article du code de la route."""
    article_number = models.CharField('Numéro d\'article', max_length=30,
                                      help_text='Ex: Art. 12.1.1')
    category = models.ForeignKey(
        RuleCategory, on_delete=models.CASCADE,
        related_name='articles', verbose_name='Catégorie'
    )

    title = models.CharField('Titre (FR)', max_length=250)
    title_nl = models.CharField('Titel (NL)', max_length=250, blank=True)
    title_ru = models.CharField('Заголовок (RU)', max_length=250, blank=True)

    content = models.TextField('Contenu (FR)', blank=True)
    content_nl = models.TextField('Inhoud (NL)', blank=True)
    content_ru = models.TextField('Содержание (RU)', blank=True)

    # Plain text version for search
    content_text = models.TextField('Texte brut', blank=True,
                                     help_text='Version texte pour la recherche.')

    slug = models.SlugField(unique=True, max_length=250)
    is_free = models.BooleanField('Gratuit', default=True,
                                  help_text='Visible sans abonnement premium.')
    order = models.IntegerField('Ordre', default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Article du code'
        verbose_name_plural = 'Articles du code'
        ordering = ['order', 'article_number']

    def __str__(self):
        return f'{self.article_number} — {self.title}'

    def save(self, *args, **kwargs):
        if not self.slug:
            base = f'{self.article_number}-{self.title}'
            self.slug = slugify(base)[:250]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('reglementation:article', kwargs={'slug': self.slug})

    def get_title(self, lang='fr'):
        if lang == 'nl' and self.title_nl:
            return self.title_nl
        if lang == 'ru' and self.title_ru:
            return self.title_ru
        return self.title

    def get_content(self, lang='fr'):
        if lang == 'nl' and self.content_nl:
            return self.content_nl
        if lang == 'ru' and self.content_ru:
            return self.content_ru
        return self.content


class TrafficSign(models.Model):
    """Panneau de signalisation."""
    SIGN_TYPES = [
        ('danger', 'Danger'),
        ('interdiction', 'Interdiction'),
        ('obligation', 'Obligation'),
        ('indication', 'Indication'),
        ('priorite', 'Priorité'),
        ('directionnel', 'Directionnel'),
        ('additionnel', 'Additionnel'),
    ]

    code = models.CharField('Code', max_length=20, unique=True,
                            help_text='Ex: C1, E1, F50')
    sign_type = models.CharField('Type', max_length=20, choices=SIGN_TYPES, default='indication')
    category = models.ForeignKey(
        RuleCategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='signs', verbose_name='Catégorie'
    )

    name = models.CharField('Nom (FR)', max_length=200)
    name_nl = models.CharField('Naam (NL)', max_length=200, blank=True)
    name_ru = models.CharField('Название (RU)', max_length=200, blank=True)

    description = models.TextField('Description (FR)', blank=True)
    description_nl = models.TextField('Beschrijving (NL)', blank=True)
    description_ru = models.TextField('Описание (RU)', blank=True)

    image = models.ImageField('Image', upload_to='signs/', blank=True)
    order = models.IntegerField('Ordre', default=0)

    class Meta:
        verbose_name = 'Panneau de signalisation'
        verbose_name_plural = 'Panneaux de signalisation'
        ordering = ['sign_type', 'order', 'code']

    def __str__(self):
        return f'{self.code} — {self.name}'

    def get_name(self, lang='fr'):
        if lang == 'nl' and self.name_nl:
            return self.name_nl
        if lang == 'ru' and self.name_ru:
            return self.name_ru
        return self.name


class ArticleImage(models.Model):
    """Image associée à un article (panneau, schéma, etc.)."""
    article = models.ForeignKey(
        CodeArticle, on_delete=models.CASCADE,
        related_name='images', verbose_name='Article'
    )
    image = models.ImageField('Image', upload_to='reglementation/')
    alt_text = models.CharField('Texte alternatif', max_length=200, blank=True)
    sign_code = models.CharField('Code panneau', max_length=20, blank=True,
                                 help_text='Ex: C1, D7, F17')
    order = models.IntegerField('Ordre', default=0)

    class Meta:
        verbose_name = "Image d'article"
        verbose_name_plural = "Images d'articles"
        ordering = ['order']

    def __str__(self):
        return f'{self.sign_code or self.alt_text} — {self.article.article_number}'