from django.contrib.sitemaps import Sitemap
from .models import CodeArticle, RuleCategory


class ArticleSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.9

    def items(self):
        return CodeArticle.objects.all()

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
