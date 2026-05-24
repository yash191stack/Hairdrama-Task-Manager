from django.core.mail import send_mail
from django.conf import settings


def send_task_created_email(task):
    
    try:
        recipient = task.assigned_to or task.created_by
        subject = f'New Task Assigned: {task.title}'
        message = f"""
Hi {recipient.name},

A new task has been assigned to you on Hairdrama Task Manager.

Task Details:
- Title: {task.title}
- Description: {task.description or 'No description'}
- Priority: {task.priority.upper()}
- Status: {task.status}
- Created by: {task.created_by.name}

Login to view and manage your tasks.

Team Hairdrama
        """
        send_mail(
            subject=subject,
            message=message.strip(),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            fail_silently=True,  # email fail ho to app crash na ho
        )
    except Exception as e:
        print(f'Email send error: {e}')


def send_task_completed_email(task):
    
    try:
        subject = f'Task Completed: {task.title}'
        message = f"""
Hi {task.created_by.name},

Good news! A task has been marked as completed.

Task Details:
- Title: {task.title}
- Completed by: {task.assigned_to.name if task.assigned_to else 'You'}
- Priority: {task.priority.upper()}

Keep up the great work!

Team Hairdrama
        """
        send_mail(
            subject=subject,
            message=message.strip(),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[task.created_by.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f'Email send error: {e}')