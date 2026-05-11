import requests
import uuid
import datetime
import logging
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
logger = logging.getLogger(__name__)
# @shared_task
@shared_task(acks_late=True, max_retries=3, default_retry_delay=10)
def scrape_url(task_id):
    # task received
    # task = Task.objects.select_for_update().get(pk=pending_task)  XXX Wrong to put task before LOCKING OR ELSE OTHER WORKERS WILL FETCH IT


    # TODO create a HeartBeat thread to run and keep updating the time to show reconciler it is ALIVE
    class HeartBeat(threading.Thread):
        def __init__(self, task_id):
            super().__init__()
            close_old_connections() #FOR CLOSING OLD DATABASE CONNECTIONS
            self.task_id = task_id
            self.task_ = Task.objects.get(pk = task_id)
            self.stop_event = threading.Event()
            self.daemon = True
            
        def stop(self):
            self.stop_event.set()
            
            # return
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

            # print('thread Closed')
            logger.info("Thread Closed,Heart Beat Stopped", extra={"task_id": str(self.task_id)})
    # task = Task.objects.select_for_update().get(pk=pending_task)
    # heart_beat = HeartBeat(pending_task)    

    # XXX LOCKING THE TASK AND NOT RUNNING YET SO THAT
    # OTHER WORKERS DON'T PICK UP THE SAME OBJECT FROM DATABASE
    try:
        with transaction.atomic():
            task  = Task.objects.get(pk = task_id)
            # task = Task.objects.select_for_update().get(pk=pending_task) XXX NO NEED SINCE USING task.TRANSITION
            # task = Task.objects.select_for_update().get(pk=pending_task)
            heart_beat = HeartBeat(task.id)
        # task = Task.objects.get(pk = pending_task)
            task.last_heartbeat = timezone.now()
            task.save(update_fields=["last_heartbeat"])
            # logger.info(f'1- Status of task right now {task.status}',extra={"task_id": str(task.id)})
            logger.info("task_acquired", extra={"task_id": str(task.id), "status": task.status})

            # print(f'1- Status of task right now {task.status}')
            if task.status != 'PENDING':
                # return REPLACE WITH EXCEPTION
                raise RuntimeError('Invalid State')
            # task.status = task.STATUS_RUNNING
            # task.mark_running()
            task.transition(Task.STATUS_PENDING, Task.STATUS_RUNNING)

            # task.save()
            # task.last_heartbeat = timezone.now()
            # task.save(update_fields=["last_heartbeat"])
            # logger.info(f'2 - Task status right now {task.status}',extra={"task_id": str(task.id)})
            logger.info("task_running", extra={"task_id": str(task.id), "status": task.status})

            # print(f'2 - Task status right now {task.status}')

            # return 'Task Acquired'
    except Exception as e:
        # The transaction is automatically rolled back if an exception occurs within the block
        logger.error(f"An unexpected error occurred: {e}. Transaction rolled back.", exc_info=True)
        # print(f"An unexpected error occurred: {e}. Transaction rolled back.")
        raise RuntimeError("Error acquiring task.")
        # return "Error acquiring task."

    
    # XXX ACTUAL TASK RUNNING  I/O (NOT IN LOCKING)
    # CONTINUE SENDING THE HEARTBEAT DURING THE I/O TASK 
    heart_beat.start()
    try:
        while True:
            task_url = task.url
            logger.info('sleeping for a few secs',extra={"task_id": str(task.id)})
            # print('sleeping for a few secs')
            time.sleep(5)
            
#             Task.objects.filter(pk=task.pk).update(
#     result=task.result
# )
            #task.save()

            logger.info('Woke Up.. Executing Tasks',extra={"task_id": str(task.id)})
            # print('WOKE UP...HELL YEAH')
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
            task.save(update_fields=["result"])
            break 
    except ConnectionError as e:
            task.error_field = str(e)
            task.save(update_fields=['error_field'])   # add this
            task.transition(Task.STATUS_RUNNING, Task.STATUS_FAILED)

            logger.error(f'task failed with mehh{task.status}', exc_info=True)
            # print(f'task failed with mehh{task.status}')
            # raise self.retry(exc=e)
            raise scrape_url.retry(exc=e)

            # return JsonResponse(
            #         {"status": "FAILED", "error": str(e)},
            #         status=500
            #     )
    finally:
        heart_beat.stop()


    #XXX AGAIN LOCK TO COMPLETE THE TASK SO OTHER WORKER DON'T PICK UP THE RUNNING TASK
    try:
        with transaction.atomic(): 
            # if task.status != 'PENDING':
            #     task.mark_completed()
            # else:
            #     return
            # Instead of task.save(), use a filtered update
            # rows_affected = Task.objects.filter(
            #     pk=pending_task, 
            #     status=Task.STATUS_RUNNING  
            # ).update(
            #     status=Task.STATUS_COMPLETED,
                
            #     last_heartbeat=timezone.now()
            # )
            rows_affected =task.transition(Task.STATUS_RUNNING,Task.STATUS_COMPLETED)


            # IF ANY OTHER WORKER PICKS UP THE TASK JUST RETURN 
            if rows_affected == 0:
                logger.info("CRITICAL: Task was stolen by Reconciler! Abandoning work.")
                # print("CRITICAL: Task was stolen by Reconciler! Abandoning work.")
                # return
                raise RuntimeError("CRITICAL: Task was stolen by Reconciler! Abandoning work.")
            # task.status = task.STATUS_COMPLETED
            # task.last_heartbeat = timezone.now()
            # task.save(update_fields=["last_heartbeat"])
                # task.save()
            # logger.info(f'task status NOW {task.status} with {task.result}')
            logger.info("task_saved", extra={"task_id": str(task.id), "status": task.status})

            # print(f'task status NOW {task.status} with {task.result}')
            
            # task.save()

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
        logger.error(f"An unexpected error occurred: {e}. Transaction rolled back.", exc_info=True)
        # print(f"An unexpected error occurred: {e}. Transaction rolled back.")
        # return "Error acquiring task."
        raise RuntimeError("Error acquiring Task")

    
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

