import smtplib
import traceback
import threading
from django.core.mail import send_mail
from django.conf import settings


def _send_email_worker(subject, message, recipient):
    """
    Background worker that runs inside a thread.
    Uses strict timeouts to prevent hanging on network-restricted platforms like Railway.
    """
    try:
        print(f"[EMAIL THREAD] Starting SMTP send to {recipient}")
        
        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            print("[EMAIL THREAD] ERROR: SMTP credentials missing in settings.")
            return

        # Explicitly test connection with a very low timeout first
        print(f"[EMAIL THREAD] Verifying connection to {settings.EMAIL_HOST}:{settings.EMAIL_PORT}...")
        try:
            # Low timeout of 3 seconds so we don't hang the worker if blocked by Railway firewall
            conn = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=3)
            conn.quit()
            print("[EMAIL THREAD] Port is open and reachable!")
        except Exception as conn_err:
            print(f"[EMAIL THREAD] NETWORK BLOCK ALERT: Port is blocked or unreachable: {conn_err}")
            return

        # Attempt actual Django send_mail
        result = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        print(f"[EMAIL THREAD] SUCCESS: Sent to {recipient}, result={result}")

    except Exception as e:
        print(f"[EMAIL THREAD] ERROR: Failed sending mail: {e}")
        traceback.print_exc()


def _send_email_async(subject, message, recipient):
    """
    Launches the email sender in a separate thread.
    This ensures that even if SMTP is blocked, the HTTP request is NOT blocked.
    """
    try:
        thread = threading.Thread(
            target=_send_email_worker,
            args=(subject, message, recipient)
        )
        thread.daemon = True
        thread.start()
        print(f"[EMAIL ASYNC] Thread dispatched for recipient: {recipient}")
    except Exception as e:
        print(f"[EMAIL ASYNC] Thread dispatch failed: {e}")
        traceback.print_exc()


def send_task_created_email(task):
    """Task creation email entry point"""
    try:
        recipient = task.assigned_to or task.created_by
        if not recipient or not recipient.email:
            print(f"[EMAIL] Invalid recipient for task: {task.title}")
            return

        subject = f'New Task: {task.title}'
        message = (
            f'Hi {recipient.name},\n\n'
            f'New task assigned: {task.title}\n'
            f'Priority: {task.priority}\n'
            f'Created by: {task.created_by.name}\n\n'
            f'Team Hairdrama'
        )

        _send_email_async(subject, message, recipient.email)

    except Exception as e:
        print(f"[EMAIL] Exception in send_task_created_email dispatch: {e}")
        traceback.print_exc()


def send_task_completed_email(task):
    """Task completion email entry point"""
    try:
        if not task.created_by or not task.created_by.email:
            print(f"[EMAIL] Invalid creator for task: {task.title}")
            return

        subject = f'Task Completed: {task.title}'
        message = (
            f'Hi {task.created_by.name},\n\n'
            f'Task completed: {task.title}\n\n'
            f'Team Hairdrama'
        )

        _send_email_async(subject, message, task.created_by.email)

    except Exception as e:
        print(f"[EMAIL] Exception in send_task_completed_email dispatch: {e}")
        traceback.print_exc()
