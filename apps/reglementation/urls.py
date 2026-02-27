from django.urls import path
from . import views

app_name = 'reglementation'

urlpatterns = [
    path('', views.index, name='index'),
    path('panneaux/', views.signs_list, name='signs'),
    path('panneaux/<str:sign_type>/', views.signs_by_type, name='signs_by_type'),
    path('category/<slug:slug>/', views.category_detail, name='category'),
    path('<slug:slug>/', views.article_detail, name='article'),
]
