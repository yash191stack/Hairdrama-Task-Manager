import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Task
from .serializers import TaskSerializer
from .email_service import send_task_created_email, send_task_completed_email

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def task_list_create(request):
    """
    List all tasks related to the authenticated user, or create a new task.
    """
    if request.method == 'GET':
        tasks = Task.objects.filter(
            created_by=request.user
        ) | Task.objects.filter(
            assigned_to=request.user
        )
        tasks = tasks.distinct().order_by('-created_at')
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            task = serializer.save(created_by=request.user)
            
            # Send email notifications in the background to avoid blocking the request thread
            try:
                send_task_created_email(task)
            except Exception as e:
                logger.error(f"Failed to dispatch task creation email: {e}", exc_info=True)
                
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def task_detail(request, pk):
    """
    Retrieve, update or delete a task instance.
    """
    try:
        task = Task.objects.get(pk=pk)
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

    # Permission Check: Only creator or assignee can interact with the task
    if task.created_by != request.user and task.assigned_to != request.user:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        serializer = TaskSerializer(task)
        return Response(serializer.data)

    elif request.method == 'PUT':
        old_status = task.status
        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            updated_task = serializer.save()
            
            # Send completion notification if status transitions to completed
            if old_status != 'completed' and updated_task.status == 'completed':
                try:
                    send_task_completed_email(updated_task)
                except Exception as e:
                    logger.error(f"Failed to dispatch task completion email: {e}", exc_info=True)
                    
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
