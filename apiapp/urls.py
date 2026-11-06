
from django.urls import path

from .views import (
    RegisterView,
    LogoutView,
    AdminDashboardView,
    AgentDashboardView,
    CustomerDashboardView,
)

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [

    # Authentication
    path('register/', RegisterView.as_view(), name='register'),

    path('login/', TokenObtainPairView.as_view(), name='login'),

    path('logout/', LogoutView.as_view(), name='logout'),

    path(
        'token/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh'
    ),

    # Authorization
    path(
        'admin-dashboard/',
        AdminDashboardView.as_view(),
        name='admin-dashboard'
    ),

    path(
        'agent-dashboard/',
        AgentDashboardView.as_view(),
        name='agent-dashboard'
    ),

    path(
        'customer-dashboard/',
        CustomerDashboardView.as_view(),
        name='customer-dashboard'
    ),
]
