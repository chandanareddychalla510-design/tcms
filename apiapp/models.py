
from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):

    ROLE_CHOICES = [
        ('CUSTOMER', 'Customer'),
        ('AGENT', 'Agent'),
        ('ADMIN', 'Admin'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='CUSTOMER'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username
