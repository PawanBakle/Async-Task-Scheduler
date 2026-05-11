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
    idempotency_key = models.CharField(max_length=255, unique=True, null=True, blank=True)
    # id =  models.CharField(primary_key=True,max_length=50, null=False)
    url = models.URLField()
    version = models.IntegerField(default=0)
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
        if self.status not in [self.STATUS_RUNNING, self.STATUS_PENDING]:
            raise ValueError("Can only mark RUNNING or PENDING tasks as FAILED")
        self.status = self.STATUS_FAILED
        self.last_heartbeat = timezone.now()
        self.save()

    def transition(self, from_state, to_state, expected_version=None):
        """
        Atomic transition with optional OCC version check.
        """
        qs = Task.objects.filter(pk=self.pk, status=from_state)
        if expected_version is not None:
            qs = qs.filter(version=expected_version)
        
        rows = qs.update(
            status=to_state,
            last_heartbeat=timezone.now(),
            version=models.F('version') + 1  # increment version
        )
        
        if rows == 0:
            raise RuntimeError("Illegal transition or stale version")
        
        self.status = to_state
        self.version += 1
        return rows
    # def transition(self, from_state, to_state):
    #     rows = Task.objects.filter(
    #         pk=self.pk,
    #         status=from_state
    #     ).update(
    #         status=to_state,
    #         last_heartbeat=timezone.now()
    #     )

    #     if rows == 0:
    #         raise RuntimeError(
    #             f"Illegal or stolen transition {from_state} → {to_state}"
    #         )

    #     self.status = to_state
    #     return rows


