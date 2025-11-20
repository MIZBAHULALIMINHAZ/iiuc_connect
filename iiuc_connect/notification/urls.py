# notifications/urls.py
from django.urls import path
from .views import NotificationListAPIView, NotificationMarkReadAPIView

urlpatterns = [
    path('', NotificationListAPIView.as_view(), name='notification-list'),
    path('mark-read/', NotificationMarkReadAPIView.as_view(), name='notification-mark-read'),
]
