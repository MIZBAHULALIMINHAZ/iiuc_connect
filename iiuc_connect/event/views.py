# event/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from mongoengine.queryset.visitor import Q
from django.utils import timezone
from accounts.authentication import GuestJWTAuthentication

from .models import Event, EventRegistration, EventPayment,GuestUser
from .serializers import (
    EventSerializer, EventRegistrationSerializer,
    EventPaymentSerializer
)
from accounts.models import User
from rest_framework.views import APIView
from django.core.mail import send_mail
from django.conf import settings
from .serializers import GuestUserSerializer
from accounts.authentication import JWTAuthentication
import jwt
from django.utils import timezone
from .utils import delete_guests_for_event
from notification.utils import create_notification
from bson import ObjectId
from mongoengine.errors import ValidationError

class EventViewSet(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]

    # CREATE EVENT
    def create(self, request):
        data = request.data.copy()
        data["creator"] = str(request.user.id)
        serializer = EventSerializer(data=data)
        if serializer.is_valid():
            event = serializer.save()
            return Response(EventSerializer(event).data)
        return Response(serializer.errors, status=400)

    # EVENT LIST
    def list(self, request):
        events = Event.objects(is_active=True)
        data = EventSerializer(events, many=True).data
        return Response(data)


class EventRegistrationViewSet(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]

    # REGISTER
    def create(self, request):
        data = request.data.copy()
        data["user"] = str(request.user.id)

        serializer = EventRegistrationSerializer(data=data)
        if serializer.is_valid():
            reg = serializer.save()
            return Response(EventRegistrationSerializer(reg).data)
        return Response(serializer.errors, status=400)


class EventPaymentViewSet(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]

    # USER SUBMITS PAYMENT
    def create(self, request):
        serializer = EventPaymentSerializer(data=request.data)
        if serializer.is_valid():
            pay = serializer.save()
            return Response(EventPaymentSerializer(pay).data)
        return Response(serializer.errors, status=400)

    # MANAGER VERIFIES PAYMENT
    def update(self, request, pk=None):
        action = request.data.get("action")  # approve / reject
        
        payment = EventPayment.objects.get(id=pk)

        if action == "approve":
            payment.verification_status = "approved"
            payment.verified_by = request.user
            payment.verified_at = timezone.now()
            payment.save()

            reg = payment.registration
            reg.status = "approved"
            reg.save()

            return Response({"message": "Payment approved."})

        elif action == "reject":
            payment.verification_status = "rejected"
            payment.verified_by = request.user
            payment.verified_at = timezone.now()
            payment.save()

            reg = payment.registration
            reg.status = "pending_payment"
            reg.save()

            return Response({"message": "Payment rejected."})

        return Response({"error": "Invalid action"}, status=400)




class GuestLoginView(APIView):
    """
    Guest login using email & password.
    Returns JWT token with multiple events.
    """
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email & password required"}, status=400)

        guest = GuestUser.objects(email=email).first()
        if not guest or not guest.check_password(password):
            return Response({"error": "Invalid credentials"}, status=400)

        payload = {
            "guest_id": str(guest.id),
            "email": guest.email,
            "events": guest.events,  # list of event IDs
            "exp": timezone.now() + timezone.timedelta(hours=24)
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        return Response({
            "token": token,
            "guest": GuestUserSerializer(guest).data
        })





class GuestRegisterView(APIView):
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        email = request.data.get("email")
        name = request.data.get("name")
        password = request.data.get("password")
        event_id = request.data.get("event")  # single event
        login_url = request.data.get("login_url")

        if not email:
            return Response({"error": "Email required"}, status=400)
        
        if  not login_url:
            return Response({"error": "login_url required"}, status=400)
        
        if  not password :
            return Response({"error": "Password required"}, status=400)
        if  not event_id :
            return Response({"error": "Event required"}, status=400)

        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=404)

        # Authorization check
        user_id = str(request.user.id)
        manager_ids = [str(m.id) for m in event.managers]
        if not (user_id == str(event.creator.id) or user_id in manager_ids):
            return Response({"error": "No permission for this event"}, status=403)

        guest = GuestUser.objects(email=email, events=event_id).first()
        if guest:
            return Response({"error": "Guest already registered for this event"}, status=400)

        # Create guest
        guest = GuestUser(email=email, name=name, events=[event_id])
        guest.set_password(password)
        guest.save()

        # Send invitation email
        message_text = f"""
Hello {guest.name},

You have been invited for the event:

Event: {event.title}
Description: {event.description or ""}
Start: {event.start_time.strftime("%Y-%m-%d %H:%M")}
End: {event.end_time.strftime("%Y-%m-%d %H:%M")}
Venue: {event.venue or "TBA"}

Login using your email and password:
Login Link: {login_url}
Email: {guest.email}
Password: {password}

Thank you!
"""
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or settings.EMAIL_HOST_USER
        send_mail(f"Your Event Invitation", message_text, from_email, [guest.email], fail_silently=False)

        return Response({
            "message": "Guest registered successfully and invitation email sent",
            "guest": GuestUserSerializer(guest).data
        })


