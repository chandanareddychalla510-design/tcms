
from django.urls import path

from .views import (
    RegisterView,
    GoogleLoginView,
    LogoutView,
    PasswordResetRequestView,
    PasswordResetConfirmView,

    AdminDashboardView,
    AgentDashboardView,
    CustomerDashboardView,

    CustomerTicketCreateView,
    CustomerTicketListView,
    CustomerTicketDetailView,

    AdminTicketListView,
    AdminAssignTicketView,

    AgentTicketListView,
    AgentAcceptTicketView,
    AgentResolveTicketView,

    TicketConversationView,
    FAQListCreateView,
    FAQDetailView,
    AIFAQAnswerView,
    AIAgentReplySuggestionView,
    AIConversationSummaryView,
)

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [

    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('google-login/', GoogleLoginView.as_view(), name='google-login'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Password Reset
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    # Dashboards
    path('admin-dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('agent-dashboard/', AgentDashboardView.as_view(), name='agent-dashboard'),
    path('customer-dashboard/', CustomerDashboardView.as_view(), name='customer-dashboard'),

    # Customer Tickets
    path('tickets/create/', CustomerTicketCreateView.as_view(), name='create-ticket'),
    path('tickets/', CustomerTicketListView.as_view(), name='customer-tickets'),
    path('tickets/<int:pk>/', CustomerTicketDetailView.as_view(), name='customer-ticket-detail'),

    # Admin Ticket Management
    path('admin/tickets/', AdminTicketListView.as_view(), name='admin-tickets'),
    path('admin/tickets/<int:pk>/assign/', AdminAssignTicketView.as_view(), name='assign-ticket'),

    # Agent Ticket Management
    path('agent/tickets/', AgentTicketListView.as_view(), name='agent-tickets'),
    path('agent/tickets/<int:pk>/accept/', AgentAcceptTicketView.as_view(), name='accept-ticket'),
    path('agent/tickets/<int:pk>/resolve/', AgentResolveTicketView.as_view(), name='resolve-ticket'),

    # Ticket Conversation
    path('tickets/<int:pk>/messages/', TicketConversationView.as_view(), name='ticket-conversation'),

    # FAQ APIs
    path('faqs/', FAQListCreateView.as_view(), name='faq-list-create'),
    path('faqs/ask/', AIFAQAnswerView.as_view(), name='ai-faq-answer'),
    path('faqs/<int:pk>/', FAQDetailView.as_view(), name='faq-detail'),

    # AI Agent Reply Suggestion
    path(
        'agent/tickets/<int:pk>/suggest-reply/',
        AIAgentReplySuggestionView.as_view(),
        name='ai-agent-reply-suggestion'
    ),

    # AI Conversation Summary
    path(
        'tickets/<int:pk>/ai-summary/',
        AIConversationSummaryView.as_view(),
        name='ai-conversation-summary'
    ),
]
