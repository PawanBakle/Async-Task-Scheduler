import requests
import time    
import uuid
import datetime
import logging
from django.utils import timezone
from bs4 import BeautifulSoup
from celery import shared_task
from .models import Task
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
    # phase 1: Acquire the task (PENDING -> RUNNING) under OCC ---
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

    # Phase 2 Do the actual scraping work (RUNNING) ---
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

            # Persist incrementally so partial progress survives a later crash/exception.
            # Only touches the 'result' column -> does not interact with the
            # version-controlled status field, so this cannot race with OCC transitions.
            task.result = {
                "succeeded": all_results,
                "failed": failed_urls,
                "batch_size": len(urls)
            }
            task.save(update_fields=["result"])

            # Heartbeat update
            if (timezone.now() - last_heartbeat).total_seconds() >= heartbeat_interval:
                Task.objects.filter(pk=task.id).update(last_heartbeat=timezone.now())
                last_heartbeat = timezone.now()

        # All URLs failed -> treat the whole task as a failure (goes to except below, eligible for retry like before). Partial success is NOT retried here.
        if failed_urls and not all_results:
            raise Exception(f"All {len(urls)} URLs failed")

    except Exception as e:
        task.error_field = str(e)
        task.save(update_fields=['error_field'])
        if self.request.retries < self.max_retries:
            task.transition(Task.STATUS_RUNNING, Task.STATUS_PENDING)
            raise self.retry(exc=e)
        else:
            task.transition(Task.STATUS_RUNNING, Task.STATUS_FAILED)
            raise

    # Phase 3 marked COMPLETED
    with transaction.atomic():
        rows_affected = task.transition(Task.STATUS_RUNNING, Task.STATUS_COMPLETED)
        if rows_affected == 0:
            raise RuntimeError("Task stolen by reconciler")

# @shared_task(acks_late=True, max_retries=3, default_retry_delay=10, bind=True)
# def scrape_url(self, task_id):
#     # TRANSITION TO RUNNING ONCE the task is received
#     try:
#         with transaction.atomic():
#             task = Task.objects.get(pk=task_id)
#             current_version = task.version
#             if task.status != 'PENDING':
#                 raise RuntimeError('Invalid State')
#             # task.transition(Task.STATUS_PENDING, Task.STATUS_RUNNING)
#             task.transition(Task.STATUS_PENDING, Task.STATUS_RUNNING, expected_version=current_version)
#     except RuntimeError:
        
#         # if there is a version conflick, another worker takes it
#         logger.warning("Version conflict – task already taken")
#         return "Task already processed by another worker"
#     except Exception as e:
#         logger.error(f"Acquisition failed: {e}")
#         raise

#     heartbeat_interval = 5
#     last_heartbeat = timezone.now()
#     headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
#     try:

#         if ',' in task.url:  # Check if there are multiple URLs
#             urls = [u.strip() for u in task.url.split(',')]
#         else:
#             urls = [task.url]
        
#     all_results = []
#     failed_urls = []

#     for url in urls:
#         try:
#             response = requests.get(url, headers=headers, timeout=10)
#             response.raise_for_status()
#             soup = BeautifulSoup(response.text, "html.parser")
#             all_results.append({
#                 "url": url,
#                 "title": soup.title.string if soup.title else None,
#                 "link_counts": len(soup.find_all("a"))
#             })
#         except Exception as url_err:
#             failed_urls.append({"url": url, "error": str(url_err)})

#         # Persist incrementally regardless of per-url outcome
#         task.result = {
#             "succeeded": all_results,
#             "failed": failed_urls,
#             "batch_size": len(urls)
#         }
#         task.save(update_fields=["result"])

#         # Heartbeat update
#         if (timezone.now() - last_heartbeat).total_seconds() >= heartbeat_interval:
#             Task.objects.filter(pk=task.id).update(last_heartbeat=timezone.now())
#             last_heartbeat = timezone.now()

#     # After the loop: decide overall task outcome
#     if failed_urls and not all_results:
#         # everything failed → let the outer except path handle retry/failure
#         raise Exception(f"All {len(urls)} URLs failed")
#     # else: partial or full success — fall through to COMPLETED transition below
    
#     except Exception as e:
#         task.error_field = str(e)
#         task.save(update_fields=['error_field'])
#         if self.request.retries < self.max_retries:
#             task.transition(Task.STATUS_RUNNING, Task.STATUS_PENDING)
#             raise self.retry(exc=e)
#         else:
#             task.transition(Task.STATUS_RUNNING, Task.STATUS_FAILED)
#             raise



#     with transaction.atomic():
#         rows_affected = task.transition(Task.STATUS_RUNNING, Task.STATUS_COMPLETED)
#         if rows_affected == 0:
#             raise RuntimeError("Task stolen by reconciler")