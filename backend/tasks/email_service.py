from django.core.mail import send_mail
from django.conf import settings


def send_email_sync(subject, message, recipient):
    """Email synchronously bhejo taaki serverless ya gunicorn threads freeze na hon"""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,  # Set to False so we can see errors in backend logs if any
        )
    except Exception as e:
        print(f'Email send error: {e}')


def send_task_created_email(task):
    try:
        recipient = task.assigned_to or task.created_by
        subject = f'New Task: {task.title}'
        message = f'Hi {recipient.name},\n\nNew task assigned: {task.title}\nPriority: {task.priority}\nCreated by: {task.created_by.name}\n\nTeam Hairdrama'
        send_email_sync(subject, message, recipient.email)
    except Exception as e:
        print(f'Email dispatch error on task creation: {e}')


def send_task_completed_email(task):
    try:
        subject = f'Task Completed: {task.title}'
        message = f'Hi {task.created_by.name},\n\nTask completed: {task.title}\n\nTeam Hairdrama'
        send_email_sync(subject, message, task.created_by.email)
    except Exception as e:
        print(f'Email dispatch error on task completion: {e}')

