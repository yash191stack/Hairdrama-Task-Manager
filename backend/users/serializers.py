from rest_framework import serializers
from .models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import User
from .serializers import UserSerializer, UserListSerializer
from django.urls import path
from . import views

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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    """logged in user ki profile return karo"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """user apna naam ya avatar update kar sake"""
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_users(request):
    """task assign karne ke liye saare users ki list"""
    users = User.objects.exclude(id=request.user.id)
    serializer = UserListSerializer(users, many=True)
    return Response(serializer.data)


urlpatterns = [
    path('profile/', views.get_profile, name='user-profile'),
    path('profile/update/', views.update_profile, name='user-update'),
    path('list/', views.list_users, name='user-list'),
]