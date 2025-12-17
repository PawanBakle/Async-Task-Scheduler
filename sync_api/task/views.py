from django.shortcuts import render
import requests
import uuid
import datetime
from django.http import HttpResponseBadRequest, JsonResponse
from .services import scrape_url
from .models import Task
# Create your views here.
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
def show_page(request):
    print('request reached')
    previous_data = Task.objects.all()
    return render(request,'task/dashboard.html',{'previous_data':previous_data})

'''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField()
    status = models.CharField(max_length=25)
    result = models.JSONField(null=True, blank=True)
    error_field = models.TextField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
'''