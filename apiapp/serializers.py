
from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers

from .models import (
    UserProfile,
    AgentProfile,
    AgentAvailability,
    Ticket,
    TicketMessage,
    FAQ,
)


# ---------------------------------
# 1. REGISTER SERIALIZER
# ---------------------------------

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                'A user with this email address already exists.'
            )
        return value

    def validate(self, attrs):
        candidate_user = User(
            username=attrs.get('username'),
            email=attrs.get('email')
        )

        try:
            password_validation.validate_password(
                attrs.get('password'),
                user=candidate_user
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError({
                'password': list(exc.messages)
            })

        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )

        UserProfile.objects.create(
            user=user,
            role='CUSTOMER'
        )

        return user


# ---------------------------------
# 2. TICKET SERIALIZER
# ---------------------------------

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = [
            'id',
            'ticket_number',
            'customer',
            'agent',
            'subject',
            'description',
            'category',
            'priority',
            'status',
            'created_at',
            'updated_at',
            'resolved_at',
        ]

        read_only_fields = [
            'id',
            'ticket_number',
            'customer',
            'agent',
            'category',
            'priority',
            'status',
            'created_at',
            'updated_at',
            'resolved_at',
        ]


# ---------------------------------
# 3. PASSWORD RESET REQUEST
# ---------------------------------

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


# ---------------------------------
# 4. PASSWORD RESET CONFIRM
# ---------------------------------

class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()

    new_password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    def validate_new_password(self, value):
        try:
            password_validation.validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))

        return value


# ---------------------------------
# 5. TICKET MESSAGE SERIALIZER
# ---------------------------------

class TicketMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketMessage
        fields = [
            'id',
            'ticket',
            'sender',
            'message',
            'created_at',
        ]

        read_only_fields = [
            'id',
            'ticket',
            'sender',
            'created_at',
        ]


# ---------------------------------
# 6. FAQ SERIALIZER
# ---------------------------------

class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = [
            'id',
            'category',
            'question',
            'answer',
            'is_active',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]


# ---------------------------------
# 7. PHASE 5 - AGENT PROFILE
# ---------------------------------

class AgentProfileSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    email = serializers.EmailField(
        source='user.email',
        read_only=True
    )

    class Meta:
        model = AgentProfile
        fields = [
            'id',
            'username',
            'email',
            'phone_number',
            'specialization',
            'bio',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'id',
            'username',
            'email',
            'created_at',
            'updated_at',
        ]


# ---------------------------------
# 8. PHASE 5 - AGENT AVAILABILITY
# ---------------------------------

class AgentAvailabilitySerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source='agent.username',
        read_only=True
    )

    class Meta:
        model = AgentAvailability
        fields = [
            'id',
            'username',
            'status',
            'updated_at',
        ]

        read_only_fields = [
            'id',
            'username',
            'updated_at',
        ]
