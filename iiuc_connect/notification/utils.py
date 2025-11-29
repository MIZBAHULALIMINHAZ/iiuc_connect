from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification
from accounts.models import User


def create_notification(user: User, title: str, message: str, notification_type='announcement'):
    notif = Notification(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type
    )
    notif.save()
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"notifications_{user.student_id}",
        {
            "type": "send_notification",
            "data": {
                "id": str(notif.id),
                "title": notif.title,
                "message": notif.message,
                "notification_type": notif.notification_type,
                "is_read": notif.is_read,
                "created_at": notif.created_at.isoformat()
            }
        }
    )
    send_ws_notification(user.id, title, message,notification_type)

    # Deployment Ready(Redis)
    # async_to_sync(channel_layer.group_send)(
    #     f"notifications_{user.id}",
    #     {
    #         "type": "send_notification",
    #         "data": {...}
    #     }
    # )

def send_ws_notification(user_id, title, message, notification_type):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"notifications_{user_id}",
        {
            "type": "send_notification",
            "data": {
                "title": title,
                "message": message,
                "notification_type": notification_type
            }
        }
    )
