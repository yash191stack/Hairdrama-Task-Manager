from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .auth_service import verify_google_token, get_or_create_user
from .serializers import UserSerializer


def generate_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
   
    access_token = request.data.get('access_token')

    if not access_token:
        return Response(
            {'error': 'access_token required hai'},
            status=status.HTTP_400_BAD_REQUEST
        )

    google_data = verify_google_token(access_token)

    if not google_data:
        return Response(
            {'error': 'Invalid Google token'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    user = get_or_create_user(google_data)

    tokens = generate_tokens(user)
    serializer = UserSerializer(user)

    return Response({
        'user': serializer.data,
        'tokens': tokens,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    refresh = request.data.get('refresh')
    if not refresh:
        return Response(
            {'error': 'Refresh token required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        token = RefreshToken(refresh)
        return Response({'access': str(token.access_token)})
    except Exception:
        return Response(
            {'error': 'Invalid refresh token'},
            status=status.HTTP_401_UNAUTHORIZED
        )