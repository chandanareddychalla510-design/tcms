from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import UserProfile


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
