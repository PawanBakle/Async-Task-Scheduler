# myapp/management/commands/my_command.py
from django.core.management.base import BaseCommand
from datetime import datetime
from task.models import Task
import time
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q,F
class Command(BaseCommand):
    help = 'A simple command that displays the current time' #

    def handle(self, *args, **options):
        
        while True:
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
                if get_running_task:
                    # its a query set not an OBJECT 
                    for task_ in get_running_task:
                            if task_.retry_count < Task.MAX_RETRIES:
                                    
                            # if i.last_heartbeat:
                                self.stdout.write(f'Task running or fucked up for {task_.status}: {task_.url} Last heartbeat:= {task_.last_heartbeat}')
                                # i.status = i.STATUS_PENDING
                                # i.save(update_fields=["status"])
                                Task.objects.filter(pk = task_.id).update(status = 'PENDING',retry_count = F('retry_count') + 1)
                                # task_.mark_pending()
                                # i.save()
                                self.stdout.write(f' Fewww... Task updated from RUNNING to {task_.status} ')
                                # self.stdout.write(f'Task running or fucked up {get_running_task} Last heartbeat: {get_running_task.last_heartbeat}')
                                time.sleep(2)
                        # else:
                        #     self.stdout.write(f'Some Issue {i.url} Last heartbeat: {i.status}')
                            else:
                                task_.mark_failed()
                else:
                    self.stdout.write("No tasks found. Entering Pyschosis for 7 seconds...")
                    time.sleep(7)
            except Exception as e:
                # self.stdout.write(get_running_task)
                self.stdout.write(self.style.ERROR(f"Error: {e}"))
                time.sleep(5)
        # current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # self.stdout.write(self.style.SUCCESS(f'Current time is: {current_time}')) #
