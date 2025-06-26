from django.contrib import admin
from .models import Task, SystemStats, TaskHistory

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'priority', 'start_time', 'end_time', 'status')
    search_fields = ('title', 'user__username')
    list_filter = ('status', 'category')

@admin.register(SystemStats)
class SystemStatsAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'cpu_usage', 'memory_usage', 'disk_usage')
    list_filter = ('timestamp',)

@admin.register(TaskHistory)
class TaskHistoryAdmin(admin.ModelAdmin):
    list_display = ('task', 'executed_at', 'duration', 'was_successful')
    list_filter = ('was_successful',)
