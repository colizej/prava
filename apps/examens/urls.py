from django.urls import path
from . import views

app_name = 'examens'

urlpatterns = [
    path('', views.categories, name='categories'),
    path('practice/', views.practice, name='practice'),
    path('practice/<slug:category_slug>/', views.practice, name='practice_category'),
    path('exam/', views.exam_mode, name='exam'),
    path('results/<uuid:uuid>/', views.results, name='results'),
    path('history/', views.history, name='history'),

    # API
    path('api/record-answer/', views.api_record_answer, name='api_record_answer'),
    path('api/finish/', views.api_finish_quiz, name='api_finish_quiz'),
]
