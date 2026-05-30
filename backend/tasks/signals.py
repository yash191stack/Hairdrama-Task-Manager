from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from users.models import User
from .models import Task, GeneratedImage, AuditLog
from core.thread_local import get_current_user

def get_serialized_data(instance):
    try:
        data = model_to_dict(instance)
        # Convert UUIDs and decimals to string so they serialize to JSON smoothly
        return {k: str(v) if hasattr(v, 'hex') or hasattr(v, 'to_eng_string') else v for k, v in data.items()}
    except Exception:
        return {}

@receiver(post_save, sender=User)
@receiver(post_save, sender=Task)
@receiver(post_save, sender=GeneratedImage)
def log_save_action(sender, instance, created, **kwargs):
    # Avoid infinite loop when saving the AuditLog itself
    if sender == AuditLog:
        return
        
    action = 'CREATE' if created else 'UPDATE'
    table_name = sender._meta.db_table
    row_id = str(instance.id)
    user = get_current_user()
    
    changes = {
        'model': sender.__name__,
        'state': get_serialized_data(instance)
    }
    
    AuditLog.objects.create(
        user=user,
        action=action,
        table_name=table_name,
        row_id=row_id,
        changes=changes
    )

@receiver(post_delete, sender=User)
@receiver(post_delete, sender=Task)
@receiver(post_delete, sender=GeneratedImage)
def log_delete_action(sender, instance, **kwargs):
    if sender == AuditLog:
        return
        
    table_name = sender._meta.db_table
    row_id = str(instance.id)
    user = get_current_user()
    
    changes = {
        'model': sender.__name__,
        'state': get_serialized_data(instance)
    }
    
    AuditLog.objects.create(
        user=user,
        action='DELETE',
        table_name=table_name,
        row_id=row_id,
        changes=changes
    )