# @shared_task(acks_late=True, max_retries=3, default_retry_delay=10, bind=True)
# def scrape_url(self, task_id):  
#     heart_beat = None
    
#     class HeartBeat(threading.Thread):
#         def __init__(self, t_id):
#             super().__init__()
#             self.task_id = t_id
#             self.stop_event = threading.Event()
#             self.daemon = True

#         def stop(self):
#             self.stop_event.set()

#         def run(self):
            
            
#             while not self.stop_event.is_set():
#                 close_old_connections()
#                 try:
#                     Task.objects.filter(pk=self.task_id).update(last_heartbeat=timezone.now())
#                 except Exception as e:
#                     logger.error(f"An Error occurred in heartbeat thread: {e}")
                
#                 # Sleep safely using the stop_event timeout check
#                 if self.stop_event.wait(timeout=5):
#                     break
            
#             # Close connection only once when the thread is completely finished
#             connections.close()
#             logger.info("Thread Closed, Heart Beat Stopped", extra={"task_id": str(self.task_id)})

#     # 1. Acquire and lock task transition safely
    
#     # XXX LOCKING THE TASK AND NOT RUNNING YET SO THAT
#     # OTHER WORKERS DON'T PICK UP THE SAME OBJECT FROM DATABASE
#     try:
#         with transaction.atomic():
        
#             task = Task.objects.get(pk=task_id)
            
#             if task.status != 'PENDING':
#                 raise RuntimeError('Invalid State')

#             task.last_heartbeat = timezone.now()
#             task.save(update_fields=["last_heartbeat"])
#             logger.info("task_acquired", extra={"task_id": str(task.id), "status": task.status})

#             task.transition(Task.STATUS_PENDING, Task.STATUS_RUNNING)
#             logger.info("task_running", extra={"task_id": str(task.id), "status": task.status})
            

#             heart_beat = HeartBeat(task.id)
#     except Exception as e:
#         logger.error(f"An unexpected error occurred during acquisition: {e}. Transaction rolled back.", exc_info=True)
#         raise RuntimeError("Error acquiring task.")

#     # 2. Run the scraping task
#         # XXX ACTUAL TASK RUNNING  I/O (NOT IN LOCKING)
#     # CONTINUE SENDING THE HEARTBEAT DURING THE I/O TASK 
#     heart_beat.start()
#     try:
#         task_url = task.url
#         logger.info('sleeping for a few secs', extra={"task_id": str(task.id)})
#         time.sleep(5)
#         # Task.objects.filter(pk=task.pk).update(
# #     result=task.result
# # )
#             #task.save()
#         logger.info('Woke Up.. Executing Tasks', extra={"task_id": str(task.id)})
        
#         response = requests.get(task_url, timeout=10)
#         response.raise_for_status()
        
#         soup = BeautifulSoup(response.text, "html.parser")
#         link_counts = len(soup.find_all("a"))
#         title = soup.title.string if soup.title else None
        
#         task.result = {
#             "title": title,
#             "link_counts": link_counts
#         }
#         task.save(update_fields=["result"])

#     except Exception as e:  
#         task.error_field = str(e)
#         task.save(update_fields=['error_field'])
        
      
#         if self.request.retries < self.max_retries:
#             # Revert state back to PENDING so the next retry run can acquire it
#             task.transition(Task.STATUS_RUNNING, Task.STATUS_PENDING)
#             logger.warning(f"Task failed, retrying... Status reverted to PENDING.", exc_info=True)
#             raise self.retry(exc=e)
#         else:
#             # Out of retries, mark as permanently FAILED
#             task.transition(Task.STATUS_RUNNING, Task.STATUS_FAILED)
#             logger.error(f"Task permanently failed after max retries.", exc_info=True)
#             raise e
#     finally:
#         if heart_beat:
#             heart_beat.stop()

#     # 3. Finalize and mark completed
#     try:
#         with transaction.atomic():
#         # if task.status != 'PENDING':
#             #     task.mark_completed()
#             # else:
#             #     return
#             # Instead of task.save(), use a filtered update
#             # rows_affected = Task.objects.filter(
#             #     pk=pending_task, 
#             #     status=Task.STATUS_RUNNING  
#             # ).update(
#             #     status=Task.STATUS_COMPLETED,
                
#             #     last_heartbeat=timezone.now()
#             # )
#             rows_affected = task.transition(Task.STATUS_RUNNING, Task.STATUS_COMPLETED)
            
#             # IF ANY OTHER WORKER PICKS UP THE TASK JUST RETURN 
#             if rows_affected == 0:
#                 logger.info("CRITICAL: Task was stolen by Reconciler! Abandoning work.")
#                 raise RuntimeError("CRITICAL: Task was stolen by Reconciler! Abandoning work.")
#             logger.info("task_saved", extra={"task_id": str(task.id), "status": task.status})
#     except Exception as e:
#         logger.error(f"An unexpected error occurred during finalization: {e}. Transaction rolled back.", exc_info=True)
#         raise RuntimeError("Error completing Task")
#     finally:
#         if heart_beat:
#             heart_beat.stop()
