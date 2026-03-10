from django.contrib.sitemaps import Sitemap
from .models import CodeArticle, RuleCategory


# Minimum content length to be included in sitemap and indexed by Google
_MIN_CONTENT_LEN = 200


class ArticleSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.9

    def items(self):
        # Exclude thin/abrogated/PDF-only articles from sitemap
        from django.db.models.functions import Length
        return (
            CodeArticle.objects
            .annotate(ct_len=Length('content_text'))
            .filter(ct_len__gte=_MIN_CONTENT_LEN)
        )

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class ReglCategorySitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.6

    def items(self):
        return RuleCategory.objects.all()

    def location(self, obj):
        return obj.get_absolute_url()
