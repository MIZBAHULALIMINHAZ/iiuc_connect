# accounts/utils.py
import jwt
import time
import random
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from accounts.models import User


def generate_jwt(user_id, days=7):
    iat = int(time.time())
    exp = iat + days * 24 * 3600
    payload = {"user_id": str(user_id), "iat": iat, "exp": exp}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token


def decode_jwt(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user = User.objects(id=payload.get("user_id")).first()
        return user
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


OTP_TTL_MINUTES = 10


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_via_email(email, otp):
    subject = "Your IIUC Connect OTP"
    message = f"Your OTP code is {otp}. It is valid for {OTP_TTL_MINUTES} minutes."
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or settings.EMAIL_HOST_USER
    send_mail(subject, message, from_email, [email], fail_silently=False)


def create_and_send_otp(user, raise_on_email_error=False):
    otp = generate_otp()
    user.otp = otp
    user.otp_created_at = timezone.now()
    user.is_verified = "no"
    try:
        if user.otp_count is None:
            user.otp_count = 0
    except Exception:
        user.otp_count = 0

    user.save()

    try:
        send_otp_via_email(user.email, otp)
        return True
    except Exception as e:
        if raise_on_email_error:
            raise
        return False
