# accounts/models.py
from mongoengine import Document, StringField, EmailField, DateTimeField,IntField
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from django.utils import timezone
from mongoengine import ReferenceField

class Department(Document):
    name = StringField(required=True, unique=True)
    code = StringField(required=True, unique=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    is_active = StringField(choices=['yes', 'no'], default='yes')
    meta = {
        'collection': 'departments',
        'indexes': ['name', 'code']
    }

class User(Document):
    student_id = StringField(required=True, unique=True)       # unique, indexed
    email = EmailField(required=True, unique=True)             # unique, indexed
    name = StringField(required=True)
    password_hash = StringField(required=True)
    created_at = DateTimeField(default=timezone.now)
    otp = StringField()               
    otp_created_at = DateTimeField()  # OTP validity
    is_verified = StringField(choices=['yes','no'], default='no') 
    is_active = StringField(choices=['yes','no'], default='no') # email verified
    role = StringField(choices=['student', 'admin', 'teacher'], default='student')
    department = ReferenceField(Department, required=False)    
    batch = StringField()           
    profile_picture = StringField()  # URL (Cloudinary)
    otp_count = IntField(default=0)
    email_change_count = IntField(default=1)


    meta = {
        'collection': 'users',
        'indexes': ['student_id', 'email', 'role']
    }

    # Password setter
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    # Password checker
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# accounts/models.py
class Stats(Document):
    total_users = IntField(default=0)
    verified_users = IntField(default=0)
    teacher = IntField(default=0)
    student = IntField(default=0)
    department = IntField(default=0)
