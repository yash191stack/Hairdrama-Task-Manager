from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Task
from .serializers import TaskSerializer
from .email_service import send_task_created_email, send_task_completed_email


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def task_list_create(request):
    import traceback
    try:
        if request.method == 'GET':
            tasks = Task.objects.filter(
                created_by=request.user
            ) | Task.objects.filter(
                assigned_to=request.user
            )
            tasks = tasks.distinct().order_by('-created_at')
            serializer = TaskSerializer(tasks, many=True)
            return Response(serializer.data)

        if request.method == 'POST':
            print(f"[DEBUG POST] Data received: {request.data}")
            serializer = TaskSerializer(data=request.data)
            if serializer.is_valid():
                task = serializer.save(created_by=request.user)
                print(f"[DEBUG POST] Task created in DB: {task.id}")
                try:
                    send_task_created_email(task)
                except Exception as e:
                    print(f'Email dispatch error: {e}')
                    traceback.print_exc()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            print(f"[DEBUG POST] Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(f"[CRITICAL ERROR] Crash in task_list_create: {e}")
        traceback.print_exc()
        return Response({
            'error': str(e),
            'traceback': traceback.format_exc(),
            'message': 'Server side crash inside task_list_create view'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def task_detail(request, pk):
    try:
        task = Task.objects.get(pk=pk)
    except Task.DoesNotExist:
        return Response({'error': 'Task nahi mila'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = TaskSerializer(task)
        return Response(serializer.data)

    if request.method == 'PUT':
        old_status = task.status
        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            updated_task = serializer.save()
            try:
                if old_status != 'completed' and updated_task.status == 'completed':
                    send_task_completed_email(updated_task)
            except Exception as e:
                print(f'Email error: {e}')
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
