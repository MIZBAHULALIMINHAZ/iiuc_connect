# event/urls.py
from django.urls import path
from .views import EndEventView, EventDetailView, EventDetailViewSet, EventEditView, EventViewSet, EventRegistrationViewSet, EventPaymentViewSet, GuestEventDetailView, GuestEventListView, GuestLoginView, GuestRegisterView

event_list = EventViewSet.as_view({
    "post": "create",
    "get": "list",
})
event_detail = EventDetailViewSet.as_view({"get": "retrieve"})
event_register = EventRegistrationViewSet.as_view({
    "post": "create"
})

event_payment = EventPaymentViewSet.as_view({
    "post": "create"
})

event_payment_verify = EventPaymentViewSet.as_view({
    "put": "update"
})

urlpatterns = [
    path("", event_list, name="event-list"),
    path("<str:pk>/", event_detail, name="event-detail"),
    path("register/", event_register, name="event-register"),
    path("payment/", event_payment, name="event-payment"),
    path("payment/<str:pk>/verify/", event_payment_verify, name="event-payment-verify"),
    path('guests/login/', GuestLoginView.as_view(), name="guest-login"),
    path('guests/register/', GuestRegisterView.as_view(), name="guest-register"),
    path('<str:event_id>/end/', EndEventView.as_view(), name="end-event"),
    path('guests/login/', GuestLoginView.as_view(), name="guest-login"),
    path('guests/register/', GuestRegisterView.as_view(), name="guest-register"),
    path('guests/events/', GuestEventListView.as_view(), name="guest-event-list"),
    path('guests/events/<str:event_id>/', GuestEventDetailView.as_view(), name="guest-event-detail"),
    path('edit/<str:event_id>/', EventEditView.as_view(), name="event-edit"),
]
