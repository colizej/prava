from django.contrib.sitemaps import Sitemap
from django.utils import timezone
from django.db.models import Q
from .models import Article

class ArticleSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        # Only published articles that are currently visible (status='published' AND published_at <= now OR null)
        now = timezone.now()
        return Article.objects.filter(
            status='published'
        ).filter(
            Q(published_at__lte=now) | Q(published_at__isnull=True)
        ).exclude(
            slug__isnull=True
        ).exclude(
            slug=''
        ).order_by('-published_at')

    def lastmod(self, obj):
        """Smart lastmod: show updated_at only for significant content updates.

        Minor edits (links, typos, formatting) within 7 days of publication
        don't trigger sitemap updates. Real content updates after 7 days do.
        """
        if obj.published_at and obj.updated_at:
            days_diff = (obj.updated_at - obj.published_at).days

            # Minor edits within 7 days = don't show as "updated" in sitemap
            if days_diff <= 7:
                return obj.published_at

            # Real content update after 7+ days = show in sitemap
            else:
                return obj.updated_at

        return obj.updated_at or obj.published_at

    def location(self, obj):
        return obj.get_absolute_url()
