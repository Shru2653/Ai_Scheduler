from django.db import models
from django.utils import timezone

class MutexLock(models.Model):
    resource_name = models.CharField(max_length=255, unique=True)
    locked_by = models.CharField(max_length=255, null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)

    def acquire(self, process_id, timeout_seconds=30):
        if not self.is_locked or (self.expires_at and self.expires_at < timezone.now()):
            self.locked_by = process_id
            self.locked_at = timezone.now()
            self.expires_at = timezone.now() + timezone.timedelta(seconds=timeout_seconds)
            self.is_locked = True
            self.save()
            return True
        return False

    def release(self, process_id):
        if self.locked_by == process_id:
            self.locked_by = None
            self.locked_at = None
            self.expires_at = None
            self.is_locked = False
            self.save()
            return True
        return False

    def __str__(self):
        return f"{self.resource_name} - {'Locked' if self.is_locked else 'Unlocked'}"

class ProcessQueue(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class QueueItem(models.Model):
    queue = models.ForeignKey(ProcessQueue, on_delete=models.CASCADE, related_name='items')
    process_id = models.CharField(max_length=255)
    priority = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed')
    ], default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-priority', 'created_at']

    def __str__(self):
        return f"{self.process_id} - {self.status}"
