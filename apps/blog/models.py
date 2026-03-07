from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from apps.translatable import TranslatableFieldsMixin


class BlogCategory(TranslatableFieldsMixin, models.Model):
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



class BlogPost(TranslatableFieldsMixin, models.Model):
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
    featured_image_caption = models.CharField('Légende image', max_length=300, blank=True,
                                              help_text='Texte affiché sous l\'image (figcaption). Bon pour le SEO.')

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
    og_title = models.CharField('OG title', max_length=200, blank=True,
                                help_text='Open Graph title (Facebook/LinkedIn). Vide = meta_title.')
    og_description = models.CharField('OG description', max_length=300, blank=True,
                                      help_text='Open Graph description. Vide = meta_description.')
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

    @staticmethod
    def _parse_yaml_frontmatter(content):
        """Extract YAML front matter from Markdown content."""
        import re
        try:
            import yaml
        except ImportError:
            return {}
        m = re.match(r'^---\s*\n(.*?)\n---\s*\n?', content or '', re.DOTALL)
        if not m:
            return {}
        try:
            return yaml.safe_load(m.group(1)) or {}
        except Exception:
            return {}

    def save(self, *args, **kwargs):
        # Auto-slug from FR title
        if not self.slug:
            self.slug = slugify(self.title)
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        # Auto-calculate read time (~200 words/min)
        if self.content:
            word_count = len(self.content.split())
            self.read_time = max(1, round(word_count / 200))
        # Populate SEO fields from YAML front matter if not set manually
        fm = self._parse_yaml_frontmatter(self.content)
        if fm:
            for field in ('meta_title', 'meta_description', 'og_title', 'og_description', 'keywords', 'canonical_url'):
                if not getattr(self, field) and fm.get(field):
                    setattr(self, field, str(fm[field])[:self._meta.get_field(field).max_length or 999])
            if 'no_index' in fm and not self.no_index:
                self.no_index = bool(fm['no_index'])
        _original = self.__class__.objects.filter(pk=self.pk).values_list('featured_image', flat=True).first() if self.pk else None
        super().save(*args, **kwargs)

        # Convert newly uploaded image to WebP
        if self.featured_image and self.featured_image.name and self.featured_image.name != _original:
            from apps.main.image_utils import convert_field_to_webp
            if convert_field_to_webp(self.featured_image):
                self.__class__.objects.filter(pk=self.pk).update(featured_image=self.featured_image.name)

    def get_absolute_url(self):
        return reverse('blog:detail', kwargs={'slug': self.slug})

    @property
    def seo_title(self):
        return self.meta_title or self.title

    @property
    def seo_description(self):
        return self.meta_description or self.excerpt or self.content[:160]

    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])

    def article_structured_data(self, request):
        """Return Article JSON-LD string (generated in Python for guaranteed valid JSON)."""
        import json as _json
        author_name = (self.author.get_full_name() or self.author.username)
        data = {
            '@context': 'https://schema.org',
            '@type': 'Article',
            'headline': self.seo_title,
            'author': {
                '@type': 'Person',
                'name': author_name,
                'url': request.build_absolute_uri('/'),
            },
            'datePublished': self.published_at.isoformat() if self.published_at else None,
            'dateModified': self.updated_at.isoformat() if self.updated_at else None,
            'description': self.seo_description,
            'mainEntityOfPage': {
                '@type': 'WebPage',
                '@id': request.build_absolute_uri(),
            },
            'wordCount': len(self.content) if self.content else 0,
        }
        if self.featured_image and self.featured_image.name:
            data['image'] = request.build_absolute_uri(self.featured_image.url)
        if self.keywords:
            data['keywords'] = self.keywords
        return _json.dumps(data, ensure_ascii=False)

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
