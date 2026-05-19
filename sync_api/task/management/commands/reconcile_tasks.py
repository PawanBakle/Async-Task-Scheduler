# myapp/management/commands/my_command.py
from django.core.management.base import BaseCommand
from datetime import datetime
from task.models import Task
import time
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q,F
from task.services import scrape_url
class Command(BaseCommand):
    help = 'A simple command that displays the current time' #

    def handle(self, *args, **options):
        
        # while True:
            threshold_time = timezone.now() - timedelta(seconds=15)
            try:
                # 
                # get_running_task = Task.objects.filter(status = 'RUNNING')
                
                get_running_task = Task.objects.filter(
                    status = Task.STATUS_RUNNING
                ).filter(
                    Q(last_heartbeat__lt=threshold_time) |
                    Q(last_heartbeat__isnull=True)
                )
                
                # get_running_task = Task.objects.filter(status = 'RUNNING',last_heartbeat__lt = threshold_time)
                # if get_running_task: XXX BETTER WAY TO HANDLE USING EXISTS()
                    # its a query set not an OBJECT 
                if get_running_task.exists():
                    

                    for task_ in get_running_task:
                            if task_.retry_count < Task.MAX_RETRIES:
                                Task.objects.filter(pk=task_.id).update(status='PENDING', retry_count=F('retry_count') + 1)
                                self.stdout.write(f'Task reset: {task_.url} → PENDING (retry {task_.retry_count + 1}/{Task.MAX_RETRIES})')
                        # else:
                        #     self.stdout.write(f'Some Issue {i.url} Last heartbeat: {i.status}')
                        #     re-queue the task into Redis so a Celery worker consumes it 
                                scrape_url.delay(task_.id)
                            else:
                                task_.mark_failed()
                else:
                    self.stdout.write("No stuck tasks found...")
                    return
                    # time.sleep(7)
            except Exception as e:
                # self.stdout.write(get_running_task)
                self.stdout.write(self.style.ERROR(f"Error: {e}"))
                return
                # time.sleep(5)
        # current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # self.stdout.write(self.style.SUCCESS(f'Current time is: {current_time}')) #
