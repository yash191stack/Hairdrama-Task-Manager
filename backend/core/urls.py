from django.contrib import admin
from django.urls import path, include
from tasks import views as tasks_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.auth_urls')),
    path('api/users/', include('users.urls')),
    path('api/tasks/', include('tasks.urls')),
    path('api/jobs/<uuid:job_id>/status/', tasks_views.poll_job_status, name='poll-job-status'),
    path('api/generations/<uuid:pk>/', tasks_views.delete_generation, name='delete-generation'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)