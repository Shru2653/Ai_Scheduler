

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

# Task Model
class Task(models.Model):
    CATEGORY_CHOICES = [
        ('System', 'System Task'),
        ('User', 'User Task'),
        ('Background', 'Background Process'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Running', 'Running'),
        ('Completed', 'Completed'),
    ]
    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='User')
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=1)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    def __str__(self):
        return f"{self.title} - {self.status}"


# System Resource Stats
class SystemStats(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    cpu_usage = models.FloatField()
    memory_usage = models.FloatField()
    disk_usage = models.FloatField()

    def __str__(self):
        return f"Stats @ {self.timestamp}"

# Task Execution History
class TaskHistory(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    executed_at = models.DateTimeField(auto_now_add=True)
    duration = models.DurationField()
    was_successful = models.BooleanField(default=True)

    def __str__(self):
        return f"History of {self.task.title}"
