from django.conf import settings


def site_context(request):
    """Context processor global — disponible dans tous les templates."""
    return {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'PRAVA.be'),
        'SITE_DESCRIPTION': getattr(settings, 'SITE_DESCRIPTION', ''),
        'LANGUAGES': getattr(settings, 'LANGUAGES', []),
        'current_language': getattr(request, 'LANGUAGE_CODE', 'fr'),
    }
