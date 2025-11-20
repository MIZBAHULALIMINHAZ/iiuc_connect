# notifications/models.py
from mongoengine import Document, ReferenceField, StringField, BooleanField, DateTimeField
from django.utils import timezone
from accounts.models import User

class Notification(Document):
    user = ReferenceField(User, required=True)
    title = StringField(required=True)
    message = StringField(required=True)
    notification_type = StringField(choices=['routine_change', 'course_update', 'announcement'], default='announcement')
    is_read = BooleanField(default=False)
    created_at = DateTimeField(default=timezone.now)

    meta = {
        'collection': 'notifications',
        'indexes': ['user', 'is_read', 'created_at']
    }
