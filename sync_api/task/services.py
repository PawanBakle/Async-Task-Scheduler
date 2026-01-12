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
from threading import Thread
import threading
from django.db import connection, connections, close_old_connections
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
    # task = Task.objects.select_for_update().get(pk=pending_task)  XXX Wrong to put task before LOCKING OR ELSE OTHER WORKERS WILL FETCH IT


    # TODO create a HeartBeat thread to run and keep updating the time to show reconciler it is ALIVE
    class HeartBeat(threading.Thread):
        def __init__(self, task_id):
            super().__init__()
            close_old_connections()
            self.task_id = task_id
            self.task_ = Task.objects.get(pk = task_id)
            self.stop_event = threading.Event()
            self.daemon = True
            
        def stop(self):
            self.stop_event.set()
            
            return
        def run(self):
            # while not self.stop_event.is_set():
            #     self.task_.save(update_fields=['last_heartbeat'])
            #     # if self.stop_event.is_set():
            # connections.close()
            while not self.stop_event.is_set():
                try:
                    # self.task_.save(update_fields=['last_heartbeat'])
                    Task.objects.filter(pk = self.task_id).update(last_heartbeat = timezone.now())
                    if self.stop_event.wait(timeout=5):
                        break
                # if self.stop_event.is_set():
                except Exception as e:
                    print('An Error occured in the thread {e}')
                finally:
                    connections.close()

            print('thread Closed')
    # task = Task.objects.select_for_update().get(pk=pending_task)
    heart_beat = HeartBeat(pending_task)    

    # XXX LOCKING THE TASK AND NOT RUNNING YET
    try:
        with transaction.atomic():

            task = Task.objects.select_for_update().get(pk=pending_task)
            heart_beat = HeartBeat(task.id)
        # task = Task.objects.get(pk = pending_task)
            task.last_heartbeat = timezone.now()
            task.save(update_fields=["last_heartbeat"])
            print(f'1- Status of task right now {task.status}')
            if task.status != 'PENDING':
                return
            # task.status = task.STATUS_RUNNING
            task.mark_running()
            # task.save()
            # task.last_heartbeat = timezone.now()
            # task.save(update_fields=["last_heartbeat"])
            print(f'2 - Task status right now {task.status}')

            # return 'Task Acquired'
    except Exception as e:
        # The transaction is automatically rolled back if an exception occurs within the block
        print(f"An unexpected error occurred: {e}. Transaction rolled back.")
        return "Error acquiring task."

    
    # XXX ACTUAL TASK RUNNING  I/O (NOT IN LOCKING)
    heart_beat.start()
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
            # task.save(update_fields=["last_heartbeat"])
            break 
    except ConnectionError as e:
            task.error_field = str(e)
            # task.status = task.STATUS_FAILED
            # task.save()
            task.mark_failed()
            print(f'task failed with mehh{task.status}')
            raise self.retry(exc=e)
            # return JsonResponse(
            #         {"status": "FAILED", "error": str(e)},
            #         status=500
            #     )
    finally:
        heart_beat.stop()


    #XXX AGAIN LOCK TO COMPLETE THE TASK 
    try:
        with transaction.atomic(): 
            # if task.status != 'PENDING':
            #     task.mark_completed()
            # else:
            #     return
            # Instead of task.save(), use a filtered update
            rows_affected = Task.objects.filter(
                pk=pending_task, 
                status=Task.STATUS_RUNNING  
            ).update(
                status=Task.STATUS_COMPLETED,
                
                last_heartbeat=timezone.now()
            )

            if rows_affected == 0:
                print("CRITICAL: Task was stolen by Reconciler! Abandoning work.")
                return
            # task.status = task.STATUS_COMPLETED
            # task.last_heartbeat = timezone.now()
            # task.save(update_fields=["last_heartbeat"])
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
    except Exception as e:
        # The transaction is automatically rolled back if an exception occurs within the block
        print(f"An unexpected error occurred: {e}. Transaction rolled back.")
        return "Error acquiring task."

    
    finally:
        heart_beat.stop()

'''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField()
    status = models.CharField(max_length=25)
    result = models.JSONField(null=True, blank=True)
    error_field = models.TextField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
'''