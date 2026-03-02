from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),

    # Script runner
    path('run/<str:script_id>/', views.run_script, name='run_script'),

    # Questions CRUD
    path('questions/', views.questions_list, name='questions'),
    path('questions/create/', views.question_create, name='question_create'),
    path('questions/<int:pk>/', views.question_detail, name='question_detail'),
    path('questions/<int:pk>/edit/', views.question_edit, name='question_edit'),
    path('questions/<int:pk>/delete/', views.question_delete, name='question_delete'),
    path('questions/<int:pk>/toggle/', views.question_toggle_active, name='question_toggle'),
]
