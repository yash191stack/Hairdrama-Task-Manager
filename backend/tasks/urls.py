from django.urls import path
from . import views

urlpatterns = [
    path('system-health/', views.system_health_check, name='system-health-check'),
    path('audit-logs/', views.list_audit_logs, name='list-audit-logs'),
    path('my-tasks/', views.my_tasks, name='my-tasks'),
    path('', views.task_list_create, name='task-list-create'),
    path('<uuid:pk>/', views.task_detail, name='task-detail'),
    path('<uuid:pk>/assign/', views.assign_task, name='assign-task'),
    path('<uuid:pk>/accept/', views.accept_task, name='accept-task'),
    path('<uuid:pk>/request-revision/', views.request_revision, name='request-revision'),
    path('<uuid:pk>/start/', views.start_task, name='start-task'),
    path('<uuid:pk>/submit/', views.submit_task, name='submit-task'),
    path('<uuid:pk>/generate/', views.trigger_generation, name='trigger-generation'),
    path('<uuid:pk>/generations/', views.get_generations, name='get-generations'),
]