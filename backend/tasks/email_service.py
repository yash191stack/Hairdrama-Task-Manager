import smtplib
import traceback
import threading
import requests
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

def _send_html_email_worker(subject, text_content, html_content, recipient):
    resend_key = getattr(settings, 'RESEND_API_KEY', '').strip()
    
    if resend_key:
        try:
            sender = getattr(settings, 'RESEND_SENDER_EMAIL', 'onboarding@resend.dev').strip()
            if not sender:
                sender = 'onboarding@resend.dev'
                
            url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {resend_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "from": sender,
                "to": [recipient],
                "subject": subject,
                "text": text_content,
                "html": html_content
            }
            res = requests.post(url, json=payload, headers=headers, timeout=10)
            if res.status_code in [200, 201]:
                return
        except Exception:
            pass

    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        return

    try:
        conn = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=3)
        conn.quit()
    except Exception:
        return

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
    except Exception:
        traceback.print_exc()

def _send_email_async(subject, text, html, recipient):
    try:
        thread = threading.Thread(
            target=_send_html_email_worker,
            args=(subject, text, html, recipient)
        )
        thread.daemon = True
        thread.start()
    except Exception:
        traceback.print_exc()

def get_base_html_template(title, body_content):
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #f4f5f7;
            margin: 0;
            padding: 0;
            -webkit-font-smoothing: antialiased;
        }}
        .wrapper {{
            width: 100%;
            background-color: #f4f5f7;
            padding: 40px 0;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
        }}
        .header {{
            background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
            padding: 32px;
            text-align: center;
        }}
        .header h1 {{
            color: #ffffff;
            font-size: 24px;
            font-weight: 700;
            margin: 0;
        }}
        .content {{
            padding: 32px;
            color: #374151;
            line-height: 1.6;
        }}
        .content h2 {{
            font-size: 20px;
            margin-top: 0;
            color: #111827;
        }}
        .footer {{
            background-color: #f9fafb;
            padding: 24px;
            text-align: center;
            font-size: 12px;
            color: #9ca3af;
            border-top: 1px border #e5e7eb;
        }}
        .btn {{
            display: inline-block;
            background-color: #4f46e5;
            color: #ffffff !important;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            margin-top: 24px;
        }}
        .meta-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .meta-table td {{
            padding: 10px 0;
            border-bottom: 1px solid #f3f4f6;
        }}
        .meta-label {{
            font-weight: 600;
            color: #6b7280;
            width: 150px;
        }}
        .meta-value {{
            color: #1f2937;
        }}
    </style>
</head>
<body>
    <div class="wrapper">
        <div class="container">
            <div class="header">
                <h1>TaskHub Studio</h1>
            </div>
            <div class="content">
                {body_content}
            </div>
            <div class="footer">
                &copy; 2026 TaskHub Inc. All rights reserved.<br>
                This is an automated notification. Please do not reply directly.
            </div>
        </div>
    </div>
</body>
</html>"""

def send_task_assigned_email(task):
    if not task.assigned_to or not task.assigned_to.email:
        return
        
    subject = f"New Task Assigned: {task.title}"
    link = f"{settings.FRONTEND_URL}/dashboard"
    
    body = f"""
    <h2>Hello {task.assigned_to.name},</h2>
    <p>A new product photography and background replacement task has been assigned to you. Please log in to your dashboard to access the AI Studio and begin generating the 8 variations.</p>
    
    <table class="meta-table">
        <tr>
            <td class="meta-label">Task Title</td>
            <td class="meta-value">{task.title}</td>
        </tr>
        <tr>
            <td class="meta-label">Description</td>
            <td class="meta-value">{task.description or 'No description provided'}</td>
        </tr>
        <tr>
            <td class="meta-label">Created By</td>
            <td class="meta-value">{task.created_by.name}</td>
        </tr>
    </table>
    
    <div style="text-align: center;">
        <a href="{link}" class="btn">View Task Dashboard</a>
    </div>
    """
    
    text = f"Hello {task.assigned_to.name},\n\nNew task assigned: {task.title}\nDescription: {task.description}\nLink: {link}"
    html = get_base_html_template(subject, body)
    
    _send_email_async(subject, text, html, task.assigned_to.email)

def send_task_submitted_email(task):
    if not task.created_by or not task.created_by.email:
        return
        
    subject = f"Task Completed: {task.title} by {task.assigned_to.name if task.assigned_to else 'User'}"
    link = f"{settings.FRONTEND_URL}/dashboard"
    
    body = f"""
    <h2>Hello {task.created_by.name},</h2>
    <p>The user has generated all 8 background-consistent variations and submitted the task for your review.</p>
    
    <table class="meta-table">
        <tr>
            <td class="meta-label">Task Title</td>
            <td class="meta-value">{task.title}</td>
        </tr>
        <tr>
            <td class="meta-label">Submitted By</td>
            <td class="meta-value">{task.assigned_to.name if task.assigned_to else 'Unknown'}</td>
        </tr>
        <tr>
            <td class="meta-label">Total Variations</td>
            <td class="meta-value">8 of 8 Generated</td>
        </tr>
    </table>
    
    <div style="text-align: center;">
        <a href="{link}" class="btn">Review Submissions</a>
    </div>
    """
    
    text = f"Hello {task.created_by.name},\n\nTask {task.title} has been submitted by {task.assigned_to.name if task.assigned_to else 'User'}.\nLink: {link}"
    html = get_base_html_template(subject, body)
    
    _send_email_async(subject, text, html, task.created_by.email)

def send_task_accepted_email(task, accepted=True, feedback=''):
    if not task.assigned_to or not task.assigned_to.email:
        return
        
    status_str = "Accepted" if accepted else "Revision Requested"
    subject = f"Task {status_str}: {task.title}"
    link = f"{settings.FRONTEND_URL}/dashboard"
    
    message_intro = "Congratulations! Your generated images have been approved by the administrator." if accepted else "The administrator reviewed your submissions and requested some revisions."
    
    feedback_section = ""
    if not accepted and feedback:
        feedback_section = f"""
        <div style="background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 16px; margin: 20px 0; border-radius: 4px;">
            <strong style="color: #991b1b; display: block; margin-bottom: 4px;">Revision Feedback:</strong>
            <span style="color: #7f1d1d;">{feedback}</span>
        </div>
        """
        
    body = f"""
    <h2>Hello {task.assigned_to.name},</h2>
    <p>{message_intro}</p>
    
    <table class="meta-table">
        <tr>
            <td class="meta-label">Task Title</td>
            <td class="meta-value">{task.title}</td>
        </tr>
        <tr>
            <td class="meta-label">Review Status</td>
            <td class="meta-value" style="font-weight: 700; color: {'#10b981' if accepted else '#f59e0b'};">{status_str.upper()}</td>
        </tr>
    </table>
    
    {feedback_section}
    
    <div style="text-align: center;">
        <a href="{link}" class="btn">Go to Dashboard</a>
    </div>
    """
    
    text = f"Hello {task.assigned_to.name},\n\nTask {task.title} has been {status_str}.\nFeedback: {feedback}\nLink: {link}"
    html = get_base_html_template(subject, body)
    
    _send_email_async(subject, text, html, task.assigned_to.email)
