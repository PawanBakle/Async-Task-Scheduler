import requests
import time    
import uuid
import datetime
import logging
from django.utils import timezone
from bs4 import BeautifulSoup
from celery import shared_task
from .models import Task,LostOwnership
from django.http import HttpResponseBadRequest, JsonResponse
from django.db import transaction
from threading import Thread
import threading
from django.db import transaction,connection, connections, close_old_connections

'''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField()
    status = models.CharField(max_length=25)
    result = models.JSONField(null=True, blank=True)
    error_field = models.TextField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
'''

logger = logging.getLogger(__name__)

@shared_task(acks_late=True, max_retries=3, default_retry_delay=10, bind=True)
def scrape_url(self, task_id):
    #phase 1 Acquire the task (PENDING -> RUNNING) under OCC
    try:
        with transaction.atomic():
            task = Task.objects.get(pk=task_id)
            current_version = task.version
            if task.status != 'PENDING':
                raise RuntimeError('Invalid State')
            task.transition(Task.STATUS_PENDING, Task.STATUS_RUNNING, expected_version=current_version)
    except RuntimeError:
        # Version conflict or wrong state -> another worker already took it
        logger.warning("Version conflict – task already taken")
        return "Task already processed by another worker"
    except Exception as e:
        logger.error(f"Acquisition failed: {e}")
        raise

    heartbeat_interval = 5
    last_heartbeat = timezone.now()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    owned_version = task.version
    # phase 2 Do the actual scraping work (RUNNING) 
    try:
        if ',' in task.url:  # Check if there are multiple URLs
            urls = [u.strip() for u in task.url.split(',')]
        else:
            urls = [task.url]

        all_results = []
        failed_urls = []

        for url in urls:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                all_results.append({
                    "url": url,
                    "title": soup.title.string if soup.title else None,
                    "link_counts": len(soup.find_all("a"))
                })
            except Exception as url_err:
                failed_urls.append({"url": url, "error": str(url_err)})

            task.update_if_owner(owned_version, result={
                "succeeded": all_results,
                "failed": failed_urls,
                "batch_size": len(urls),
            })
            # Persist incrementally so partial progress survives a later crash/exception.
            # Only touches the 'result' column -> does not interact with the
            # version-controlled status field, so this cannot race with OCC transitions.
            task.save(update_fields=["result"])

            # Heartbeat update — guarded by status=RUNNING so a task that has
            # already been reclaimed (e.g. by the reconciler) doesn't get its
            # heartbeat refreshed by a worker that no longer truly owns it.
            if (timezone.now() - last_heartbeat).total_seconds() >= heartbeat_interval:
                task.update_if_owner(owned_version, last_heartbeat=timezone.now())
                last_heartbeat = timezone.now()

        # All URLs failed -> treat the whole task as a failure (goes to except below,
        # eligible for retry like before). Partial success is NOT retried here.
        if failed_urls and not all_results:
            raise Exception(f"All {len(urls)} URLs failed")
    except LostOwnership:           # must come BEFORE the generic handler
        logger.warning("Lost ownership mid-scrape")
        return
    except Exception as e:
        try:
            task.update_if_owner(owned_version, error_field=str(e))
            if self.request.retries < self.max_retries:
                task.transition(Task.STATUS_RUNNING, Task.STATUS_PENDING, expected_version=owned_version)
                should_retry = True
            else:
                task.transition(Task.STATUS_RUNNING, Task.STATUS_FAILED, expected_version=owned_version)
                should_retry = False
        except (LostOwnership, RuntimeError):
            logger.warning("Lost ownership in failure path; not touching the row")
            return
        if should_retry:
            raise self.retry(exc=e)
        raise

    # phase 3 Mark COMPLETED (
    with transaction.atomic():
        rows_affected = task.transition(Task.STATUS_RUNNING, Task.STATUS_COMPLETED, expected_version=task.version)
        if rows_affected == 0:
            raise RuntimeError("Task stolen by reconciler")

