from django.urls import path
from . import views

urlpatterns = [
    path('input/', views.input_processes, name='input_processes'),
    path('visualize/', views.visualize_schedule, name='visualize_schedule'),
]
