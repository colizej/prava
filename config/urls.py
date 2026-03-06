"""PermisReady — URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.shortcuts import render

from apps.blog.sitemaps import BlogSitemap, BlogCategorySitemap
from apps.main.sitemaps import StaticViewSitemap
from apps.reglementation.sitemaps import ArticleSitemap, ReglCategorySitemap
from apps.examens.sitemaps import ExamCategorySitemap, QuestionSitemap


def handler404_view(request, exception):
    return render(request, 'errors/404.html', status=404)


def handler500_view(request):
    return render(request, 'errors/500.html', status=500)


handler404 = handler404_view
handler500 = handler500_view

sitemaps = {
    'static': StaticViewSitemap,
    'blog': BlogSitemap,
    'blog-categories': BlogCategorySitemap,
    'articles': ArticleSitemap,
    'regl-categories': ReglCategorySitemap,
    'exam-categories': ExamCategorySitemap,
    'questions': QuestionSitemap,
}

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # i18n language switching
    path('i18n/', include('django.conf.urls.i18n')),

    # Apps
    path('', include('apps.main.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('blog/', include('apps.blog.urls')),
    path('reglementation/', include('apps.reglementation.urls')),
    path('examens/', include('apps.examens.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('shop/', include('apps.shop.urls')),
    path('rewards/', include('apps.rewards.urls')),


    # SEO
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Admin customization
admin.site.site_header = 'PermisReady Administration'
admin.site.site_title = 'PermisReady Admin'
admin.site.index_title = 'Gestion du site'
