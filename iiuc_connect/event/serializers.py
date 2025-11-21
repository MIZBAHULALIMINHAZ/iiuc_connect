# event/serializers.py
from rest_framework import serializers
from .models import Event, EventRegistration, EventPayment
from accounts.models import User, Department
from accounts.models import User
from django.conf import settings
from django.core.mail import send_mail
import random
import string

# ----------------------------
# Send Email Helper (Reused)
# ----------------------------
def send_event_email(email, title, message):
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or settings.EMAIL_HOST_USER
    send_mail(title, message, from_email, [email], fail_silently=False)

# ----------------------------
# Event Serializer
# ----------------------------
class EventSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    title = serializers.CharField()
    description = serializers.CharField(required=False)
    venue = serializers.CharField(required=False)

    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()

    creator = serializers.CharField(required=False)
    managers = serializers.ListField(child=serializers.CharField(), required=False)

    is_paid = serializers.BooleanField(default=False)
    fee_amount = serializers.FloatField(required=False)
    payment_instructions = serializers.CharField(required=False)

    departments_allowed = serializers.ListField(child=serializers.CharField(), required=False)
    batches_allowed = serializers.JSONField(required=False)

    def create(self, validated_data):
        creator = User.objects.get(id=validated_data["creator"])
        managers = []
        if "managers" in validated_data:
            managers = [User.objects.get(id=m) for m in validated_data["managers"]]

        event = Event(
            title=validated_data["title"],
            description=validated_data.get("description", ""),
            creator=creator,
            managers=managers,
            start_time=validated_data["start_time"],
            end_time=validated_data["end_time"],
            venue=validated_data.get("venue", ""),

            is_paid=validated_data.get("is_paid", False),
            fee_amount=validated_data.get("fee_amount", 0),
            payment_instructions=validated_data.get("payment_instructions", ""),

            departments_allowed=[Department.objects.get(id=d) for d in validated_data.get("departments_allowed", [])],
            batches_allowed=validated_data.get("batches_allowed", {})
        )
        event.save()
        return event
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            # For lists like managers, you may need special handling
            if attr == "managers":
                instance.managers = value
            else:
                setattr(instance, attr, value)
        instance.save()
        return instance

# ----------------------------
# Registration Serializer
# ----------------------------
class EventRegistrationSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    event = serializers.CharField()
    user = serializers.CharField()
    department = serializers.CharField()
    batch = serializers.CharField()

    def create(self, validated_data):
        event = Event.objects.get(id=validated_data["event"])
        user = User.objects.get(id=validated_data["user"])
        department = Department.objects.get(id=validated_data["department"])

        reg = EventRegistration(
            event=event,
            user=user,
            department=department,
            batch=validated_data["batch"],
            status="pending_payment" if event.is_paid else "approved"
        )
        reg.save()

        # notify user
        send_event_email(
            user.email,
            "Registration Received",
            f"Your registration for '{event.title}' has been submitted."
        )

        return reg


# ----------------------------
# Payment Serializer
# ----------------------------
class EventPaymentSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    registration = serializers.CharField()
    amount = serializers.FloatField()
    method = serializers.CharField()
    trx_id = serializers.CharField()
    screenshot = serializers.CharField(required=False)

    def create(self, validated_data):
        reg = EventRegistration.objects.get(id=validated_data["registration"])

        pay = EventPayment(
            registration=reg,
            amount=validated_data["amount"],
            method=validated_data["method"],
            trx_id=validated_data["trx_id"],
            screenshot=validated_data.get("screenshot")
        )
        pay.save()

        # update registration status
        reg.status = "payment_submitted"
        reg.save()

        # notify managers
        for m in reg.event.managers:
            send_event_email(
                m.email,
                "New Payment Submitted",
                f"A new payment was submitted for event '{reg.event.title}'. Please verify."
            )

        return pay


from rest_framework import serializers
from .models import GuestUser

class GuestUserSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    email = serializers.EmailField()
    name = serializers.CharField()
    events = serializers.ListField(child=serializers.CharField())  # <-- changed
    created_at = serializers.DateTimeField(read_only=True)

