from django.urls import path
from . import views

app_name = 'taskmanager'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('tasks/', views.list_tasks, name='list_tasks'),
    path('system/stats/', views.get_system_stats, name='get_system_stats'),
    path('monitor/', views.system_monitor, name='system_monitor'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('current-task/', views.current_task, name='current_task'),
    path('executing/', views.executing_task_info, name='executing_task_info'),
    
    #Schedulers
    path('schedule_tasks/', views.schedule_tasks, name='schedule_tasks'),
    path('disk_schedule/', views.disk_schedule, name='disk_schedule'),
    path('paging/', views.paging, name='paging'),
    path('page-replacement/', views.page_replacement_visualizer, name='page_replacement_visualizer'),
    path('page-replacement-line-graph/', views.page_replacement_line_graph, name='page_replacement_line_graph'),
    
    # Learning Module
    path('learn/', views.learning_module, name='learning_module'),
    path('schedule/', views.schedule_tasks, name='schedule_tasks'),
    path('get-algorithm-recommendation/', views.get_algorithm_recommendation, name='get_algorithm_recommendation'),
]
