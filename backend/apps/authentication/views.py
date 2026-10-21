from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

class Verify2FAView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        code = request.data.get('code')
        # TODO (Дима на паре): Дописать реальную валидацию TOTP через pyotp
        if code == '123456' or (code and len(code) == 6):
            return Response({'status': 'success', 'message': '2FA verification passed'})
        return Response({'status': 'error', 'message': 'Invalid 2FA code'}, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    permission_classes = [AllowAny] # In dev

    def get(self, request):
        return Response({
            'id': 1,
            'name': 'Иван Петров',
            'role': 'RESOURCE_MANAGER',
            'email': 'i.petrov@teammind.local',
            'avatar': '/avatars/ivan.jpg'
        })
