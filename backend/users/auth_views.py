from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .auth_service import verify_google_token, verify_github_code, get_or_create_oauth_user
from .serializers import UserSerializer

def generate_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }

def _oauth_login_response(provider, profile_data):
    if not profile_data:
        if provider == 'google':
            hint = 'Check GOOGLE_CLIENT_ID matches Vercel NEXT_PUBLIC_GOOGLE_CLIENT_ID and Google Console origins.'
            return Response(
                {'error': 'Google authentication failed', 'detail': hint},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if provider == 'github':
            return Response(
                {
                    'error': 'GitHub authentication failed',
                    'detail': 'Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET on Railway, and NEXT_PUBLIC_GITHUB_CLIENT_ID on Vercel.',
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response({'error': 'Authentication failed'}, status=status.HTTP_401_UNAUTHORIZED)

    user = get_or_create_oauth_user(provider, profile_data)
    tokens = generate_tokens(user)
    serializer = UserSerializer(user)
    return Response({'user': serializer.data, 'tokens': tokens}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def oauth_callback(request):
    provider = request.data.get('provider')
    credential = request.data.get('credential')
    code = request.data.get('code')

    if not provider or provider not in ['google', 'github']:
        return Response({'error': 'Invalid provider'}, status=status.HTTP_400_BAD_REQUEST)

    profile_data = None
    if provider == 'google':
        token = credential or request.data.get('access_token')
        if not token:
            return Response({'error': 'Token required'}, status=status.HTTP_400_BAD_REQUEST)
        profile_data = verify_google_token(token)
    elif provider == 'github':
        auth_code = code or request.data.get('access_token')
        if not auth_code:
            return Response({'error': 'Code required'}, status=status.HTTP_400_BAD_REQUEST)
        profile_data = verify_github_code(auth_code)

    return _oauth_login_response(provider, profile_data)


@api_view(['POST'])
@permission_classes([AllowAny])
def google_login_legacy(request):
    """Older frontend builds POST /api/users/auth/google/"""
    token = (
        request.data.get('credential')
        or request.data.get('id_token')
        or request.data.get('access_token')
    )
    if not token:
        return Response({'error': 'Token required'}, status=status.HTTP_400_BAD_REQUEST)
    profile_data = verify_google_token(token)
    return _oauth_login_response('google', profile_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_me(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh = request.data.get('refresh')
        if refresh:
            token = RefreshToken(refresh)
            token.blacklist()
        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
    except Exception:
        return Response({'message': 'Logged out'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    refresh = request.data.get('refresh')
    if not refresh:
        return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        token = RefreshToken(refresh)
        return Response({'access': str(token.access_token)})
    except Exception:
        return Response({'error': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)