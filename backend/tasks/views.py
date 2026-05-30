import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from django.shortcuts import get_object_or_404
from django.db.models import Q

from core.permissions import IsAdmin
from .models import Task, GeneratedImage, AuditLog, Job
from .serializers import TaskSerializer, GeneratedImageSerializer, AuditLogSerializer
from .email_service import send_task_assigned_email, send_task_submitted_email, send_task_accepted_email
from .ai_service import trigger_bg_generation

logger = logging.getLogger(__name__)


def _can_access_task(user, task):
    return user.is_authenticated


def _can_work_on_task(user, task):
    return user.is_authenticated


class AIGeneratorThrottle(UserRateThrottle):
    scope = 'ai_generate'

@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    return Response({
        "service": "Hairdrama Task Manager API",
        "status": "online",
        "health": "/api/tasks/system-health/",
        "docs_hint": "Use the Next.js frontend; API routes live under /api/",
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def system_health_check(request):
    db_status = "Healthy"
    try:
        from django.db import connection
        connection.ensure_connection()
    except Exception as e:
        db_status = f"Unhealthy: {str(e)}"
    return Response({
        "status": "online",
        "database_connectivity": db_status
    })

@api_view(['GET'])
@permission_classes([IsAdmin])
def list_audit_logs(request):
    logs = AuditLog.objects.all()
    serializer = AuditLogSerializer(logs, many=True)
    return Response(serializer.data)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def task_list_create(request):
    if request.method == 'GET':
        tasks = Task.objects.all()
        serializer = TaskSerializer(tasks, many=True, context={'request': request})
        return Response(serializer.data)

    elif request.method == 'POST':
        if request.user.role != 'admin':
            return Response({'error': 'Admin permission required'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = TaskSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            task = serializer.save(created_by=request.user)
            if task.assigned_to:
                task.status = 'assigned'
                task.save()
                try:
                    send_task_assigned_email(task)
                except Exception as e:
                    logger.error(e)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_tasks(request):
    tasks = Task.objects.filter(assigned_to=request.user)
    serializer = TaskSerializer(tasks, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)

    if not _can_access_task(request.user, task):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        serializer = TaskSerializer(task, context={'request': request})
        return Response(serializer.data)

    elif request.method == 'DELETE':
        if request.user.role != 'admin':
            return Response({'error': 'Admin permission required'}, status=status.HTTP_403_FORBIDDEN)
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([IsAdmin])
def assign_task(request, pk):
    task = get_object_or_404(Task, pk=pk)
    assigned_to_id = request.data.get('assigned_to_id')
    
    if not assigned_to_id:
        return Response({'error': 'assigned_to_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
    task.assigned_to_id = assigned_to_id
    task.status = 'assigned'
    task.save()
    
    try:
        send_task_assigned_email(task)
    except Exception as e:
        logger.error(e)
        
    serializer = TaskSerializer(task, context={'request': request})
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAdmin])
def accept_task(request, pk):
    task = get_object_or_404(Task, pk=pk)
    task.status = 'accepted'
    task.save()
    
    try:
        send_task_accepted_email(task, accepted=True)
    except Exception as e:
        logger.error(e)
        
    serializer = TaskSerializer(task, context={'request': request})
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAdmin])
def request_revision(request, pk):
    task = get_object_or_404(Task, pk=pk)
    feedback = request.data.get('feedback', '')
    
    task.status = 'revision_requested'
    if feedback and task.description:
        task.description = f"{task.description}\n\nRevision Feedback: {feedback}"
    elif feedback:
        task.description = f"Revision Feedback: {feedback}"
    task.save()
    
    try:
        send_task_accepted_email(task, accepted=False, feedback=feedback)
    except Exception as e:
        logger.error(e)
        
    serializer = TaskSerializer(task, context={'request': request})
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def start_task(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not _can_work_on_task(request.user, task):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
    task.status = 'in_progress'
    task.save()
    
    serializer = TaskSerializer(task, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_task(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not _can_work_on_task(request.user, task):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
    if task.generations.count() < 8:
        return Response({'error': 'Must generate exactly 8 variations before submitting.'}, status=status.HTTP_400_BAD_REQUEST)
        
    task.status = 'submitted'
    task.save()
    
    try:
        send_task_submitted_email(task)
    except Exception as e:
        logger.error(e)
        
    serializer = TaskSerializer(task, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIGeneratorThrottle])
def trigger_generation(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not _can_work_on_task(request.user, task):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    image_type = request.data.get('image_type')
    prompt = request.data.get('prompt', '')
    angle = request.data.get('angle', 'none')
    theme = request.data.get('theme', '')

    if not image_type or image_type not in ['white_background', 'theme', 'creative', 'model']:
        return Response({'error': 'Invalid image_type'}, status=status.HTTP_400_BAD_REQUEST)

    job = Job.objects.create(
        task=task,
        image_type=image_type,
        status='pending'
    )

    trigger_bg_generation(
        job_id=job.id,
        image_type=image_type,
        prompt=prompt,
        angle=angle,
        theme=theme
    )

    return Response({'job_id': str(job.id), 'status': job.status}, status=status.HTTP_202_ACCEPTED)

@api_view(['GET'])
@permission_classes([AllowAny])
def poll_job_status(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    image_url = job.image_url or ''
    if image_url and '/media/generations/' in image_url:
        host = request.build_absolute_uri('/')[:-1]
        filename = image_url.split('/media/generations/')[-1]
        image_url = f"{host}/media/generations/{filename}"
    return Response({
        'job_id': str(job.id),
        'status': job.status,
        'image_url': image_url,
        'error': job.error
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_generations(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not _can_access_task(request.user, task):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
    generations = task.generations.all()
    serializer = GeneratedImageSerializer(generations, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_generation(request, pk):
    gen = get_object_or_404(GeneratedImage, pk=pk)
    if not _can_work_on_task(request.user, gen.task):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
    gen.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
