from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Basic user info jo frontend ko bhejni hai
    password aur sensitive fields exclude kiye hain
    """
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'avatar', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserListSerializer(serializers.ModelSerializer):
    """
    Task assign karte waqt users ki list dikhane ke liye
    sirf basic info chahiye
    """
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'avatar']