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

    # Public question detail (SEO)
    path('q/<int:pk>/', views.question_detail, name='question_detail'),

    # Admin preview
    path('preview/<int:pk>/', views.question_preview, name='question_preview'),

    # Saved questions / Révisions
    path('mes-revisions/', views.my_list, name='my_list'),
    path('mes-revisions/<slug:list_slug>/', views.my_list, name='my_list_slug'),
    path('pratique/revisions/', views.practice_saved, name='practice_saved'),
    path('pratique/revisions/<slug:list_slug>/', views.practice_saved, name='practice_saved_slug'),

    # API
    path('api/record-answer/', views.api_record_answer, name='api_record_answer'),
    path('api/finish/', views.api_finish_quiz, name='api_finish_quiz'),
    path('api/toggle-saved/', views.api_toggle_saved, name='api_toggle_saved'),
]