class EndEventView(APIView):
    """
    Event creator/admin clicks 'End Event' -> triggers guest deletion
    """
    def post(self, request, event_id):
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=404)

        # Only creator or admin can trigger
        user = request.user  # JWT authenticated user
        if not (user.id == str(event.creator.id) or user.role == 'admin'):
            return Response({"error": "Permission denied"}, status=403)

        # Set event inactive
        event.is_active = False
        event.save()

        # Delete guest accounts
        deleted_count = delete_guests_for_event(event.id)

        return Response({
            "message": f"Event ended successfully. {deleted_count} guest(s) deleted."
        })


class GuestEventListView(APIView):
    authentication_classes = [GuestJWTAuthentication]
    """
    Guest sees list of all events they are registered for.
    """
    def get(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return Response({"error": "Authorization header missing"}, status=401)

        token = auth_header.replace("Bearer ", "")
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return Response({"error": "Token expired"}, status=401)
        except jwt.InvalidTokenError:
            return Response({"error": "Invalid token"}, status=401)

        guest_event_ids = payload.get("events", [])
        events = Event.objects(id__in=guest_event_ids, is_active=True)
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data)

class GuestEventDetailView(APIView):
    authentication_classes = [GuestJWTAuthentication]
    """
    Guest sees full details of a single event they are registered for.
    """
    def get(self, request, event_id):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return Response({"error": "Authorization header missing"}, status=401)

        token = auth_header.replace("Bearer ", "")
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return Response({"error": "Token expired"}, status=401)
        except jwt.InvalidTokenError:
            return Response({"error": "Invalid token"}, status=401)

        guest_event_ids = payload.get("events", [])
        if event_id not in guest_event_ids:
            return Response({"error": "Permission denied for this event"}, status=403)

        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=404)

        serializer = EventSerializer(event)
        return Response(serializer.data)


class EventEditView(APIView):
    authentication_classes = [JWTAuthentication]

    def put(self, request, event_id):
        try:
            # Convert string to ObjectId
            event = Event.objects.get(id=ObjectId(event_id))
        except ValidationError:
            return Response({"error": "Invalid event ID"}, status=400)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=404)

        # Permission check
        user_id = str(request.user.id)
        manager_ids = [str(m.id) for m in event.managers]
        if not (user_id == str(event.creator.id) or request.user.role == "admin" or user_id in manager_ids):
            return Response({"error": "No permission to edit this event"}, status=403)

        serializer = EventSerializer(event, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_event = serializer.save()

        # Notify creator
        create_notification(
            user=updated_event.creator,
            title="Event Updated",
            message=f"The event '{updated_event.title}' has been updated.",
            notification_type="announcement"
        )

        # Notify managers
        for manager in updated_event.managers:
            create_notification(
                user=manager,
                title="Event Updated",
                message=f"The event '{updated_event.title}' has been updated.",
                notification_type="announcement"
            )

        # Notify guests
        guest_list = GuestUser.objects(events=updated_event.id)
        for guest in guest_list:
            send_mail(
                subject=f"Event Updated: {updated_event.title}",
                message=f"Dear {guest.name},\n\nThe event '{updated_event.title}' has been updated. Please check the details.\n\nThank you!",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER),
                recipient_list=[guest.email],
                fail_silently=True
            )

        return Response({
            "message": "Event updated successfully. Notifications sent.",
            "event": EventSerializer(updated_event).data
        }, status=200)
