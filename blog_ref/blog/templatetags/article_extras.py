from django import template
from django.utils.safestring import mark_safe
import re

try:
    import markdown as md
except ImportError:
    md = None

register = template.Library()


@register.filter
def markdown_to_html(value):
    """Convert Markdown text to HTML.

    Automatically removes YAML front matter (--- ... ---) and first H1 heading before rendering.

    Usage in template: {{ text|markdown_to_html }}
    """
    if not value:
        return ''
    if not md:
        # Fallback if markdown is not installed
        return value.replace('\n', '<br>')

    try:
        # Remove YAML front matter (--- at start, content, --- at end)
        # Pattern: starts with ---, any content, ends with ---
        # Made more robust to handle various newline patterns
        clean_value = re.sub(r'^---\s*\n.*?\n---\s*\n?', '', value, flags=re.DOTALL)

        # Remove first H1 heading (# Title) that appears at the start
        # This prevents duplication since H1 is already in the template
        clean_value = re.sub(r'^\s*#\s+.+?\n', '', clean_value, count=1)

        # Remove standalone '#' used as FAQ block terminator (before markdown conversion)
        # This prevents it from becoming an empty H1 tag
        clean_value = re.sub(r'\n\s*#\s*\n', '\n', clean_value)
        clean_value = re.sub(r'\n\s*#\s*$', '', clean_value)

        # Pre-process blockquotes with attribution
        # Find and replace BEFORE markdown processes them
        quote_blocks = []

        def replace_quote_with_placeholder(match):
            quote_text = match.group(1).strip()
            attribution_text = match.group(2).strip()

            # Store the complete HTML blockquote
            quote_html = f'<blockquote class="quote"><p class="quote__content">{quote_text}</p><footer class="quote__attribution">{attribution_text}</footer></blockquote>'
            quote_blocks.append(quote_html)

            # Return a simple placeholder WITHOUT > so markdown won't process it
            return f'\n___QUOTE_PLACEHOLDER_{len(quote_blocks)-1}___\n'

        # Match: > quote text followed by >> attribution on next line
        # This removes both lines from markdown processing
        clean_value = re.sub(
            r'^>\s*(.+?)\s*\n>>\s*(.+?)$',
            replace_quote_with_placeholder,
            clean_value,
            flags=re.MULTILINE
        )

        html = md.markdown(
            clean_value,
            extensions=['fenced_code', 'nl2br', 'tables', 'sane_lists']
        )

        # Post-process: replace placeholders with actual blockquote HTML
        for idx, quote_html in enumerate(quote_blocks):
            placeholder = f'___QUOTE_PLACEHOLDER_{idx}___'
            # Markdown might wrap it in <p> tags
            html = html.replace(f'<p>{placeholder}</p>', quote_html)
            html = html.replace(placeholder, quote_html)

        return mark_safe(html)
    except Exception:
        # Fallback on error
        return value.replace('\n', '<br>')


@register.filter
def split(value, sep=','):
    """Split a string by `sep` and return a list of trimmed parts.

    Usage in template: `{{ article.keywords|split:',' }}`
    """
    if value is None:
        return []
    try:
        parts = [p.strip() for p in str(value).split(sep)]
    except Exception:
        return []
    return [p for p in parts if p]


@register.filter
def trim(value):
    if value is None:
        return ''
    return str(value).strip()


@register.inclusion_tag('partials/category_menu.html', takes_context=True)
def category_menu(context):
    """Render the categories menu with both blog and product categories.

    Usage in template:
      {% load article_extras %}
      {% category_menu %}
    """
    blog_categories = []
    product_categories = []

    try:
        from blog.models import Category
        blog_categories = list(Category.objects.all())
    except Exception:
        pass

    try:
        from profiles.models import ProductCategory
        from django.db.models import Count
        # Only show categories that have at least one product
        product_categories = list(
            ProductCategory.objects.annotate(product_count=Count('products'))
            .filter(product_count__gt=0)
        )
    except Exception:
        pass

    return {
        'blog_categories': blog_categories,
        'product_categories': product_categories,
        'request': context.get('request')
    }
