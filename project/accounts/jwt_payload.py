from rest_framework_jwt.utils import jwt_create_payload

from .serializers import UserSerializer


def terra_payload_handler(user):
    """Custom response payload handler.

    This function controlls the custom payload after login or token refresh.
    This data is returned through the web API.
    """
    payload = jwt_create_payload(user)

    user_serializer = UserSerializer(user)
    payload.update({"user": user_serializer.data})
    return payload
