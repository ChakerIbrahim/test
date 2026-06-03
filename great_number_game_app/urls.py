from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('guess', views.guess, name='guess'),
    path('reset', views.reset, name='reset'),
    path('submit_name', views.submit_name, name='submit_name'),
    path('leaderboard', views.leaderboard, name='leaderboard'),
]
