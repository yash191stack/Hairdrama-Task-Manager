import uuid
from django.db import models
from users.models import User

class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('accepted', 'Accepted'),
        ('revision_requested', 'Revision Requested'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    product_image_url = models.URLField(blank=True, null=True)
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_tasks'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tasks'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} [{self.status}]"

class GeneratedImage(models.Model):
    IMAGE_TYPE_CHOICES = [
        ('white_background', 'White Background'),
        ('theme', 'Theme-Based Background'),
        ('creative', 'Creative/Artistic Background'),
        ('model', 'Model Wearing Product'),
    ]

    ANGLE_CHOICES = [
        ('front', 'Front'),
        ('side', 'Side'),
        ('close_up', 'Close Up'),
        ('none', 'None'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='generations')
    image_type = models.CharField(max_length=50, choices=IMAGE_TYPE_CHOICES)
    image_url = models.URLField()
    prompt_used = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    angle = models.CharField(max_length=20, choices=ANGLE_CHOICES, default='none')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'generated_images'
        ordering = ['created_at']

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50)
    table_name = models.CharField(max_length=100)
    row_id = models.CharField(max_length=255)
    changes = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']

class Job(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    image_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default='pending')
    image_url = models.URLField(blank=True, null=True)
    error = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'jobs'
        ordering = ['-created_at']