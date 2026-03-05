from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.pricing, name='pricing'),
    path('checkout/<slug:plan_key>/', views.checkout, name='checkout'),
    path('return/', views.payment_return, name='return'),
    path('webhook/', views.webhook, name='webhook'),
    path('success/<uuid:order_id>/', views.success, name='success'),
]
