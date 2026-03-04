from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.urls import reverse
from django.utils import timezone
import re
from html import escape as html_escape
import json
from django.utils.html import strip_tags
import io
import os
from django.core.files.base import ContentFile
from utils.yaml_utils import parse_article_yaml, extract_seo_fields

try:
    import markdown as md
except Exception:
    md = None
try:
    from PIL import Image
except Exception:
    Image = None


def replace_video_markers(md_text: str) -> str:
    """Replace video markers in Markdown with safe, responsive iframe HTML.

    Supported syntaxes:
      [video:youtube:VIDEO_ID]
      [video:youtube:VIDEO_ID width=800]
      [video:youtube:VIDEO_ID width=80%]
      [video:vimeo:12345678]
      [video:vimeo:12345678 width=640px]

    By default the video wrapper uses `max-width:100%` and is centered (`margin:0 auto`).
    If `width` is provided it is applied as the `max-width` of the wrapper. Numeric
    values without units are treated as pixels.
    """
    if not md_text:
        return md_text

    def _normalize_width(raw: str) -> str:
        if not raw:
            return '100%'
        raw = raw.strip()
        if raw.isdigit():
            return f'{raw}px'
        return raw

    def _yt_repl(m):
        vid = m.group(1)
        raw_w = m.group(2)
        w = _normalize_width(raw_w)
        wrapper_style = (
            f'position:relative;padding-bottom:56.25%;height:0;overflow:hidden;margin:0 auto;max-width:{w};'
        )
        iframe = (
            f'<div style="{wrapper_style}">'
            f'<iframe src="https://www.youtube-nocookie.com/embed/{vid}"'
            ' frameborder="0" '
            ' allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
            ' allowfullscreen loading="lazy" referrerpolicy="strict-origin-when-cross-origin" '
            ' style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"'
            '></iframe></div>'
        )
        return iframe

    def _vimeo_repl(m):
        vid = m.group(1)
        raw_w = m.group(2)
        w = _normalize_width(raw_w)
        wrapper_style = (
            f'position:relative;padding-bottom:56.25%;height:0;overflow:hidden;margin:0 auto;max-width:{w};'
        )
        iframe = (
            f'<div style="{wrapper_style}">'
            f'<iframe src="https://player.vimeo.com/video/{vid}"'
            ' frameborder="0" '
            ' allow="autoplay; fullscreen; picture-in-picture" '
            ' allowfullscreen loading="lazy" referrerpolicy="strict-origin-when-cross-origin" '
            ' style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"'
            '></iframe></div>'
        )
        return iframe

    # patterns: optional width parameter (digits or with px/% unit)
    md_text = re.sub(r"\[video:youtube:([A-Za-z0-9_-]{11})(?:\s+width=([0-9]+(?:px|%)?))?\]", _yt_repl, md_text)
    md_text = re.sub(r"\[video:vimeo:(\d+)(?:\s+width=([0-9]+(?:px|%)?))?\]", _vimeo_repl, md_text)

    return md_text


