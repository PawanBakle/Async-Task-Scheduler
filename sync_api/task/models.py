from django.db import models
import uuid
from django.utils import timezone
# Create your models here.
class LostOwnership(Exception):
    pass
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
            raise RuntimeError("illegal transition or stale version")
        
        self.status = to_state
        self.version += 1
        return rows
    # to make sure 2 same workers don't workers over write in same states
    def update_if_owner(self, owned_version, **fields):
        rows = Task.objects.filter(
            pk=self.pk,
            status=Task.STATUS_RUNNING,
            version=owned_version,
        ).update(**fields)
        if rows == 0:
            raise LostOwnership(f"{self.pk}is no longer owned at version {owned_version}")