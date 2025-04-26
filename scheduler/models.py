from django.db import models

# Create your models here.
class Process(models.Model):
    name = models.CharField(max_length=20)
    arrival_time = models.IntegerField()
    burst_time = models.IntegerField()
    priority = models.IntegerField()

    def __str__(self):
        return self.name