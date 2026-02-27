"""PermisReady — URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap

from apps.blog.sitemaps import BlogSitemap, BlogCategorySitemap
from apps.main.sitemaps import StaticViewSitemap

sitemaps = {
    'static': StaticViewSitemap,
    'blog': BlogSitemap,
    'blog-categories': BlogCategorySitemap,
}

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Apps
    path('', include('apps.main.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('blog/', include('apps.blog.urls')),
    path('reglementation/', include('apps.reglementation.urls')),
    path('examens/', include('apps.examens.urls')),

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
