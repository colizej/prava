from django.urls import path

from . import views

app_name = 'rewards'

urlpatterns = [
    path('heartbeat/', views.heartbeat_view, name='heartbeat'),
    path('spend/', views.spend_keys, name='spend'),
]
