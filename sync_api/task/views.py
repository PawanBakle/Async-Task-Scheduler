from django.shortcuts import render
import requests
import uuid
import hashlib
import logging
import datetime
from django.http import HttpResponseBadRequest, JsonResponse
from django.utils import timezone
from .services import scrape_url
from .models import Task
from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db import IntegrityError
logger = logging.getLogger(__name__)
from django.shortcuts import redirect
from django.contrib import messages
import redis


@require_POST
def get_data(request):
    # Form submission . redirects back to dashboard
    get_url = request.POST.get('API', '').strip()
    
    if not get_url:
        messages.error(request, "Please provide a valid URL")
        return redirect('show_page')
    
    # Idempotency key (minute bucket)
    minute_bucket = timezone.now().replace(second=0, microsecond=0)
    key_string = f"{get_url}:{minute_bucket.isoformat()}"
    idempotency_key = hashlib.sha256(key_string.encode()).hexdigest()
    
    try:
        pending_task, created = Task.objects.get_or_create(
            idempotency_key=idempotency_key,
            defaults={'url': get_url, 'status': Task.STATUS_PENDING}
        )
    except IntegrityError:
        # Race condition if someone else created it
        pending_task = Task.objects.get(idempotency_key=idempotency_key)
        created = False
    
    if created:
        try:
            scrape_url.delay(pending_task.pk)
            messages.success(request, f"Task created! Scraping: {get_url[:50]}...")
        except Exception as e:
            logger.error(f"Failed to queue task: {e}")
            pending_task.status = Task.STATUS_FAILED
            pending_task.error_field = str(e)
            pending_task.save()
            messages.error(request, f"Failed to queue task: {e}")
    else:
        messages.info(request, f"Task already exists (status: {pending_task.status})")
    
    return redirect('show_page')

def user_task(request, pk):
    # API endpoint – returns JSON for polling
    task = get_object_or_404(Task, id=pk)
    
    response = {
        'id': task.id,
        'status': task.status,
        'url': task.url,
    }
    
    if task.status == Task.STATUS_COMPLETED and task.result:
        response['result'] = task.result
    elif task.status == Task.STATUS_FAILED:
        response['error'] = task.error_field
    elif task.status == Task.STATUS_RUNNING:
        response['last_heartbeat'] = task.last_heartbeat
    
    return JsonResponse(response)

def show_page(request):
    tasks = Task.objects.all().order_by('-date_created')
    paginator = Paginator(tasks, 25)  # 25 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'task/dashboard.html', {'page_obj': page_obj})
