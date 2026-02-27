from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('pricing/', views.pricing, name='pricing'),
    path('glossary/', views.glossary, name='glossary'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
]
