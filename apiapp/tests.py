
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserProfile


class AuthenticationAndAuthorizationTests(APITestCase):

    def setUp(self):
        self.username = "test_customer"
        self.password = "TestPass!12345"
        self.email = "test_customer@example.com"

    def test_customer_registration(self):
        response = self.client.post(
            "/api/register/",
            {
                "username": self.username,
                "email": self.email,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username=self.username)

        self.assertTrue(user.check_password(self.password))
        self.assertEqual(user.profile.role, "CUSTOMER")

    def test_login_returns_jwt_tokens(self):
        user = User.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password,
        )
        UserProfile.objects.create(user=user, role="CUSTOMER")

        response = self.client.post(
            "/api/login/",
            {
                "username": self.username,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_customer_can_access_customer_dashboard(self):
        user = User.objects.create_user(
            username=self.username,
            password=self.password,
        )
        UserProfile.objects.create(user=user, role="CUSTOMER")

        refresh = RefreshToken.for_user(user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}"
        )

        response = self.client.get("/api/customer-dashboard/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Welcome Customer")

    def test_unauthenticated_user_cannot_access_dashboard(self):
        response = self.client.get("/api/customer-dashboard/")

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_customer_cannot_access_agent_or_admin_dashboard(self):
        user = User.objects.create_user(
            username=self.username,
            password=self.password,
        )
        UserProfile.objects.create(user=user, role="CUSTOMER")

        refresh = RefreshToken.for_user(user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}"
        )

        agent_response = self.client.get("/api/agent-dashboard/")
        admin_response = self.client.get("/api/admin-dashboard/")

        self.assertEqual(
            agent_response.status_code,
            status.HTTP_403_FORBIDDEN
        )
        self.assertEqual(
            admin_response.status_code,
            status.HTTP_403_FORBIDDEN
        )
