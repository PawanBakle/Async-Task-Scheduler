from django.db import models
import uuid
# Create your models here.

class Task(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_FAILED = 'FAILED'
    STATUS_CHOICES = ((STATUS_PENDING,'Pending'),(STATUS_COMPLETED,'Completed'),(STATUS_FAILED,'Failed'))

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # id =  models.CharField(primary_key=True,max_length=50, null=False)
    url = models.URLField()
    status = models.CharField(max_length=25,choices = STATUS_CHOICES)
    result = models.JSONField(null=True, blank=True)
    error_field = models.TextField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)