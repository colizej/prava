from django.utils.translation import get_language


class TranslatableFieldsMixin:
    """
    Mixin for Django models with multilingual fields.

    Expects fields named `field`, `field_nl`, `field_ru` (FR is the default/fallback).
    Provides `trans_name`, `trans_title`, `trans_description`, `trans_content`,
    `trans_excerpt` properties that return the correct language value automatically.
    """

    def _trans(self, field):
        lang = (get_language() or 'fr')[:2]
        if lang != 'fr':
            val = getattr(self, f'{field}_{lang}', None)
            if val:
                return val
        return getattr(self, field, '')

    @property
    def trans_name(self):
        return self._trans('name')

    @property
    def trans_title(self):
        return self._trans('title')

    @property
    def trans_description(self):
        return self._trans('description')

    @property
    def trans_content(self):
        return self._trans('content')

    @property
    def trans_excerpt(self):
        lang = (get_language() or 'fr')[:2]
        if lang != 'fr':
            val = getattr(self, f'excerpt_{lang}', None)
            if val:
                return val
        excerpt = getattr(self, 'excerpt', '')
        if excerpt:
            return excerpt
        content = getattr(self, 'content', '')
        return content[:200] if content else ''
