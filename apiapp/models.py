
from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    CUSTOMER = 'CUSTOMER'
    AGENT = 'AGENT'
    ADMIN = 'ADMIN'

    ROLE_CHOICES = [
        (CUSTOMER, 'Customer'),
        (AGENT, 'Agent'),
        (ADMIN, 'Admin'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=CUSTOMER
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Ticket(models.Model):

    CATEGORY_CHOICES = [
        ('TECHNICAL', 'Technical'),
        ('BILLING', 'Billing'),
        ('ACCOUNT', 'Account'),
        ('GENERAL', 'General'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
    ]

    ticket_number = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True
    )

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='customer_tickets'
    )

    agent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets'
    )

    subject = models.CharField(max_length=200)
    description = models.TextField()

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='GENERAL'
    )

    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='MEDIUM'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='OPEN'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    resolved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            super().save(*args, **kwargs)

            prefix = self.category[:4].upper()
            self.ticket_number = f"{prefix}-{self.pk:05d}"

            super().save(update_fields=['ticket_number'])
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.ticket_number or "New Ticket"


# ---------------------------------
# TICKET CONVERSATION / MESSAGES
# ---------------------------------

class TicketMessage(models.Model):

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='messages'
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ticket_messages'
    )

    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message on {self.ticket.ticket_number}"


# ---------------------------------
# FAQ MODULE
# ---------------------------------

class FAQ(models.Model):

    category = models.CharField(
        max_length=20,
        choices=Ticket.CATEGORY_CHOICES,
        default='GENERAL'
    )

    question = models.CharField(max_length=500)

    answer = models.TextField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'question']

    def __str__(self):
        return self.question
