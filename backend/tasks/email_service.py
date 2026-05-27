import smtplib
import traceback
from django.core.mail import send_mail
from django.conf import settings


def _send_email(subject, message, recipient):
    """
    Synchronous email sender — no threading, no daemon.
    Production mein daemon threads silently die ho jaate hain
    isliye direct synchronous call reliable hai.
    """
    try:
        print(f"[EMAIL] Attempting to send email to {recipient}")
        print(f"[EMAIL] Using HOST_USER: {settings.EMAIL_HOST_USER}")
        print(f"[EMAIL] Using HOST: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        print(f"[EMAIL] TLS: {settings.EMAIL_USE_TLS}, SSL: {getattr(settings, 'EMAIL_USE_SSL', False)}")
        print(f"[EMAIL] FROM: {settings.DEFAULT_FROM_EMAIL}")

        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            print("[EMAIL] ERROR: EMAIL_HOST_USER or EMAIL_HOST_PASSWORD is empty! Check .env file.")
            return False

        result = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        print(f"[EMAIL] SUCCESS — sent to {recipient}, result={result}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"[EMAIL] SMTP AUTH ERROR: Gmail credentials galat hain ya App Password invalid hai. Error: {e}")
        return False
    except smtplib.SMTPException as e:
        print(f"[EMAIL] SMTP ERROR: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"[EMAIL] UNEXPECTED ERROR: {e}")
        traceback.print_exc()
        return False


def send_task_created_email(task):
    """Task create hone par email bhejo"""
    try:
        recipient = task.assigned_to or task.created_by
        if not recipient or not recipient.email:
            print(f"[EMAIL] No valid recipient for task: {task.title}")
            return

        subject = f'New Task: {task.title}'
        message = (
            f'Hi {recipient.name},\n\n'
            f'New task assigned: {task.title}\n'
            f'Priority: {task.priority}\n'
            f'Created by: {task.created_by.name}\n\n'
            f'Team Hairdrama'
        )

        _send_email(subject, message, recipient.email)
        print(f"[EMAIL] Task creation email processed for: {task.title}")

    except Exception as e:
        print(f"[EMAIL] Error in send_task_created_email: {e}")
        traceback.print_exc()


def send_task_completed_email(task):
    """Task complete hone par email bhejo"""
    try:
        if not task.created_by or not task.created_by.email:
            print(f"[EMAIL] No valid creator email for task: {task.title}")
            return

        subject = f'Task Completed: {task.title}'
        message = (
            f'Hi {task.created_by.name},\n\n'
            f'Task completed: {task.title}\n\n'
            f'Team Hairdrama'
        )

        _send_email(subject, message, task.created_by.email)
        print(f"[EMAIL] Task completion email processed for: {task.title}")

    except Exception as e:
        print(f"[EMAIL] Error in send_task_completed_email: {e}")
        traceback.print_exc()
