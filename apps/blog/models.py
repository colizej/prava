from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class BlogCategory(models.Model):
    """Catégorie de blog."""
    name = models.CharField('Nom (FR)', max_length=100)
    name_nl = models.CharField('Naam (NL)', max_length=100, blank=True)
    name_ru = models.CharField('Название (RU)', max_length=100, blank=True)

    slug = models.SlugField(unique=True)
    description = models.TextField('Description', blank=True)
    order = models.IntegerField('Ordre', default=0)

    class Meta:
        verbose_name = 'Catégorie blog'
        verbose_name_plural = 'Catégories blog'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('blog:category', kwargs={'slug': self.slug})

    def get_name(self, lang='fr'):
        if lang == 'nl' and self.name_nl:
            return self.name_nl
        if lang == 'ru' and self.name_ru:
            return self.name_ru
        return self.name


class BlogPost(models.Model):
    """Article de blog avec SEO complet."""
    # Content FR (principal)
    title = models.CharField('Titre (FR)', max_length=200)
    content = models.TextField('Contenu (FR)')
    excerpt = models.CharField('Extrait (FR)', max_length=300, blank=True)

    # Content NL
    title_nl = models.CharField('Titel (NL)', max_length=200, blank=True)
    content_nl = models.TextField('Inhoud (NL)', blank=True)
    excerpt_nl = models.CharField('Uittreksel (NL)', max_length=300, blank=True)

    # Content RU
    title_ru = models.CharField('Заголовок (RU)', max_length=200, blank=True)
    content_ru = models.TextField('Содержание (RU)', blank=True)
    excerpt_ru = models.CharField('Отрывок (RU)', max_length=300, blank=True)

    # Relations
    slug = models.SlugField(unique=True, max_length=250)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    category = models.ForeignKey(
        BlogCategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='posts'
    )

    # Media
    featured_image = models.ImageField('Image principale', upload_to='blog/', blank=True)
    featured_image_alt = models.CharField('Alt image', max_length=200, blank=True)

    # Publishing
    is_published = models.BooleanField('Publié', default=False)
    published_at = models.DateTimeField('Date de publication', blank=True, null=True)

    # Stats
    views_count = models.IntegerField('Vues', default=0)
    read_time = models.IntegerField('Temps de lecture (min)', default=5)

    # SEO
    meta_title = models.CharField('Meta title', max_length=70, blank=True,
                                  help_text='Max 70 caractères. Vide = titre de l\'article.')
    meta_description = models.CharField('Meta description', max_length=160, blank=True,
                                        help_text='Max 160 caractères. Vide = extrait.')
    keywords = models.CharField('Mots-clés', max_length=300, blank=True,
                                help_text='Séparés par des virgules.')
    canonical_url = models.URLField('URL canonique', blank=True,
                                    help_text='Laisser vide pour utiliser l\'URL par défaut.')
    no_index = models.BooleanField('No index', default=False,
                                   help_text='Empêcher l\'indexation par les moteurs de recherche.')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'
        ordering = ['-published_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        # Auto-calculate read time (~200 words/min)
        if self.content:
            word_count = len(self.content.split())
            self.read_time = max(1, round(word_count / 200))
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:detail', kwargs={'slug': self.slug})

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

    def get_excerpt(self, lang='fr'):
        if lang == 'nl' and self.excerpt_nl:
            return self.excerpt_nl
        if lang == 'ru' and self.excerpt_ru:
            return self.excerpt_ru
        return self.excerpt or self.content[:200]

    @property
    def seo_title(self):
        return self.meta_title or self.title

    @property
    def seo_description(self):
        return self.meta_description or self.excerpt or self.content[:160]

    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])

    @property
    def faq_structured_data(self):
        """Return FAQ JSON-LD string if content contains Q/R FAQ blocks.

        Format in Markdown:
            #### Q : Question text
            R : Answer text (can span multiple lines)
            #
        """
        import json as _json
        import re as _re
        try:
            import markdown as _md
            from django.utils.html import strip_tags
        except ImportError:
            return ''

        text = self.content or ''
        items = []
        m = _re.search(r'(####\s*Q\s*:.*?)(?:\n\s*#\s*\n|\n\s*#\s*$)', text, flags=_re.S | _re.I)
        if not m:
            m = _re.search(r'####\s*Q\s*:\s*(.*)$', text, flags=_re.S | _re.I)
        if not m:
            return ''

        block = m.group(0)
        cur_q, cur_a = None, []
        for ln in block.splitlines():
            qm = _re.match(r'^\s*####\s*Q\s*:\s*(.*)$', ln)
            if qm:
                if cur_q:
                    a_text = strip_tags(_md.markdown('\n'.join(cur_a).strip()))
                    items.append({'@type': 'Question', 'name': cur_q,
                                  'acceptedAnswer': {'@type': 'Answer', 'text': a_text}})
                cur_q = qm.group(1).strip()
                cur_a = []
                continue
            rm = _re.match(r'^\s*R\s*:\s*(.*)$', ln)
            if rm:
                cur_a.append(rm.group(1))
                continue
            if _re.match(r'^\s*#\s*$', ln):
                break
            if cur_q:
                cur_a.append(ln)
        if cur_q:
            a_text = strip_tags(_md.markdown('\n'.join(cur_a).strip()))
            items.append({'@type': 'Question', 'name': cur_q,
                          'acceptedAnswer': {'@type': 'Answer', 'text': a_text}})
        if not items:
            return ''
        return _json.dumps(
            {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': items},
            ensure_ascii=False,
        )
