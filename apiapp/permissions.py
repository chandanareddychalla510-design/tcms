
from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):

    def has_permission(self, request, view):
        user = request.user
        profile = getattr(user, 'profile', None)

        return (
            user.is_authenticated
            and (
                user.is_superuser
                or (
                    profile is not None
                    and profile.role == 'ADMIN'
                )
            )
        )


class IsAgent(BasePermission):

    def has_permission(self, request, view):
        user = request.user
        profile = getattr(user, 'profile', None)

        return (
            user.is_authenticated
            and profile is not None
            and profile.role == 'AGENT'
        )


class IsCustomer(BasePermission):

    def has_permission(self, request, view):
        user = request.user
        profile = getattr(user, 'profile', None)

        return (
            user.is_authenticated
            and profile is not None
            and profile.role == 'CUSTOMER'
        )
