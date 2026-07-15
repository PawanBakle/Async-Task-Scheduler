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
# Create your views here.

# def home_page(request):
#     return render(request, 'task/home_page.html')

def home_page(request):
    return redirect('show_tasks')  # Just redirect to dashboard

'''
def get_data(request):
    get_id = uuid.uuid4()
    if request.POST:
            
        try:
            get_url = request.POST.get('API','')
            if not get_url:
                return JsonResponse({"error": "URL is required"}, status=400)
            data = scrape_url(get_url)
        except Exception as e:
            return JsonResponse({'status':'failed','error':str(e)})
    # data = scrape_url(get_url)
    # return data
    # print(f"Request bod : {request.POST.get('text_field','NO DATA')}")
    # data = scrape_url(request)
    Task.objects.create( **{
        'id':str(get_id),
                         'url':get_url,
                         'status':'COMPLETED',
                         'result': data,
                         'error_field':'None',
                         'date_created':datetime.datetime.now()
    })

    
    return JsonResponse({'status':'ok','received':data})
'''
'''

XXX PHASE 1
def get_data(request):
    get_id = uuid.uuid4()
    if request.method != 'POST':
        return JsonResponse({"error": "POST required"}, status=405)
    get_url = request.POST.get('API','')
    if not get_url:
         return JsonResponse({"error":"URL is required"},status = 405)
    try:
            # get_url = request.POST.get('API','')
            # if not get_url:
            #     return JsonResponse({"error": "URL is required"}, status=400)
            data = scrape_url(get_url)
            Task.objects.create( 
                    url=get_url,
                    status="COMPLETED",
                    result = data
            )
    except Exception as e:

            task = Task.objects.create(
            url=get_url,
            status="FAILED",
            error_field=str(e)
            )
            return JsonResponse(
                {"status": "FAILED", "error": str(e)},
                status=500
            )
    
    return JsonResponse({
        "id": str(task.id),
        "status": task.status,
        "result": task.result
    })
    
    '''


# # XXX PHASE 2
# def get_data(request):
#     if request.method != 'POST':
#         return JsonResponse({"error":"POST Required"},status = 405)
#     get_url = request.POST.get('API','')
#     if not get_url:
#         return JsonResponse({"error: Incorrect URL"},status = 405)
#     pending_task = Task.objects.create(
#         url = get_url,
#         status = Task.STATUS_PENDING,
        
#     )
#     if pending_task.status == 'PENDING':
#         # print({
#         #     'id':pending_task.id,
#         #     'status':pending_task.status
#         # }
#         return JsonResponse({
#             'id':pending_task.id,
#             'status':pending_task.status
#         }
#     )
#     data = scrape_url(get_url)
#     if not data:

#         pending_task.status = Task.STATUS_FAILED
#         pending_task.save()
#     else:
        
#         pending_task.status = Task.STATUS_COMPLETED
#         pending_task.save()
#         return JsonResponse(
#             {
#             'id':pending_task.id,
#             'status':pending_task.status,
#             'result':pending_task.result
#             },status = 202
#         )
'''
Task object (5271fa0d-68a9-4f50-8f44-2f5e23596369) 
Task object (07992ab1-c638-4b76-8ab1-1f6abae25958) Task object 
(75852ef5-3d12-4663-80c9-b1a0f0cde4ba)
 Task object (4c7b42a7-c80c-4f0d-881a-5704b366a2ad)
   Task object (a07568e6-5134-4414-9526-3a38844d98e8)
'''


# # XXX PHASE 2.1
# def get_data(request):
#     if request.method != 'POST':
#         return JsonResponse({"error":"POST Required"},status = 405)
#     get_url = request.POST.get('API','')
#     if not get_url:
#         return JsonResponse({"error: Incorrect URL"},status = 405)
#     pending_task = Task.objects.create(
#         url = get_url,
#         status = Task.STATUS_PENDING,
        
#     )
#     if pending_task.status == 'PENDING':
#         # print({
#         #     'id':pending_task.id,
#         #     'status':pending_task.status
#         # }
#         return JsonResponse({
#             'id':pending_task.id,
#             'status':pending_task.status,
#             'url':pending_task.url
#         }
#     )
#     data = scrape_url(get_url)
#     if not data:

#         pending_task.status = Task.STATUS_FAILED
#         pending_task.save()
#     else:
#         # pending_task.result
#         pending_task.status = Task.STATUS_COMPLETED
#         pending_task.save()
#         return JsonResponse(
#             {
#             'id':pending_task.id,
#             'status':pending_task.status,
#             'result':pending_task.result
#             },status = 202
#         )

# celery worker working hard

