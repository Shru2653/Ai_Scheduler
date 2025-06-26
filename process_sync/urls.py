from django.urls import path
from . import views

app_name = 'process_sync'

urlpatterns = [
    path('', views.index, name='index'),
    path('mutex/acquire/', views.acquire_lock, name='acquire_lock'),
    path('mutex/release/', views.release_lock, name='release_lock'),
    path('queue/create/', views.create_queue, name='create_queue'),
    path('queue/add/', views.add_to_queue, name='add_to_queue'),
    path('queue/status/', views.get_queue_status, name='get_queue_status'),
] 