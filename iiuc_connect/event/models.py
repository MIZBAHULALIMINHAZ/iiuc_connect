# event/models.py
from mongoengine import (
    Document, StringField, ReferenceField,
    DateTimeField, FloatField, ListField,
    BooleanField, DictField
)
from django.utils import timezone
from accounts.models import User, Department
import datetime
from mongoengine import Document, StringField, EmailField, DateTimeField, ListField
from werkzeug.security import generate_password_hash, check_password_hash
from django.utils import timezone



class Event(Document):
    title = StringField(required=True)
    description = StringField()
    creator = ReferenceField(User, required=True)
    managers = ListField(ReferenceField(User))  # max 2–3 manually checked

    # Event time
    start_time = DateTimeField(required=True)
    end_time = DateTimeField(required=True)

    # Venue
    venue = StringField()

    # Registration control
    is_paid = BooleanField(default=False)
    fee_amount = FloatField(default=0.0)
    payment_instructions = StringField()

    # Department & Batch filtering
    departments_allowed = ListField(ReferenceField(Department))
    batches_allowed = DictField()  # {"CSE": ["52", "53"], "EEE": ["30"]}

    # Metadata
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    is_active = BooleanField(default=True)

    meta = {
        "collection": "events",
        "indexes": ["title", "creator"]
    }


class EventRegistration(Document):
    event = ReferenceField(Event, required=True)
    user = ReferenceField(User, required=True)
    department = ReferenceField(Department)
    batch = StringField()
    
    status = StringField(
        choices=["pending_payment", "payment_submitted", "approved", "rejected"],
        default="pending_payment"
    )
    created_at = DateTimeField(default=timezone.now)

    meta = {
        "collection": "event_registrations",
        "indexes": ["event", "user", "status"]
    }


class EventPayment(Document):
    registration = ReferenceField(EventRegistration, required=True)
    amount = FloatField(required=True)
    method = StringField(required=True)
    trx_id = StringField(required=True)
    screenshot = StringField() 
    
    submitted_at = DateTimeField(default=timezone.now)

    # Manager verification
    verified_by = ReferenceField(User)
    verified_at = DateTimeField()
    verification_status = StringField(
        choices=["pending", "approved", "rejected"], default="pending"
    )

    meta = {
        "collection": "event_payments",
        "indexes": ["verification_status", "trx_id"]
    }


class GuestUser(Document):
    email = EmailField(required=True, unique=True)
    name = StringField()
    password_hash = StringField(required=True)
    events = ListField(StringField(), default=[])  # Multiple Event IDs
    created_at = DateTimeField(default=timezone.now)

    meta = {
        'collection': 'guest_users',
        'indexes': ['email', 'events']
    }

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
