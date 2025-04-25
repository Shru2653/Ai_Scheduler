from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('tasks/', views.list_tasks, name='list_tasks'),
    path('tasks/create/', views.create_task, name='create_task'),
    path('system/stats/', views.get_system_stats, name='get_system_stats'),
    path('monitor/', views.system_monitor, name='system_monitor'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('current-task/', views.current_task, name='current_task'),
    path('executing/', views.executing_task_info, name='executing_task_info'),
    
    #Schedulers
    path('schedule_tasks/', views.schedule_tasks, name='schedule_tasks'),

]