class Article(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("review", "Review"),
        ("published", "Published"),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.CharField(max_length=512, blank=True, help_text="Recommended 50-160 characters for search snippets")
    description = models.TextField(blank=True)
    content_markdown = models.TextField(blank=True)
    content_html = models.TextField(blank=True, editable=False)
    profile_author = models.ForeignKey('profiles.Profile', on_delete=models.SET_NULL, null=True, blank=True, related_name="articles", verbose_name="Author", help_text="Article author (leave empty for technical pages)")
    published_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    canonical_url = models.URLField(blank=True)
    og_title = models.CharField(max_length=255, blank=True)
    og_description = models.CharField(max_length=512, blank=True)
    reading_time = models.PositiveIntegerField(default=0, help_text="Estimated reading time in minutes")

    # Technical page flag (for help pages, legal docs, etc. - not shown in blog list)
    is_page = models.BooleanField(
        default=False,
        verbose_name="Technical page",
        help_text="Check if this is a technical page (won't appear in blog listing)"
    )

    # Featured/pinned articles
    is_featured = models.BooleanField(
        default=False,
        verbose_name="Featured article",
        help_text="Featured articles appear at the top of listings with special styling"
    )
    featured_order = models.IntegerField(
        default=0,
        verbose_name="Featured order",
        help_text="Order for featured articles (lower numbers appear first, 0 = not featured)"
    )

    # Series
    series = models.ForeignKey(
        'ArticleSeries',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='articles',
        verbose_name="Article series",
        help_text="Part of a series (e.g., tutorial series)"
    )
    series_order = models.IntegerField(
        default=0,
        verbose_name="Order in series",
        help_text="Position in the series (1 = first, 2 = second, etc.)"
    )

    # taxonomy fields (nullable/optional)
    category = models.ForeignKey('Category', null=True, blank=True, on_delete=models.SET_NULL, related_name="articles")
    tags = models.ManyToManyField('Tag', blank=True, related_name="articles")

    # Related content recommendations
    recommended_products = models.ManyToManyField(
        'profiles.Play',
        blank=True,
        related_name='recommended_in_articles',
        help_text="Produits recommandés pour cet article (max 4-6)"
    )

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        try:
            return reverse('blog:article_detail', args=[self.slug])
        except Exception:
            return f"/blog/{self.slug}/"

    def save(self, *args, **kwargs):
        # Parse YAML frontmatter using yaml_utils
        if self.content_markdown:
            text_wo_yaml = self.content_markdown

            # Try to parse YAML frontmatter
            try:
                yaml_data, text_wo_yaml, seo_fields = parse_article_yaml(self.content_markdown)

                # Basic fields from YAML
                if not self.title and 'title' in yaml_data:
                    self.title = yaml_data['title']
                if not self.slug and 'slug' in yaml_data:
                    self.slug = yaml_data['slug']

                # Author field (if present in YAML)
                if 'author' in yaml_data and not self.profile_author:
                    # Note: author is stored as string in YAML, would need to map to Profile
                    pass

                # Status and publishing
                if 'status' in yaml_data:
                    self.status = yaml_data.get('status', 'draft')
                if 'published_at' in yaml_data:
                    # Parse published_at if it's a string
                    pass  # Keep existing logic for published_at

                # SEO Fields - populate from YAML (with proper cleaning)
                if 'meta_title' in seo_fields:
                    self.meta_title = seo_fields['meta_title']
                if 'meta_description' in seo_fields:
                    self.meta_description = seo_fields['meta_description']

                # Auto-fill og_ fields from meta_ fields if NOT in YAML
                # This ensures Open Graph tags always populated for social sharing
                # Only use YAML og_ values if explicitly provided in YAML
                if 'og_title' in seo_fields:
                    self.og_title = seo_fields['og_title']
                elif 'meta_title' in seo_fields:
                    # If no og_title in YAML, copy from meta_title
                    self.og_title = seo_fields['meta_title']

                if 'og_description' in seo_fields:
                    self.og_description = seo_fields['og_description']
                elif 'meta_description' in seo_fields:
                    # If no og_description in YAML, copy from meta_description
                    self.og_description = seo_fields['meta_description']

                # Auto-fill description from og_description if description is empty
                if not self.description and 'og_description' in seo_fields:
                    self.description = seo_fields['og_description']

            except ValueError:
                # No YAML or invalid format - continue with existing logic
                pass

            # Ensure YAML frontmatter is removed from text_wo_yaml even if parsing failed
            # This is critical to prevent YAML from appearing in the rendered HTML
            if text_wo_yaml.startswith('---'):
                # Remove YAML block manually as fallback
                parts = text_wo_yaml.split('---', 2)
                if len(parts) >= 3:
                    text_wo_yaml = parts[2].strip()

            # Extract first h1 and set as title (only if title is empty)
            h1_match = re.search(r'^#\s*(.+)$', text_wo_yaml, re.MULTILINE)
            if h1_match and not self.title:
                h1_text = h1_match.group(1).strip()
                self.title = h1_text

            # Always remove first h1 from markdown (to avoid duplication with template's <h1>)
            if h1_match:
                text_wo_yaml = re.sub(r'^#\s*.+\n?', '', text_wo_yaml, count=1, flags=re.MULTILINE)

        # Auto-generate slug if missing
        if not self.slug:
            base = slugify(self.title)[:200]
            slug = base
            i = 1
            while Article.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug

        # Render markdown to html if markdown lib available
        quote_attributions = []  # Initialize before processing
        if md and self.content_markdown:
            placeholder = "<!--TOC_PLACEHOLDER-->"
            # Use text_wo_yaml and without first h1
            text = text_wo_yaml
            text = re.sub(r'\[(?:contents|toc)\]', placeholder, text, flags=re.I)

            # Hide FAQ blocks from displayed content (don't delete - keep in source)
            # FAQ blocks start with '### FAQ' or '### Foire aux Questions' and end with standalone '#' OR end of file
            # Replace with placeholder that markdown won't process, but keep a marker for banner positioning
            faq_blocks_removed = []
            def hide_faq_block(match):
                faq_content = match.group(0)
                faq_blocks_removed.append(faq_content)
                # Return HTML comment with FAQ_SECTION_MARKER for banner positioning
                # This marker can be used by banner system to insert ads before FAQ
                return f'\n<!-- FAQ_SECTION_MARKER -->\n<!-- FAQ_HIDDEN_{len(faq_blocks_removed)-1} -->\n'

            # Find and hide entire FAQ section BEFORE markdown conversion
            # Pattern: ### FAQ, Foire aux Questions, Les questions fréquentes, etc. -> all content -> ending with # OR EOF
            text = re.sub(
                r'(###\s*(?:FAQ|Foire aux [Qq]uestions|Les questions [Ff]réquentes|Questions [Ff]réquentes).*?)(?:\n\s*#\s*(?:\n|$)|$)',
                hide_faq_block,
                text,
                flags=re.DOTALL | re.IGNORECASE
            )

            # Process quote attribution (>> Author, description)
            # Find blockquotes with attribution: > quote\n>> attribution
            # Replace entire pattern with HTML before markdown processing
            quote_blocks = []
            def process_quote_with_attribution(match):
                quote_text = match.group(1).strip()
                attribution_text = match.group(2).strip()

                # Format attribution: text before comma in red, rest in gray
                if ',' in attribution_text:
                    parts = attribution_text.split(',', 1)
                    author = parts[0].strip()
                    description = parts[1].strip()
                    formatted_attribution = f'<span class="quote__author">{author}</span>, <span class="quote__description">{description}</span>'
                else:
                    formatted_attribution = f'<span class="quote__author">{attribution_text}</span>'

                # Store complete blockquote HTML
                quote_html = f'<blockquote class="quote"><p class="quote__content">{quote_text}</p><footer class="quote__attribution">{formatted_attribution}</footer></blockquote>'
                quote_blocks.append(quote_html)
                # Return placeholder WITHOUT > so markdown won't process it
                return f'\n{{{{QUOTE_BLOCK_{len(quote_blocks)-1}}}}}\n'

            # Match: > quote followed by >> attribution on next line
            text = re.sub(
                r'^>\s*(.+?)\s*\n>>\s*(.+?)$',
                process_quote_with_attribution,
                text,
                flags=re.MULTILINE
            )

            # Replace video markers in markdown (e.g. [video:youtube:ID width=80%])
            text = replace_video_markers(text)

            try:
                # first pass: markdown -> html (we don't use the 'toc' extension here; we'll build TOC ourselves)
                md_inst = md.Markdown(extensions=['fenced_code', 'nl2br', 'tables', 'sane_lists', 'codehilite'] if 'codehilite' in md.__dict__ else ['fenced_code', 'nl2br', 'tables', 'sane_lists'])
                html = md_inst.convert(text)
            except Exception:
                # fallback to simple conversion
                html = md.markdown(self.content_markdown, extensions=["fenced_code", "nl2br", "tables", "sane_lists"])

            # Now find h2 elements, ensure they have unique ids, add small anchor link and collect TOC items
            toc_items = []
            counts = {}

            def h2_repl(match):
                attrs = match.group(1) or ''
                inner = match.group(2) or ''

                # If id already present in attrs, reuse it; otherwise generate one
                id_attr_match = re.search(r'\sid=(["\'])(.*?)\1', attrs)
                if id_attr_match:
                    idval = id_attr_match.group(2)
                else:
                    # Get plain text from inner HTML to slugify
                    plain = re.sub(r'<[^>]+>', '', inner).strip()
                    base = slugify(plain)[:200] or 'section'
                    cnt = counts.get(base, 0)
                    counts[base] = cnt + 1
                    idval = base if cnt == 0 else f"{base}-{cnt+1}"
                    # Insert id into attrs (preserve other attributes if any)
                    attrs_str = (' ' + attrs.strip()) if attrs.strip() else ''
                    attrs = f' id="{idval}"' + attrs_str

                # Avoid adding duplicate anchor if anchor already exists in inner
                if 'class="header-anchor"' in inner or "class='header-anchor'" in inner:
                    new_inner = inner
                else:
                    # Small anchor symbol — can be styled via CSS .header-anchor
                    anchor_html = f'<a class="header-anchor" href="#{idval}" aria-hidden="true">¶</a>'
                    # Append anchor after heading content
                    new_inner = inner + anchor_html

                # Title text for TOC (strip tags)
                title_text = re.sub(r'<[^>]+>', '', inner).strip() or 'Section'
                toc_items.append((idval, title_text))
                return f'<h2{attrs}>{new_inner}</h2>'

            # Apply replacement across the HTML
            html = re.sub(r'<h2([^>]*)>(.*?)</h2>', h2_repl, html, flags=re.S | re.I)

            # Build TOC HTML (only h2 depth) - SIDEBAR style
            if toc_items:
                toc_parts = [
                    '<nav class="table-of-contents sidebar">',
                    '<h3 class="toc-title">Table des matières</h3>',
                    '<ul>'
                ]
                for idval, title in toc_items:
                    safe_title = html_escape(title)
                    toc_parts.append(f'<li><a href="#{idval}">{safe_title}</a></li>')
                toc_parts.append('</ul></nav>')

                toc_html = ''.join(toc_parts)
            else:
                toc_html = ''

            # Replace placeholder (prefer replacing <p>placeholder</p> to avoid an extra paragraph)
            html = re.sub(r'<p>\s*' + re.escape(placeholder) + r'\s*</p>', toc_html, html, flags=re.I)
            # fallback
            html = html.replace(placeholder, toc_html)
        else:
            html = self.content_markdown or ''

        # replace [imageN:...]/[imageN] placeholders with actual img tags
        html = self._replace_image_placeholders(html)

        # обработка импортных путей вида ![](/images/ID/size/W/H)
        def fix_imported_image_paths(text):
            # Markdown ![](/images/ID/size/W/H)
            text = re.sub(r'!\[\]\((/images/\d+/size/\d+/\d+)\)', r'<img src="/media\1/image.webp" loading="lazy"/>', text)
            # HTML <img src="/images/ID/size/W/H">
            text = re.sub(r'<img([^>]+)src=["\	\'](/images/\d+/size/\d+/\d+)["\	\']', r'<img\1src="/media\2/image.webp"', text)
            return text
        html = fix_imported_image_paths(html)

        # replace YouTube links/shortcodes with responsive iframe embeds
        html = self._replace_youtube_embeds(html)
        # Ensure external absolute links open in a new tab and have safe rel attributes
        html = self._ensure_external_links_open_new_tab(html)

        # Wrap tables in responsive container for mobile
        html = self._wrap_tables_responsive(html)

        # Post-process quote blocks: replace placeholders with formatted HTML
        for idx, quote_html in enumerate(quote_blocks):
            placeholder = f'{{{{QUOTE_BLOCK_{idx}}}}}'
            # Markdown might wrap placeholder in <p> tags
            html = re.sub(rf'<p>\s*{re.escape(placeholder)}\s*</p>', quote_html, html)
            html = html.replace(placeholder, quote_html)

        self.content_html = html

        # estimate reading time (~200 words/min)
        words = re.findall(r"\w+", self.content_markdown or "")
        self.reading_time = max(1, int(len(words) / 200))

        # Clean quotes from SEO fields (legacy fix for articles created before YAML parsing)
        # Remove all quotes from SEO meta tags (not needed for web/SEO)
        def strip_quotes(text):
            """Remove all double and single quotes from text"""
            if not text:
                return text

            # Remove all double quotes (straight and curly)
            text = text.replace('"', '').replace('"', '').replace('"', '')
            # Remove all single quotes (straight and curly)
            text = text.replace("'", '').replace(''', '').replace(''', '')

            # Clean up any double spaces that may result
            while '  ' in text:
                text = text.replace('  ', ' ')

            return text.strip()
        self.meta_title = strip_quotes(self.meta_title)
        self.meta_description = strip_quotes(self.meta_description)
        self.og_title = strip_quotes(self.og_title)
        self.og_description = strip_quotes(self.og_description)

        # auto-fill meta_description ONLY if not already set from YAML
        # Priority: YAML meta_description > description field > auto-generated from markdown
        if not self.meta_description:
            if self.description:
                source = self.description
            else:
                source = self.content_markdown or ""

            if source:
                # Strip HTML tags first
                s = strip_tags(source).strip()
                # Remove markdown syntax (headers, bold, italic, links, etc)
                s = re.sub(r'#{1,6}\s+', '', s)  # headers
                s = re.sub(r'\*\*([^*]+)\*\*', r'\1', s)  # bold
                s = re.sub(r'\*([^*]+)\*', r'\1', s)  # italic
                s = re.sub(r'\[([^]]+)\]\([^)]+\)', r'\1', s)  # links
                s = re.sub(r'`([^`]+)`', r'\1', s)  # code
                s = re.sub(r'\s+', ' ', s).strip()  # normalize whitespace

                # Truncate to ~155 chars without cutting words
                if len(s) > 155:
                    cut = s[:155]
                    last_space = cut.rfind(" ")
                    if last_space > 80:
                        cut = cut[:last_space]
                    s = cut.rstrip() + '...'

                self.meta_description = s

        # set published_at when status becomes published and not set
        if self.status == "published" and not self.published_at:
            self.published_at = timezone.now()

        # Auto-generate canonical URL if not set (for SEO and duplicate content prevention)
        if not self.canonical_url and self.slug:
            from django.conf import settings
            site_url = getattr(settings, 'SITE_URL', 'https://piecedetheatre.be')
            # Remove trailing slash from site_url if present
            site_url = site_url.rstrip('/')
            # Get relative URL and combine with site URL
            relative_url = self.get_absolute_url()
            self.canonical_url = f"{site_url}{relative_url}"

        super().save(*args, **kwargs)

    def _replace_image_placeholders(self, html_text: str) -> str:
        # pattern: [image1] or [image1:alt="...",caption="..."]
        pattern = re.compile(r"\[image(\d+)(:([^\]]+))?\]")

        def repl(match):
            idx = int(match.group(1))
            opts = match.group(3)
            alt = ""
            caption = ""
            if opts:
                # simple parse key="value",key2="value2"
                for part in re.split(r",\s*", opts):
                    if "=" in part:
                        k, v = part.split("=", 1)
                        v = v.strip().strip('"\'')
                        if k.strip() == "alt":
                            alt = v
                        if k.strip() == "caption":
                            caption = v

            try:
                img = self.images.filter(order=idx).first()
                if not img:
                    return ""
                # Проверяем есть ли файл изображения
                if not img.image:
                    return ""
                url = img.image.url
            except Exception:
                return ""

            alt_text = alt or img.alt or self.title
            fig = f'<figure class="article-image"><img src="{url}" alt="{html_escape(alt_text)}" loading="lazy"/>'
            if caption or img.caption:
                fig += f'<figcaption>{html_escape(caption or img.caption)}</figcaption>'
            fig += '</figure>'
            return fig

        return pattern.sub(repl, html_text)

    def _replace_youtube_embeds(self, html_text: str) -> str:
        """Replace plain YouTube URLs or simple shortcodes with a responsive iframe embed.

        Supported inputs inside rendered HTML:
        - Plain URL on its own paragraph: <p>https://www.youtube.com/watch?v=ID</p>
        - Short link: <p>https://youtu.be/ID</p>
        - Existing anchor: <a href="https://youtu.be/ID">...</a>
        - Shortcode form (in markdown before render): [youtube:ID] or [youtube:https://youtu.be/ID]

        Output: responsive `<iframe>` using `youtube-nocookie.com/embed/ID` with
        `allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"`
        and `referrerpolicy="strict-origin-when-cross-origin"`.
        """
        def make_iframe(video_id: str) -> str:
            src = f"https://www.youtube-nocookie.com/embed/{video_id}"
            iframe = (
                '<div class="video-wrapper mb-6">'
                '<div class="relative pb-[56.25%] h-0">'
                f'<iframe class="absolute inset-0 w-full h-full rounded-lg" src="{src}" '
                'frameborder="0" '
                'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
                'allowfullscreen '
                'referrerpolicy="strict-origin-when-cross-origin">'
                '</iframe>'
                '</div>'
                '</div>'
            )
            return iframe

        # pattern to find youtube id in various URL forms
        # handles youtube.com/watch?v=ID, youtu.be/ID, embed URLs
        url_patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=([A-Za-z0-9_-]{11})',
            r'https?://(?:www\.)?youtube\.com/embed/([A-Za-z0-9_-]{11})',
            r'https?://youtu\.be/([A-Za-z0-9_-]{11})',
        ]

        # Replace only paragraphs that contain *only* a YouTube/Vimeo URL or a single
        # anchor pointing to such a URL. This avoids replacing inline links or
        # paragraphs with surrounding text (which would otherwise remove content).
        def repl_p(m):
            inner = (m.group(1) or '').strip()

            # If paragraph is exactly a raw URL, e.g. <p>https://youtu.be/ID</p>
            for pat in url_patterns:
                if re.fullmatch(pat, inner, flags=re.I):
                    vid = re.search(pat, inner, flags=re.I).group(1)
                    return make_iframe(vid)

            # If paragraph is exactly a single anchor: <p><a href="...">text</a></p>
            a_match = re.fullmatch(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>.*?</a>', inner, flags=re.I | re.S)
            if a_match:
                href = a_match.group(1)
                for pat in url_patterns:
                    mm = re.search(pat, href, flags=re.I)
                    if mm:
                        vid = mm.group(1)
                        return make_iframe(vid)

            # otherwise, leave paragraph unchanged (do not strip or remove inline links)
            return m.group(0)

        html_text = re.sub(r'<p>\s*(.*?)\s*</p>', repl_p, html_text, flags=re.I | re.S)

        # Support simple shortcode that might remain after markdown: [youtube:ID]
        html_text = re.sub(r'\[youtube\s*:\s*(?:https?://[^\s\]]+/)?([A-Za-z0-9_-]{11})\s*\]', lambda m: make_iframe(m.group(1)), html_text, flags=re.I)

        return html_text

    def _ensure_external_links_open_new_tab(self, html_text: str) -> str:
        """Add target="_blank" and rel="noopener noreferrer" to absolute http(s) links.

        Rules:
        - Only affects links with href starting with http:// or https:// (mailto: and tel: untouched).
        - If `target` already present, it is preserved.
        - If `rel` already present, it is preserved.
        """
        if not html_text:
            return html_text

        def repl(match):
            attrs = match.group(1) or ''
            href_m = re.search(r'href=(?:"|\')([^"\']+)(?:"|\')', attrs)
            if not href_m:
                return match.group(0)
            href = href_m.group(1).strip()
            # only process absolute http(s) URLs
            if not re.match(r'^https?://', href, flags=re.I):
                return match.group(0)

            # if target already present, leave it
            if re.search(r'\btarget\s*=\s*', attrs, flags=re.I):
                return match.group(0)

            # build new attributes string: append target and rel if rel not present
            new_attrs = attrs
            # add target
            new_attrs = new_attrs + ' target="_blank"'
            # if rel absent, add safe rel
            if not re.search(r'\brel\s*=\s*', attrs, flags=re.I):
                new_attrs = new_attrs + ' rel="noopener noreferrer"'

            return f'<a{new_attrs}>'

        # replace opening <a ...> tags (do not touch closing tags or inner content)
        html_text = re.sub(r'<a([^>]*)>', repl, html_text, flags=re.I | re.S)
        return html_text

    def _wrap_tables_responsive(self, html_text: str) -> str:
        """Wrap all <table> elements in a responsive container for mobile scrolling.

        This prevents tables from breaking the page layout on mobile devices
        by adding horizontal scroll when needed.
        """
        if not html_text:
            return html_text

        # Wrap each <table>...</table> in <div class="table-responsive">...</div>
        # Use re.DOTALL to match across newlines
        html_text = re.sub(
            r'(<table[^>]*>.*?</table>)',
            r'<div class="table-responsive overflow-x-auto">\1</div>',
            html_text,
            flags=re.DOTALL | re.IGNORECASE
        )

        return html_text

    @property
    def get_cover_url(self):
        """
        Возвращает url обложки: сначала cover, если оно есть,
        иначе первую картинку из content_html.
        """
        if self.cover_image and self.cover_image.image:
            try:
                return self.cover_image.image.url
            except Exception:
                pass
        # Поиск первой картинки в content_html
        match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', self.content_html or '')
        if match:
            return match.group(1)
        return None

    @property
    def cover_image(self):
        return self.images.order_by("order").first()

    def get_related_articles(self, count=3):
        """Get related articles based on category and tags.

        Priority algorithm:
        1. Same category + common tags (most relevant)
        2. Same category (if not enough from #1)
        3. Common tags (if still not enough)
        4. Recent popular articles (fallback)

        Returns: List of Article objects (published, not is_page, excluding self)
        """
        if not self.pk:
            return []

        related_ids = []
        related_articles = []

        # 1. Same category + common tags
        if self.category and self.tags.exists():
            same_cat_tags = Article.objects.filter(
                status='published',
                is_page=False,
                category=self.category,
                tags__in=self.tags.all()
            ).exclude(id=self.id).distinct().order_by('-published_at')

            for article in same_cat_tags:
                if article.id not in related_ids:
                    related_articles.append(article)
                    related_ids.append(article.id)
                    if len(related_articles) >= count:
                        return related_articles

        # 2. Fill up with same category articles
        if len(related_articles) < count and self.category:
            same_cat = Article.objects.filter(
                status='published',
                is_page=False,
                category=self.category
            ).exclude(id=self.id).exclude(id__in=related_ids).order_by('-published_at')

            for article in same_cat:
                if article.id not in related_ids:
                    related_articles.append(article)
                    related_ids.append(article.id)
                    if len(related_articles) >= count:
                        return related_articles

        # 3. Fill up with articles sharing tags
        if len(related_articles) < count and self.tags.exists():
            same_tags = Article.objects.filter(
                status='published',
                is_page=False,
                tags__in=self.tags.all()
            ).exclude(id=self.id).exclude(id__in=related_ids).distinct().order_by('-published_at')

            for article in same_tags:
                if article.id not in related_ids:
                    related_articles.append(article)
                    related_ids.append(article.id)
                    if len(related_articles) >= count:
                        return related_articles

        # 4. Fallback to recent popular articles
        if len(related_articles) < count:
            popular = Article.objects.filter(
                status='published',
                is_page=False
            ).exclude(id=self.id).exclude(id__in=related_ids).order_by('-views', '-published_at')

            for article in popular:
                if article.id not in related_ids:
                    related_articles.append(article)
                    related_ids.append(article.id)
                    if len(related_articles) >= count:
                        return related_articles

        return related_articles

    def get_prev_in_series(self):
        """Get previous article in the series."""
        if not self.series:
            return None
        return Article.objects.filter(
            series=self.series,
            series_order__lt=self.series_order,
            status='published',
            is_page=False
        ).order_by('-series_order').first()

    def get_next_in_series(self):
        """Get next article in the series."""
        if not self.series:
            return None
        return Article.objects.filter(
            series=self.series,
            series_order__gt=self.series_order,
            status='published',
            is_page=False
        ).order_by('series_order').first()

    @property
    def faq_structured_data(self):
        """Return FAQ JSON-LD.

        Only the precise Q/R in-block format is supported now.

        Format (inside a block):
        - Questions start with: '#### Q : <question text>'
        - Answers start with: 'R : <answer first line>' and may continue on following lines
        - The FAQ block is terminated by a lone line containing '#'

        The parser does NOT use admin-managed FAQs anymore.
        """
        items = []

        # look for the Q/R blocks inside content_markdown first
        md_text = (self.content_markdown or '')
        block = None
        if md_text:
            # Find the first occurrence of a line starting with '#### Q :' and capture until a line with a single '#'.
            m = re.search(r"(####\s*Q\s*:.*?)(?:\n\s*#\s*\n|\n\s*#\s*$)", md_text, flags=re.S | re.I)
            if not m:
                # alternative: capture from first '#### Q :' to EOF
                m = re.search(r"####\s*Q\s*:\s*(.*)$", md_text, flags=re.S | re.I)
            if m:
                block = m.group(0)

        # as a last resort, try content_html (in case editor saved HTML without markdown)
        if not block and getattr(self, 'content_html', None):
            html_text = self.content_html
            m = re.search(r"####\s*Q\s*:.*?(?:\n\s*#\s*\n|\n\s*#\s*$)", html_text, flags=re.S | re.I)
            if m:
                block = m.group(0)

        if not block:
            return ''

        # Parse the block lines for Q/R markers
        lines = block.splitlines()
        cur_q = None
        cur_a_lines = []
        for ln in lines:
            qm = re.match(r'^\s*####\s*Q\s*:\s*(.*)$', ln)
            if qm:
                # flush previous
                if cur_q is not None:
                    a_md = '\n'.join(cur_a_lines).strip()
                    if md:
                        a_html = md.markdown(a_md)
                        a_text = strip_tags(a_html)
                    else:
                        a_text = a_md
                    items.append({"@type": "Question", "name": cur_q, "acceptedAnswer": {"@type": "Answer", "text": a_text}})
                cur_q = qm.group(1).strip()
                cur_a_lines = []
                continue

            rm = re.match(r'^\s*R\s*:\s*(.*)$', ln)
            if rm:
                cur_a_lines.append(rm.group(1))
                continue

            # end marker
            if re.match(r'^\s*#\s*$', ln):
                break

            # continuation lines
            if cur_q is not None:
                cur_a_lines.append(ln)

        # flush last
        if cur_q is not None:
            a_md = '\n'.join(cur_a_lines).strip()
            if md:
                a_html = md.markdown(a_md)
                a_text = strip_tags(a_html)
            else:
                a_text = a_md
            items.append({"@type": "Question", "name": cur_q, "acceptedAnswer": {"@type": "Answer", "text": a_text}})

        if not items:
            return ''

        payload = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": items}
        return json.dumps(payload, ensure_ascii=False)

    def get_faq_items(self):
        """Parse FAQ from Markdown content for the unified FAQ template.

        Format:
        - Section starts with: ### FAQ or ### Foire aux Questions
        - Questions: #### Q: <question text>
        - Answer follows on next lines (can be multiline)
        - Block ends with: # on a separate line
        - Multiple FAQ blocks supported

        Returns:
            List of dicts: [{'question': '...', 'answer': '...', 'answer_html': '...'}, ...]
        """
        items = []

        if not self.content_markdown:
            return items

        lines = self.content_markdown.split('\n')
        current_question = None
        current_answer_lines = []
        in_faq_section = False
        in_faq_block = False

        for line in lines:
            # Check for FAQ section start: ### FAQ, ### Foire aux Questions, ### Les questions fréquentes, etc.
            if re.match(r'^\s*###\s*(?:FAQ|Foire aux [Qq]uestions|Les questions [Ff]réquentes|Questions [Ff]réquentes).*$', line, re.IGNORECASE):
                in_faq_section = True
                continue

            # Skip if not in FAQ section
            if not in_faq_section:
                continue

            # Check for question marker: #### Q:
            if re.match(r'^\s*####\s*Q\s*:\s*', line, re.IGNORECASE):
                # Save previous question if exists
                if current_question and current_answer_lines:
                    answer_md = '\n'.join(current_answer_lines).strip()
                    # Convert markdown to HTML
                    try:
                        import markdown as md_lib
                        answer_html = md_lib.markdown(
                            answer_md,
                            extensions=['extra', 'nl2br', 'sane_lists']
                        )
                    except Exception:
                        answer_html = answer_md

                    items.append({
                        'question': current_question,
                        'answer': answer_md,
                        'answer_html': answer_html
                    })

                # Start new question
                current_question = re.sub(r'^\s*####\s*Q\s*:\s*', '', line, flags=re.IGNORECASE).strip()
                current_answer_lines = []
                in_faq_block = True
                continue

            # Check for end marker: # on separate line
            if re.match(r'^\s*#\s*$', line) and in_faq_block:
                # Save current question
                if current_question and current_answer_lines:
                    answer_md = '\n'.join(current_answer_lines).strip()
                    try:
                        import markdown as md_lib
                        answer_html = md_lib.markdown(
                            answer_md,
                            extensions=['extra', 'nl2br', 'sane_lists']
                        )
                    except Exception:
                        answer_html = answer_md

                    items.append({
                        'question': current_question,
                        'answer': answer_md,
                        'answer_html': answer_html
                    })

                # Reset state
                current_question = None
                current_answer_lines = []
                in_faq_block = False
                # Exit FAQ section after end marker
                in_faq_section = False
                continue

            # Collect answer lines
            if in_faq_block and current_question:
                # Remove old "R :" prefix if present (backward compatibility)
                cleaned_line = re.sub(r'^\s*R\s*:\s*', '', line)
                current_answer_lines.append(cleaned_line)

        # Handle last question if FAQ block not closed with #
        if current_question and current_answer_lines:
            answer_md = '\n'.join(current_answer_lines).strip()
            try:
                import markdown as md_lib
                answer_html = md_lib.markdown(
                    answer_md,
                    extensions=['extra', 'nl2br', 'sane_lists']
                )
            except Exception:
                answer_html = answer_md

            items.append({
                'question': current_question,
                'answer': answer_md,
                'answer_html': answer_html
            })

        return items


class ArticleImage(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="articles/%Y/%m/%d/")
    alt = models.CharField(max_length=255, blank=True)
    caption = models.CharField(max_length=512, blank=True)
    order = models.PositiveIntegerField(default=1, help_text="1 = первая (обложка)")

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.article.title} - image {self.order}"

    def save(self, *args, **kwargs):
        """Override save to convert uploaded images to WebP for smaller size.

        - If Pillow is not available, fallback to default save.
        - If the file already has .webp extension, do nothing.
        - Converts preserving alpha when present.
        """
        if Image is None:
            return super().save(*args, **kwargs)

        if not self.image:
            return super().save(*args, **kwargs)

        name = getattr(self.image, 'name', '') or ''
        base, ext = os.path.splitext(name)
        if ext.lower() == '.webp':
            return super().save(*args, **kwargs)

        try:
            # Ensure file is ready
            self.image.open(mode='rb')
            img = Image.open(self.image)

            # Determine mode for conversion
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and 'transparency' in img.info):
                converted = img.convert('RGBA')
            else:
                converted = img.convert('RGB')

            webp_io = io.BytesIO()
            # quality 80 is a good balance; method 6 gives better compression if supported
            save_kwargs = {'format': 'WEBP', 'quality': 80, 'method': 6}
            # Pillow may not support 'method' on all builds; guard it
            try:
                converted.save(webp_io, **save_kwargs)
            except TypeError:
                # fallback without method
                converted.save(webp_io, format='WEBP', quality=80)

            webp_io.seek(0)
            new_name = f"{base}.webp"
            # Replace field content without saving model yet
            self.image.save(new_name, ContentFile(webp_io.read()), save=False)
        except Exception:
            # On any conversion failure, fall back to original file
            try:
                self.image.close()
            except Exception:
                pass
            return super().save(*args, **kwargs)

        # close original and save model with new webp
        try:
            self.image.close()
        except Exception:
            pass
        result = super().save(*args, **kwargs)

        # After saving the main image, create responsive WebP variants (srcset)
        try:
            storage = self.image.storage
            # reopen image via storage
            self.image.open('rb')
            img = Image.open(self.image)
            orig_w, orig_h = img.size
            # responsive widths to generate (in px)
            sizes = [320, 640, 960, 1280, 1920]
            base, ext = os.path.splitext(self.image.name)

            for w in sizes:
                if w >= orig_w:
                    # skip sizes larger or equal to original
                    continue
                new_name = f"{base}-{w}.webp"
                # avoid regenerating existing files
                if storage.exists(new_name):
                    continue

                ratio = w / float(orig_w)
                h = max(1, int(orig_h * ratio))
                resized = img.resize((w, h), Image.LANCZOS)
                buf = io.BytesIO()
                try:
                    resized.save(buf, format='WEBP', quality=80, method=6)
                except TypeError:
                    resized.save(buf, format='WEBP', quality=80)
                buf.seek(0)
                storage.save(new_name, ContentFile(buf.read()))
                try:
                    buf.close()
                except Exception:
                    pass
        except Exception:
            # non-fatal: if variant generation fails, continue silently
            pass

        return result

    @property
    def srcset(self):
        """Return a srcset string for responsive images (WebP variants).

        Example: '/media/articles/...-320.webp 320w, /media/...-640.webp 640w'
        """
        try:
            storage = self.image.storage
            base, ext = os.path.splitext(self.image.name)
            # check generated sizes in the same order as created
            sizes = [320, 640, 960, 1280, 1920]
            parts = []
            for w in sizes:
                name = f"{base}-{w}.webp"
                if storage.exists(name):
                    parts.append(f"{storage.url(name)} {w}w")

            # fallback: include main image URL with its width if nothing else
            if not parts and self.image:
                parts.append(f"{self.image.url} {Image.open(self.image).size[0]}w")

            return ", ".join(parts)
        except Exception:
            return ''


