
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import RegisterSerializer
from .permissions import IsAdmin, IsAgent, IsCustomer


# Customer Registration
class RegisterView(generics.CreateAPIView):

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


# User Logout
class LogoutView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {'message': 'Logout successful'},
                status=status.HTTP_200_OK
            )

        except TokenError:
            return Response(
                {'error': 'Invalid or expired refresh token'},
                status=status.HTTP_400_BAD_REQUEST
            )


# Admin Dashboard
class AdminDashboardView(APIView):

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        return Response({
            'message': 'Welcome Admin'
        })


# Agent Dashboard
class AgentDashboardView(APIView):

    permission_classes = [IsAuthenticated, IsAgent]

    def get(self, request):
        return Response({
            'message': 'Welcome Agent'
        })


# Customer Dashboard
class CustomerDashboardView(APIView):

    permission_classes = [IsAuthenticated, IsCustomer]

    def get(self, request):
        return Response({
            'message': 'Welcome Customer'
        })