'''
# XXX PHASE 3
def get_data(request):
    if request.method != 'POST':
        return JsonResponse({"error":"POST Required"},status = 405)
    get_url = request.POST.get('API','')
    if not get_url:
        return JsonResponse({"error: Incorrect URL"},status = 405)
    pending_task = Task.objects.create(
        url = get_url,
        status = Task.STATUS_PENDING,
        
    )
    print(pending_task.url)
    scrape_url.delay(str(pending_task.url))
    if pending_task.status == 'PENDING':
        # print({
        #     'id':pending_task.id,
        #     'status':pending_task.status
        # }
        return JsonResponse({
            'id':pending_task.id,
            'status':pending_task.status,
            'url':pending_task.url
        }
    )
    # data = scrape_url(get_url)
    # if not data:

    #     pending_task.status = Task.STATUS_FAILED
    #     pending_task.save()
    # else:
    #     # pending_task.result
    #     pending_task.status = Task.STATUS_COMPLETED
    #     pending_task.save()
    #     return JsonResponse(
    #         {
    #         'id':pending_task.id,
    #         'status':pending_task.status,
    #         'result':pending_task.result
    #         },status = 202
    #     )

'''

# XXX PHASE 4
# def get_data(request):
#     if request.method != 'POST':
#         return JsonResponse({"error":"POST Required"},status = 405)
#     get_url = request.POST.get('API','')
#     if not get_url:
#         return JsonResponse({"error: Incorrect URL"},status = 405)
#     pending_task = Task.objects.create(
#         url = get_url,
#         status = Task.STATUS_PENDING,
#     )
#     print(pending_task)
#     scrape_url.delay(pending_task.pk)
#     if pending_task.status == 'PENDING':
#         # print({
#         #     'id':pending_task.id,
#         #     'status':pending_task.status
#         # }
#         return JsonResponse({
#             'id':pending_task.pk,
#             'status':pending_task.status,
#             'url':pending_task.url
#         }
#     )
from django.shortcuts import redirect
from django.contrib import messages
import redis

# XXX Phase 5
# @require_POST
# def get_data(request):
#     if request.method != 'POST':
#         return JsonResponse({"error":"POST Required"},status=405)
    
#     get_url = request.POST.get('API','')
#     if not get_url:
#         messages.error(request, "Please provide a valid URL")
#         return redirect('show_page')
#     minute_bucket = timezone.now().replace(second=0, microsecond=0)
#     key_string = f"{get_url}:{minute_bucket.isoformat()}"
#     idempotency_key = hashlib.sha256(key_string.encode()).hexdigest()
#     # Strip the time bucket entirely
#     # The signature is driven purely by the resource itself

#     # Minute bucket prevents duplicates within same minute
# # But allows re-scraping across minutes (fresh data)
# # Trade-off: tasks taking >1 minute may create duplicate on retry

#     # URL BASED KEY. issue here is that user cannot send or rescrape same url again
#     # key_string = f"global_url:{get_url}"
#     # idempotency_key = hashlib.sha256(key_string.encode()).hexdigest()

#     # Check for existing task with same key ( RACE CONDITION )
#     # existing_task = Task.objects.filter(idempotency_key=idempotency_key).first()
#     # if existing_task:
#     #     # Return existing task instead of creating new one
#     #     return JsonResponse({
#     #         'id': existing_task.pk,
#     #         'status': existing_task.status,
#     #         'url': existing_task.url,
#     #         'duplicate': True
#     #     })

#     # pending_task = Task.objects.create(
#     #     url=get_url,
#     #     status=Task.STATUS_PENDING,
#     #     idempotency_key=idempotency_key
#     # )
    
#     pending_task, created = Task.objects.get_or_create(
#     idempotency_key=idempotency_key,
#     defaults={'url': get_url, 'status': Task.STATUS_PENDING}
# )
#     if not created:
#         messages.info(request, f"Task already exists (status: {pending_task.status})")
#     # Existing task found
#         # return JsonResponse({
#         #     'id': pending_task.pk,
#         #     'status': pending_task.status,
#         #     'message': 'Duplicate request – returning existing task'
#         # })
#     scrape_url.delay(pending_task.pk)    
#     messages.success(request, f'Task created! Scraping: {get_url[:50]}...')
#     return redirect('show_page')
#     # return JsonResponse({
#     #     'id': pending_task.pk,
#     #     'status': pending_task.status,
#     #     'url': pending_task.url
#     # })


@require_POST
def get_data(request):
    # Form submission – redirects back to dashboard
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

# def show_page(request):
#     print('request reached')
#     previous_data = Task.objects.all()
#     return render(request,'task/dashboard.html',{'previous_data':previous_data})

'''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField()
    status = models.CharField(max_length=25)
    result = models.JSONField(null=True, blank=True)
    error_field = models.TextField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
'''

     # though i need a user here for user based Hash GENERATION
    # key_string = f"user_{request.user.id}:{get_url}"
    # idempotency_key = hashlib.sha256(key_string.encode()).hexdigest()
    # userid = request.user.id
   
    # redis_key = f"IdempotencyKey{IndentationError}"
    # ttl = 86400