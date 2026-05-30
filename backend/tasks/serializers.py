from rest_framework import serializers
from .models import Task, GeneratedImage, AuditLog
from users.serializers import UserListSerializer

class GeneratedImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = GeneratedImage
        fields = ['id', 'task', 'image_type', 'image_url', 'prompt_used', 'metadata', 'angle', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_image_url(self, obj):
        if not obj.image_url:
            return ""
        url = obj.image_url
        request = self.context.get('request')
        if request:
            host = request.build_absolute_uri('/')[:-1]
            if "/media/generations/" in url:
                filename = url.split("/media/generations/")[-1]
                return f"{host}/media/generations/{filename}"
        
        from django.conf import settings
        backend_url = getattr(settings, 'BACKEND_URL', 'http://localhost:8001')
        if "/media/generations/" in url:
            filename = url.split("/media/generations/")[-1]
            return f"{backend_url}/media/generations/{filename}"
        return url

class TaskSerializer(serializers.ModelSerializer):
    created_by = UserListSerializer(read_only=True)
    assigned_to = UserListSerializer(read_only=True)
    assigned_to_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    generations = GeneratedImageSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status',
            'product_image_url', 'created_by', 'assigned_to',
            'assigned_to_id', 'generations', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'generations']

    def create(self, validated_data):
        assigned_to_id = validated_data.pop('assigned_to_id', None)
        task = Task.objects.create(
            assigned_to_id=assigned_to_id,
            **validated_data
        )
        return task

    def update(self, instance, validated_data):
        assigned_to_id = validated_data.pop('assigned_to_id', None)
        if assigned_to_id is not None:
            instance.assigned_to_id = assigned_to_id
        return super().update(instance, validated_data)

class AuditLogSerializer(serializers.ModelSerializer):
    user = UserListSerializer(read_only=True)
    
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'action', 'table_name', 'row_id', 'changes', 'timestamp']
        read_only_fields = ['id', 'timestamp']