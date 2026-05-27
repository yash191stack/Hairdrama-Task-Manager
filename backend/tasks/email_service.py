from django.core.mail import send_mail
from django.conf import settings
import threading


def send_email_async(subject, message, recipient):
    """Email background me bhejo — request block na ho"""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=True,
        )
    except Exception as e:
        print(f'Email error: {e}')


def send_task_created_email(task):
    try:
        recipient = task.assigned_to or task.created_by
        subject = f'New Task: {task.title}'
        message = f'Hi {recipient.name},\n\nNew task assigned: {task.title}\nPriority: {task.priority}\nCreated by: {task.created_by.name}\n\nTeam Hairdrama'
        t = threading.Thread(target=send_email_async, args=(subject, message, recipient.email))
        t.daemon = True
        t.start()
    except Exception as e:
        print(f'Email thread error: {e}')


def send_task_completed_email(task):
    try:
        subject = f'Task Completed: {task.title}'
        message = f'Hi {task.created_by.name},\n\nTask completed: {task.title}\n\nTeam Hairdrama'
        t = threading.Thread(target=send_email_async, args=(subject, message, task.created_by.email))
        t.daemon = True
        t.start()
    except Exception as e:
        print(f'Email thread error: {e}')
