from django.urls import path
from . import views, author_views

app_name = 'blog'

urlpatterns = [
    # Public blog views
    path('blog/', views.article_list, name='article_list'),
    path('blog/<slug:slug>/', views.category_detail, name='category_detail'),
    path('<slug:slug>/', views.article_detail, name='article_detail'),
    path('<slug:slug>/like/', views.like_article, name='like_article'),
    path('<slug:slug>/comment/', views.add_comment, name='add_comment'),

    # Author management views (requires can_write_articles permission)
    path('articles/new/', author_views.article_create, name='article_create'),
    path('articles/<slug:slug>/edit/', author_views.article_edit, name='article_edit'),
    path('articles/<slug:slug>/delete/', author_views.article_delete, name='article_delete'),
]
