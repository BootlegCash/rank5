# competitions/urls.py
from django.urls import path
from . import views

app_name = 'competitions'

urlpatterns = [
    path('',          views.competition_list,   name='competition_list'),
    path('create/',   views.competition_create, name='competition_create'),
    path('<int:pk>/', views.competition_detail, name='competition_detail'),
    path('<int:pk>/delete/', views.delete_competition, name='delete_competition'),
]
