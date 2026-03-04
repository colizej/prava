from django.contrib.sitemaps import Sitemap
from .models import BlogPost, BlogCategory


class BlogSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return BlogPost.objects.filter(is_published=True)

    def lastmod(self, obj):
        """Smart lastmod: minor edits within 7 days of publish don't count."""
        if obj.published_at and obj.updated_at:
            if (obj.updated_at - obj.published_at).days <= 7:
                return obj.published_at
            return obj.updated_at
        return obj.updated_at or obj.published_at

    def location(self, obj):
        return obj.get_absolute_url()


class BlogCategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.5

    def items(self):
        return BlogCategory.objects.all()

    def location(self, obj):
        return obj.get_absolute_url()
