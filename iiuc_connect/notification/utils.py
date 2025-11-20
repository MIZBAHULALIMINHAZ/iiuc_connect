# notifications/utils.py
from .models import Notification
from accounts.models import User

def create_notification(user: User, title: str, message: str, notification_type='announcement'):
    Notification(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type
    ).save()