# ArticleFAQ model removed — FAQ content is now embedded in article markdown.


# Taxonomy models: Category and Tag (slugs auto-generated and unique)
class Category(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    color_bg = models.CharField(
        max_length=7,
        default='#f3e8ff',
        help_text="Background color (hex format, e.g., #f3e8ff)"
    )
    color_text = models.CharField(
        max_length=7,
        default='#7c3aed',
        help_text="Text color (hex format, e.g., #7c3aed)"
    )

    # SEO fields
    description = models.TextField(
        blank=True,
        verbose_name="Short description",
        help_text="Brief description shown at the top of category page (2-3 sentences)"
    )
    seo_text = models.TextField(
        blank=True,
        verbose_name="SEO content",
        help_text="Detailed SEO text shown at the bottom of category page (200-400 words for better Google indexing)"
    )

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_color_classes(self):
        """Return background and text colors for the category badge."""
        return {
            'bg': self.color_bg,
            'text': self.color_text
        }

    def get_absolute_url(self):
        """Return the canonical URL for this category."""
        return reverse('blog:category_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)[:140]
            slug = base
            i = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)[:110]
            slug = base
            i = 1
            while Tag.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)


class ArticleSeries(models.Model):
    """Series of related articles (e.g., tutorial series, multi-part guides)."""
    title = models.CharField(max_length=200, verbose_name="Series title")
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(verbose_name="Series description", help_text="Brief description of what this series covers")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Article Series"
        verbose_name_plural = "Article Series"
        ordering = ['title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:190]
            slug = base
            i = 1
            while ArticleSeries.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_articles(self):
        """Get all articles in this series ordered by series_order."""
        return self.articles.filter(status='published', is_page=False).order_by('series_order')


class ArticleLike(models.Model):
    """Track article likes from users and anonymous visitors."""
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='article_likes')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True, help_text="Session key for anonymous users")
    ip_address = models.GenericIPAddressField(help_text="IP address of liker")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['article', 'user'], ['article', 'session_key']]
        indexes = [
            models.Index(fields=['article', 'created_at']),
        ]

    def __str__(self):
        if self.user:
            return f"{self.user.username} likes {self.article.title}"
        return f"Anonymous ({self.session_key[:8]}) likes {self.article.title}"


