from django.urls import path
from . import views

urlpatterns = [
    path('system-health/', views.system_health_check, name='system-health-check'),
    path('', views.task_list_create, name='task-list-create'),
    path('<uuid:pk>/', views.task_detail, name='task-detail'),
]