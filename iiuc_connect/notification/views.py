# notifications/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from accounts.authentication import JWTAuthentication
from .models import Notification
from .serializers import NotificationSerializer
from mongoengine.queryset.visitor import Q

# List notifications for logged-in user
class NotificationListAPIView(APIView):
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        notifications = Notification.objects(user=user).order_by('-created_at')
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)


# Mark a notification as read
class NotificationMarkReadAPIView(APIView):
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        notif_id = request.data.get("id")
        if not notif_id:
            return Response({"error": "Notification ID required"}, status=400)

        notif = Notification.objects(id=notif_id, user=request.user).first()
        if not notif:
            return Response({"error": "Notification not found"}, status=404)

        notif.is_read = True
        notif.save()
        return Response({"message": "Notification marked as read"})
