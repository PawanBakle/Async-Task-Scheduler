from django.urls import path
from . import views
urlpatterns = [
    path('',views.home_page),
    path('show_tasks/',views.show_page,name = 'show_tasks'),
    path('provide_data/',views.get_data,name = 'provide-data'),
    path('get_user_data/<str:pk>/',views.user_task,name = 'user_data')

]