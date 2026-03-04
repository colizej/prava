from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def responsive_image(image_obj, sizes='(max-width: 768px) 100vw, 800px', css_class='w-full h-auto object-cover', alt_text='', loading='lazy'):
    """Render a responsive <picture> element for an ArticleImage instance.

    Parameters:
    - image_obj: ArticleImage instance (expects .image.url and .srcset property)
    - sizes: sizes attribute for img
    - css_class: CSS classes for the <img>
    - alt_text: optional alt text (fallback to image_obj.alt)
    - loading: loading attribute (e.g., 'lazy')

    Usage in template:
      {% load responsive_image %}
      {% responsive_image article.cover_image %}
    """
    if not image_obj:
        return ''

    # Проверяем есть ли файл изображения - проверяем name а не сам объект
    try:
        if not image_obj.image.name:
            return ''
    except (ValueError, AttributeError):
        return ''

    # try to obtain srcset from object; fallback to empty
    srcset = ''
    try:
        srcset = getattr(image_obj, 'srcset', '') or ''
    except Exception:
        srcset = ''

    # main image url
    try:
        src = image_obj.image.url
    except Exception:
        return ''

    if not src:
        return ''

    alt = alt_text or getattr(image_obj, 'alt', '') or ''

    # Get image dimensions if available
    width = ''
    height = ''
    try:
        if hasattr(image_obj.image, 'width') and hasattr(image_obj.image, 'height'):
            width = f' width="{image_obj.image.width}"'
            height = f' height="{image_obj.image.height}"'
    except Exception:
        pass

    # Build picture element: prefer WebP srcset if available
    picture_parts = ['<picture>']
    if srcset:
        # If srcset contains webp entries, use as source
        picture_parts.append(f'<source type="image/webp" srcset="{srcset}">')

    # Fallback img
    img_tag = f'<img src="{src}" srcset="{srcset}" sizes="{sizes}" class="{css_class}" alt="{alt}" loading="{loading}"{width}{height}>'
    picture_parts.append(img_tag)
    picture_parts.append('</picture>')

    return mark_safe('\n'.join(picture_parts))