class ArticleComment(models.Model):
    """Comments for blog articles with moderation and spam protection."""

    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
    ]

    # Relations
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='comments',
        help_text="Article being commented on"
    )
    author_profile = models.ForeignKey(
        'profiles.Profile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blog_comments',
        help_text="Profile if user is registered"
    )

    # For unregistered users
    author_name = models.CharField(
        max_length=100,
        help_text="Name (required for non-registered users)"
    )
    author_email = models.EmailField(
        help_text="Email (required for non-registered users)"
    )

    # Content
    comment = models.TextField(
        max_length=2000,
        help_text="Comment text (max 2000 characters)"
    )

    # Moderation
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    moderation_note = models.TextField(
        blank=True,
        help_text="Internal note for moderators"
    )
    moderated_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_comments'
    )
    moderated_at = models.DateTimeField(null=True, blank=True)

    # Threading (nested replies)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        help_text="Parent comment for nested replies"
    )

    # Anti-spam metadata
    ip_address = models.GenericIPAddressField(
        help_text="IP address of commenter"
    )
    user_agent = models.CharField(
        max_length=255,
        blank=True,
        help_text="Browser user agent"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    edited_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When comment was last edited by author"
    )

    # Engagement (optional)
    likes_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of likes"
    )

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Article Comment'
        verbose_name_plural = 'Article Comments'
        indexes = [
            models.Index(fields=['article', 'status', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        author = self.author_profile.display_name if self.author_profile else self.author_name
        return f"{author} on {self.article.title}"

    @property
    def author_display_name(self):
        """Return author name (from profile or manual entry)."""
        return self.author_profile.display_name if self.author_profile else self.author_name

    @property
    def can_edit(self):
        """Check if comment can still be edited (within 15 minutes)."""
        if not self.created_at:
            return False
        time_limit = timezone.now() - timezone.timedelta(minutes=15)
        return self.created_at > time_limit

    def approve(self, moderator=None):
        """Approve the comment."""
        self.status = 'approved'
        self.moderated_by = moderator
        self.moderated_at = timezone.now()
        self.save(update_fields=['status', 'moderated_by', 'moderated_at'])

    def reject(self, moderator=None, note=''):
        """Reject the comment."""
        self.status = 'rejected'
        self.moderated_by = moderator
        self.moderated_at = timezone.now()
        if note:
            self.moderation_note = note
        self.save(update_fields=['status', 'moderated_by', 'moderated_at', 'moderation_note'])


class BlogSettings(models.Model):
    """
    Singleton model for blog main page SEO content.
    Contains header and footer text blocks for /blog/ page.
    """
    title = models.CharField(
        max_length=200,
        default="Blog",
        verbose_name="Page Title (H1)"
    )
    header_text = models.TextField(
        blank=True,
        verbose_name="Header Description",
        help_text="Short introduction text displayed at the top of the blog page (2-3 sentences)"
    )
    footer_text = models.TextField(
        blank=True,
        verbose_name="Footer SEO Text",
        help_text="Detailed description displayed at the bottom of the blog page (200-300 words, with keywords)"
    )
    meta_title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Meta Title",
        help_text="SEO meta title for blog page"
    )
    meta_description = models.TextField(
        max_length=300,
        blank=True,
        verbose_name="Meta Description",
        help_text="SEO meta description for blog page"
    )

    class Meta:
        verbose_name = "Blog Settings"
        verbose_name_plural = "Blog Settings"

    def __str__(self):
        return "Blog Main Page Settings"

    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton pattern)."""
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance."""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj