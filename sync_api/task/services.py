import requests
import uuid
import datetime
from django.utils import timezone
from bs4 import BeautifulSoup
from celery import shared_task
from .models import Task
import time    
from django.http import HttpResponseBadRequest, JsonResponse
from django.db import transaction
# # url = 'https://jsonplaceholder.typicode.com/posts'
# url = 'https://example.com/'
# response = requests.get(url, timeout=10)
# print(f'HEADERS -> {response.headers}')
# print('\nJSON\n')
# # print(f'Data -> {response.json()}')
# print('\n')
# bond = response.raise_for_status()
# print(bond)

# print(f'STATUS CODE -> {response.status_code}')
# print(f'RESPONSE TEXT -> {response.text}')
# soup = BeautifulSoup(response.text, "html.parser")

# print(f'SOUP -> {soup}')
# title = soup.title.string if soup.title else None
# print(F'TITLE -> {title}')
# links_count = len(soup.find_all("a"))

# print(f'COUNT OF THE LINKS ->{links_count} ')

# @shared_task
@shared_task(acks_late=True, max_retries=3, default_retry_delay=10)
def scrape_url(pending_task):
    # task received
    task = Task.objects.select_for_update().get(pk=pending_task)
    with transaction.atomic():
    # task = Task.objects.get(pk = pending_task)
        task.last_heartbeat = timezone.now()
        task.save(update_fields=["last_heartbeat"])
        print(f'1- Status of task right now {task.status}')
        if task.status != 'PENDING':
            return
        task.status = task.STATUS_RUNNING
        
        task.save()
        task.last_heartbeat = timezone.now()
        task.save(update_fields=["last_heartbeat"])
        print(f'2 - Task status right now {task.status}')
    try:
        while True:
            task_url = task.url

            print('sleeping for a few secs')
            time.sleep(5)
            
            task.save()
            print('WOKE UP...HELL YEAH')
            response = requests.get(task_url, timeout=10)

            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            link_counts = len(soup.find_all("a"))
            title = soup.title.string if soup.title else None
            get_id = uuid.uuid4()

            task.result = {
                        "title" : title,
                        "link_counts":link_counts
                        }
            task.save(update_fields=["last_heartbeat"])
            break  
        task.status = task.STATUS_COMPLETED
        task.last_heartbeat = timezone.now()
        task.save(update_fields=["last_heartbeat"])
            # task.save()
        print(f'task status NOW {task.status} with {task.result}')
        task.save()
            # return {
            #     # 'id':str(get_id),
            #     # 'url':url,
            #     'status':response.status_code,
            #     'result': {
            #             "title" : title,
            #             "link_counts":link_counts
            #             },
            #     # 'error_field': response.raise_for_status() if response.raise_for_status() else None,
            #     # 'date_created': datetime.datetime.now()
            # }
    except ConnectionError as e:
            task.error_field = str(e)
            task.status = task.STATUS_FAILED
            task.save()
            print(f'task failed with mehh{task.status}')
            raise self.retry(exc=e)
            # return JsonResponse(
            #         {"status": "FAILED", "error": str(e)},
            #         status=500
            #     )
    

'''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField()
    status = models.CharField(max_length=25)
    result = models.JSONField(null=True, blank=True)
    error_field = models.TextField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
'''