from django.contrib.sitemaps import Sitemap
from .models import ExamCategory, Question


class ExamCategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        return ExamCategory.objects.all()

    def location(self, obj):
        return obj.get_absolute_url()


class QuestionSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.8

    def items(self):
        return Question.objects.filter(is_active=True).select_related('category')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()
