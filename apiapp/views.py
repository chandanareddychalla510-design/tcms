
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth import password_validation
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.conf import settings

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from rest_framework_simplejwt.tokens import RefreshToken

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from .models import UserProfile, Ticket, TicketMessage, FAQ
from .serializers import (
    RegisterSerializer,
    TicketSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    TicketMessageSerializer,
    FAQSerializer,
)
from .permissions import IsAdmin, IsAgent, IsCustomer
from .ai_services import classify_ticket


# ---------------------------------
# 1. CUSTOMER REGISTRATION
# ---------------------------------

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            return Response({
                "message": "Registration successful",
                "username": user.username,
                "email": user.email,
                "role": user.profile.role,
            }, status=status.HTTP_201_CREATED)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ---------------------------------
# 2. GOOGLE LOGIN
# ---------------------------------

class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        credential = request.data.get("credential")

        if not credential:
            return Response(
                {"error": "Google credential is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        client_id = settings.GOOGLE_OAUTH_CLIENT_ID

        if not client_id:
            return Response(
                {"error": "Google OAuth Client ID is not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            google_user = id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                client_id
            )
        except ValueError:
            return Response(
                {"error": "Invalid Google token"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        email = google_user.get("email")
        email_verified = google_user.get("email_verified", False)

        if not email or not email_verified:
            return Response(
                {"error": "Google email is not verified"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.filter(email__iexact=email).first()

        if user is None:
            username_base = email.split("@")[0]
            username = username_base
            counter = 1

            while User.objects.filter(username=username).exists():
                username = f"{username_base}{counter}"
                counter += 1

            user = User.objects.create_user(
                username=username,
                email=email
            )

        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={"role": "CUSTOMER"}
        )

        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Google login successful",
            "username": user.username,
            "email": user.email,
            "role": profile.role,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_200_OK)


# ---------------------------------
# 3. LOGOUT
# ---------------------------------

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "Logout successful"},
                status=status.HTTP_200_OK
            )

        except Exception:
            return Response(
                {"error": "Invalid or expired refresh token"},
                status=status.HTTP_400_BAD_REQUEST
            )


# ---------------------------------
# 4. PASSWORD RESET REQUEST
# ---------------------------------

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]

            user = User.objects.filter(email__iexact=email).first()

            if user:
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)

                reset_link = (
                    f"Password reset details:\n"
                    f"UID: {uid}\n"
                    f"Token: {token}"
                )

                send_mail(
                    subject="TMS Password Reset",
                    message=reset_link,
                    from_email=None,
                    recipient_list=[user.email],
                    fail_silently=False,
                )

            return Response({
                "message": (
                    "If the email exists, password reset instructions "
                    "have been sent."
                )
            }, status=status.HTTP_200_OK)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ---------------------------------
# 5. PASSWORD RESET CONFIRM
# ---------------------------------

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)

        if serializer.is_valid():
            uid = serializer.validated_data["uid"]
            token = serializer.validated_data["token"]
            new_password = serializer.validated_data["new_password"]

            try:
                user_id = force_str(urlsafe_base64_decode(uid))
                user = User.objects.get(pk=user_id)

            except (
                ValueError,
                TypeError,
                OverflowError,
                User.DoesNotExist
            ):
                return Response(
                    {"error": "Invalid reset details"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not default_token_generator.check_token(user, token):
                return Response(
                    {"error": "Invalid or expired reset token"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                password_validation.validate_password(
                    new_password,
                    user=user
                )
            except DjangoValidationError as exc:
                return Response(
                    {"error": exc.messages},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.set_password(new_password)
            user.save()

            return Response({
                "message": "Password reset successful"
            }, status=status.HTTP_200_OK)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ---------------------------------
# 6. CUSTOMER DASHBOARD
# ---------------------------------

class CustomerDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def get(self, request):
        tickets = Ticket.objects.filter(
            customer=request.user
        ).order_by("-created_at")

        return Response({
            "message": "Customer dashboard",
            "username": request.user.username,
            "total_tickets": tickets.count(),
            "open_tickets": tickets.filter(status="OPEN").count(),
            "resolved_tickets": tickets.filter(status="RESOLVED").count(),
            "tickets": TicketSerializer(tickets, many=True).data,
        })


# ---------------------------------
# 7. AGENT DASHBOARD
# ---------------------------------

class AgentDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsAgent]

    def get(self, request):
        tickets = Ticket.objects.filter(
            agent=request.user
        ).order_by("-created_at")

        return Response({
            "message": "Agent dashboard",
            "username": request.user.username,
            "total_tickets": tickets.count(),
            "assigned_tickets": tickets.filter(status="ASSIGNED").count(),
            "in_progress_tickets": tickets.filter(
                status="IN_PROGRESS"
            ).count(),
            "resolved_tickets": tickets.filter(status="RESOLVED").count(),
            "tickets": TicketSerializer(tickets, many=True).data,
        })


# ---------------------------------
# 8. ADMIN DASHBOARD
# ---------------------------------

class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        tickets = Ticket.objects.all()

        return Response({
            "message": "Admin dashboard",
            "total_users": User.objects.count(),
            "total_customers": UserProfile.objects.filter(
                role="CUSTOMER"
            ).count(),
            "total_agents": UserProfile.objects.filter(
                role="AGENT"
            ).count(),
            "total_tickets": tickets.count(),
            "open_tickets": tickets.filter(status="OPEN").count(),
            "assigned_tickets": tickets.filter(status="ASSIGNED").count(),
            "in_progress_tickets": tickets.filter(
                status="IN_PROGRESS"
            ).count(),
            "resolved_tickets": tickets.filter(
                status="RESOLVED"
            ).count(),
        })


# ---------------------------------
# 9. CUSTOMER CREATE TICKET WITH AI CLASSIFICATION
# ---------------------------------

class CustomerTicketCreateView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def post(self, request):
        serializer = TicketSerializer(data=request.data)

        if serializer.is_valid():
            subject = serializer.validated_data["subject"]
            description = serializer.validated_data["description"]

            ai_status = "success"
            ai_reason = ""

            try:
                # Gemini AI ticket classification
                ai_result = classify_ticket(subject, description)

                category = ai_result["category"]
                priority = ai_result["priority"]
                ai_reason = ai_result.get("reason", "")

            except Exception as e:
                # Print actual Gemini error in terminal
                print("Gemini classification error:", repr(e))

                # Fallback values if AI fails
                category = "GENERAL"
                priority = "MEDIUM"
                ai_status = "unavailable"
                ai_reason = "AI classification could not be completed."

            # Save ticket with AI classification
            ticket = serializer.save(
                customer=request.user,
                category=category,
                priority=priority
            )

            return Response({
                "message": "Ticket created successfully",
                "ai_classification_status": ai_status,
                "ai_reason": ai_reason,
                "ticket": TicketSerializer(ticket).data,
            }, status=status.HTTP_201_CREATED)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

# ---------------------------------
# 10. ADMIN VIEW ALL TICKETS
# ---------------------------------

class AdminTicketListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        tickets = Ticket.objects.all().order_by("-created_at")

        return Response({
            "total_tickets": tickets.count(),
            "tickets": TicketSerializer(tickets, many=True).data,
        })


# ---------------------------------
# 11. ADMIN ASSIGN TICKET TO AGENT
# ---------------------------------

class AdminAssignTicketView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)

        agent_id = request.data.get("agent_id")

        if not agent_id:
            return Response(
                {"error": "agent_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            agent = User.objects.get(
                pk=agent_id,
                profile__role="AGENT"
            )
        except User.DoesNotExist:
            return Response(
                {"error": "Valid agent not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if ticket.status == "RESOLVED":
            return Response(
                {"error": "Resolved ticket cannot be assigned"},
                status=status.HTTP_400_BAD_REQUEST
            )

        ticket.agent = agent
        ticket.status = "ASSIGNED"
        ticket.save()

        return Response({
            "message": "Ticket assigned successfully",
            "ticket": TicketSerializer(ticket).data,
        }, status=status.HTTP_200_OK)


# ---------------------------------
# 12. AGENT VIEW ASSIGNED TICKETS
# ---------------------------------

class AgentTicketListView(APIView):
    permission_classes = [IsAuthenticated, IsAgent]

    def get(self, request):
        tickets = Ticket.objects.filter(
            agent=request.user
        ).order_by("-created_at")

        return Response({
            "total_tickets": tickets.count(),
            "tickets": TicketSerializer(tickets, many=True).data,
        })


# ---------------------------------
# 13. AGENT ACCEPT TICKET
# ---------------------------------

class AgentAcceptTicketView(APIView):
    permission_classes = [IsAuthenticated, IsAgent]

    def post(self, request, pk):
        ticket = get_object_or_404(
            Ticket,
            pk=pk,
            agent=request.user
        )

        if ticket.status != "ASSIGNED":
            return Response(
                {"error": "Only assigned tickets can be accepted"},
                status=status.HTTP_400_BAD_REQUEST
            )

        ticket.status = "IN_PROGRESS"
        ticket.save()

        return Response({
            "message": "Ticket accepted successfully",
            "ticket": TicketSerializer(ticket).data,
        }, status=status.HTTP_200_OK)


# ---------------------------------
# 14. AGENT RESOLVE TICKET
# ---------------------------------

class AgentResolveTicketView(APIView):
    permission_classes = [IsAuthenticated, IsAgent]

    def post(self, request, pk):
        ticket = get_object_or_404(
            Ticket,
            pk=pk,
            agent=request.user
        )

        if ticket.status != "IN_PROGRESS":
            return Response(
                {"error": "Only in-progress tickets can be resolved"},
                status=status.HTTP_400_BAD_REQUEST
            )

        ticket.status = "RESOLVED"
        ticket.resolved_at = timezone.now()
        ticket.save()

        return Response({
            "message": "Ticket resolved successfully",
            "ticket": TicketSerializer(ticket).data,
        }, status=status.HTTP_200_OK)


# ---------------------------------
# 15. CUSTOMER VIEW ALL OWN TICKETS
# ---------------------------------

class CustomerTicketListView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def get(self, request):
        tickets = Ticket.objects.filter(
            customer=request.user
        ).order_by("-created_at")

        return Response({
            "message": "Customer tickets retrieved successfully",
            "total_tickets": tickets.count(),
            "tickets": TicketSerializer(
                tickets,
                many=True
            ).data,
        }, status=status.HTTP_200_OK)


# ---------------------------------
# 16. CUSTOMER VIEW SINGLE TICKET
# ---------------------------------

class CustomerTicketDetailView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def get(self, request, pk):
        ticket = get_object_or_404(
            Ticket,
            pk=pk,
            customer=request.user
        )

        return Response({
            "message": "Ticket details retrieved successfully",
            "ticket": TicketSerializer(ticket).data,
        }, status=status.HTTP_200_OK)


# ---------------------------------
# 17. TICKET CONVERSATION
# ---------------------------------

class TicketConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def get_ticket(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)

        profile = getattr(request.user, "profile", None)

        is_admin = (
            request.user.is_superuser
            or (
                profile is not None
                and profile.role == "ADMIN"
            )
        )

        is_customer = ticket.customer_id == request.user.id
        is_assigned_agent = ticket.agent_id == request.user.id

        if not (is_admin or is_customer or is_assigned_agent):
            return None

        return ticket

    def get(self, request, pk):
        ticket = self.get_ticket(request, pk)

        if ticket is None:
            return Response(
                {"error": "You do not have permission to view this conversation"},
                status=status.HTTP_403_FORBIDDEN
            )

        messages = ticket.messages.select_related(
            "sender"
        ).all()

        serializer = TicketMessageSerializer(
            messages,
            many=True
        )

        return Response({
            "ticket_number": ticket.ticket_number,
            "total_messages": messages.count(),
            "messages": serializer.data,
        }, status=status.HTTP_200_OK)

    def post(self, request, pk):
        ticket = self.get_ticket(request, pk)

        if ticket is None:
            return Response(
                {"error": "You do not have permission to reply to this ticket"},
                status=status.HTTP_403_FORBIDDEN
            )

        if ticket.status == "RESOLVED":
            return Response(
                {"error": "Cannot send messages to a resolved ticket"},
                status=status.HTTP_400_BAD_REQUEST
            )

        message = request.data.get("message")

        if not isinstance(message, str) or not message.strip():
            return Response(
                {"error": "Message cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_message = TicketMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            message=message.strip()
        )

        serializer = TicketMessageSerializer(new_message)

        return Response({
            "message": "Reply added successfully",
            "data": serializer.data,
        }, status=status.HTTP_201_CREATED)



# ---------------------------------
# 18. FAQ LIST AND CREATE
# ---------------------------------

class FAQListCreateView(APIView):

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAdmin()]
        return [AllowAny()]

    def get(self, request):
        faqs = FAQ.objects.filter(is_active=True)

        category = request.query_params.get("category")

        if category:
            valid_categories = [
                choice[0] for choice in Ticket.CATEGORY_CHOICES
            ]

            if category not in valid_categories:
                return Response(
                    {"error": "Invalid FAQ category"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            faqs = faqs.filter(category=category)

        serializer = FAQSerializer(faqs, many=True)

        return Response({
            "total_faqs": faqs.count(),
            "faqs": serializer.data,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = FAQSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response({
                "message": "FAQ created successfully",
                "faq": serializer.data,
            }, status=status.HTTP_201_CREATED)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ---------------------------------
# 19. ADMIN FAQ UPDATE AND DELETE
# ---------------------------------

class FAQDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_object(self, pk):
        return get_object_or_404(FAQ, pk=pk)

    def put(self, request, pk):
        faq = self.get_object(pk)
        serializer = FAQSerializer(faq, data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response({
                "message": "FAQ updated successfully",
                "faq": serializer.data,
            }, status=status.HTTP_200_OK)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, pk):
        faq = self.get_object(pk)
        serializer = FAQSerializer(
            faq,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            return Response({
                "message": "FAQ updated successfully",
                "faq": serializer.data,
            }, status=status.HTTP_200_OK)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, pk):
        faq = self.get_object(pk)
        faq.is_active = False
        faq.save(update_fields=["is_active", "updated_at"])

        return Response(
            {"message": "FAQ deactivated successfully"},
            status=status.HTTP_200_OK
        )
