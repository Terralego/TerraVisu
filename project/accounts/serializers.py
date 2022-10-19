from rest_framework import serializers

from project.accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'uuid', 'email', 'is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login', 'groups', 'user_permissions'
        )