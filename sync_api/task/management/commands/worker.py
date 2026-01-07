import time
from django.core.management.base import BaseCommand
from task.models import Task
from task.services import scrape_url
'''
Run in an infinite loop

Fetch ONE task with status = PENDING

Mark it RUNNING

Perform scraping

Save result

Mark COMPLETED or FAILED

Sleep if no tasks exist

'''
class Command(BaseCommand):
    help = "A simple command that says hello"

    def handle(self, *args, **options):
        while True:
            try:
                get_task = Task.objects.filter(status = 'PENDING').first()
                if get_task:
                
                    get_task.status = Task.STATUS_RUNNING
                    get_task.save()
                    self.stdout.write(f"Current STATUS for {get_task.id} is {get_task.status}")
                    scarpe_data = scrape_url(get_task.url)
                    get_task.result = scarpe_data
                    get_task.status = 'COMPLETED'
                    get_task.save()
                    self.stdout.write(f"Status changed for {get_task.url} from Running to , {get_task.status} and results are {get_task.result}")
                    time.sleep(10)
                else:
                    self.stdout.write("No tasks found. Entering Pyschosis for 10 seconds...")
                    time.sleep(10)
            except KeyboardInterrupt:
                self.stdout.write("Stopping task processor...")
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error: {e}"))
                time.sleep(5)
    # def handle(self, *args, **options):
    #     while True:
    #         get_task = Task.objects.filter(status = 'PENDING')
    #         if get_task:
    #             for task in get_task:
    #                 task.status = Task.STATUS_RUNNING
    #                 task.save()
    #                 self.stdout.write(f"Current STATUS for {task.url} is {task.status}")
    #                 scarpe_data = scrape_url(task.url)
    #                 task.result = scarpe_data
    #                 task.status = 'COMPLETED'
    #                 task.save()
    #                 self.stdout.write(f"Status changed for {task.url} from Running to , {task.status}")
    #         else:
    #             self.stdout.write("No tasks found. Entering Pyschosis for 10 seconds...")
    #             time.sleep(10)


# okay but isnt services or scrape_url also performing requests? which should block the django worker
'''
    pending_task = Task.objects.create(
        url = get_url,
        status = Task.STATUS_PENDING,
        
    )
    so i am saving the url the moment request arrives, even though its not included in JsonResponse
            return JsonResponse({
            'id':pending_task.id,
            'status':pending_task.status,
            'url':pending_task.url
        }
    if i dont include url in JsonResponse it does not print in worker for Pending tasks
'''
