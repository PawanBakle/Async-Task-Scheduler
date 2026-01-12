from django.db import models
import uuid
from django.utils import timezone
# Create your models here.

class Task(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_RUNNING = 'RUNNING'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_FAILED = 'FAILED'
    STATUS_CHOICES = ((STATUS_PENDING,'Pending'),(STATUS_RUNNING,'RUNNING'),(STATUS_COMPLETED,'Completed'),(STATUS_FAILED,'Failed'))

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # id =  models.CharField(primary_key=True,max_length=50, null=False)
    url = models.URLField()
    status = models.CharField(max_length=25,choices = STATUS_CHOICES)
    result = models.JSONField(null=True, blank=True)
    error_field = models.TextField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    last_heartbeat = models.DateTimeField(null=True,blank=True)
    retry_count = models.IntegerField(default = 0)
    MAX_RETRIES = 3

    def mark_pending(self):
        self.status = Task.STATUS_PENDING
        self.save()
    def mark_running(self):
        if self.status != Task.STATUS_PENDING:
            raise ValueError("Invalid Transition")
        self.status = Task.STATUS_RUNNING
        self.last_heartbeat = timezone.now()
        self.save()
    def mark_completed(self):
        if self.status != Task.STATUS_RUNNING:
            raise ValueError()
        self.status = Task.STATUS_COMPLETED
        self.last_heartbeat = timezone.now()
        self.save()
    def mark_failed(self):
        if self.status != Task.STATUS_RUNNING or self.status != Task.STATUS_PENDING:
            raise ValueError()
        self.status = Task.STATUS_PENDING
        self.last_heartbeat = timezone.now()
        self.save()
