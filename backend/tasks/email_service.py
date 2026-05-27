import smtplib
import traceback
import threading
import requests
from django.core.mail import send_mail
from django.conf import settings


def _send_email_worker(subject, message, recipient):
    """
    Highly resilient email worker.
    Attempts HTTPS API (Resend) first since HTTPS is never blocked by cloud firewalls.
    Falls back to Gmail SMTP if RESEND_API_KEY is not configured or fails.
    """
    resend_api_key = getattr(settings, 'RESEND_API_KEY', '').strip()
    
    # --- METHOD 1: HTTPS API (Resend) - Best for Production Deployments ---
    if resend_api_key:
        print("[EMAIL THREAD] Resend API Key detected! Attempting HTTPS delivery...")
        try:
            url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json"
            }
            # Resend requires verified domains in prod. But they offer a free sandbox onboarding email
            # for testing, which allows sending emails to the account holder's email.
            sender_email = getattr(settings, 'RESEND_SENDER_EMAIL', 'onboarding@resend.dev').strip()
            if not sender_email:
                sender_email = 'onboarding@resend.dev'

            payload = {
                "from": sender_email,
                "to": [recipient],
                "subject": subject,
                "text": message
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code in [200, 201]:
                print(f"[EMAIL THREAD] HTTPS SUCCESS: Email delivered successfully to {recipient}!")
                return
            else:
                print(f"[EMAIL THREAD] HTTPS API returned error {response.status_code}: {response.text}. Falling back to SMTP...")
        except Exception as api_err:
            print(f"[EMAIL THREAD] HTTPS API Request failed: {api_err}. Falling back to SMTP...")

    # --- METHOD 2: Standard SMTP (Gmail) - Perfect for Local Machine ---
    print("[EMAIL THREAD] Attempting standard SMTP (Gmail) delivery...")
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        print("[EMAIL THREAD] ERROR: Gmail SMTP credentials missing. Aborting.")
        return

    # Check for SMTP Port restrictions (Railway / Render firewall)
    try:
        conn = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=3)
        conn.quit()
    except Exception as conn_err:
        print(f"[EMAIL THREAD] SMTP BLOCKED by host firewall: {conn_err}. Delivery aborted.")
        return

    try:
        result = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        print(f"[EMAIL THREAD] SMTP SUCCESS: Sent to {recipient}, result={result}")
    except Exception as e:
        print(f"[EMAIL THREAD] SMTP ERROR: Failed sending mail: {e}")
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
