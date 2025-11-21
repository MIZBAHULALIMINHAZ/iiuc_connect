# accounts/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.utils import timezone as dj_timezone
import cloudinary
from rest_framework import status, permissions
from accounts.serializers import (
    DepartmentListSerializer, RegisterSerializer, LoginSerializer, OTPVerifySerializer,
    ProfileUpdateSerializer, ProfileSerializer
)
from .models import User, Department
from .utils import create_and_send_otp, generate_jwt
from django.conf import settings
import jwt
import datetime
from cloudinary.uploader import upload as cloudinary_upload
from accounts.serializers import DepartmentSerializer, UserActivationSerializer
from rest_framework.permissions import IsAuthenticated
from accounts.authentication import JWTAuthentication
from cloudinary.exceptions import Error as CloudinaryError
from urllib.parse import urlparse

def upload_image(file_obj, folder="iiuc_connect_profiles"):
    try:
        result = cloudinary_upload(file_obj, folder=folder, overwrite=True, resource_type="image")
        url = result.get("secure_url")
        if not url or not isinstance(url, str):
            raise Exception("Invalid URL returned from Cloudinary")
        return url
    except Exception as e:
        raise e

def delete_image(public_id):
    """Delete file from Cloudinary using public_id"""
    try:
        result = cloudinary.uploader.destroy(public_id, invalidate=True)

        # Accept both 'ok' and 'not found'
        if result.get("result") in ["ok", "not found"]:
            return True

        # Only raise error for genuine failures
        raise Exception(f"Failed to delete image: {result}")

    except CloudinaryError as e:
        raise Exception(f"Cloudinary delete error: {str(e)}")

    
from urllib.parse import urlparse

def extract_public_id(url: str) -> str:
    path = urlparse(url).path
    parts = path.split("/")
    if len(parts) < 5:
        return ""
    public_id_with_ext = "/".join(parts[4:])
    return ".".join(public_id_with_ext.split(".")[:-1])


# Register
class RegisterAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        # uniqueness checks
        if User.objects(student_id=data["student_id"]).first():
            return Response({"error": "student_id already exists"}, status=400)
        if User.objects(email=data["email"]).first():
            return Response({"error": "email already exists"}, status=400)
        
        from bson import ObjectId  # যদি ID string আকারে আসে

        department_id = data.get("department")
        department_obj = None
        if department_id:
            try:
                department_obj = Department.objects(id=ObjectId(department_id)).first()
            except Exception:
                return Response({"error": "Invalid department ID"}, status=400)
            if not department_obj:
                return Response({"error": "Department not found"}, status=404)


        email = data["email"]
        if email.endswith("@ugrad.iiuc.ac.bd"):
            is_active =  "yes"
        else:
            is_active = "no"
        user = User(
            student_id=data["student_id"],
            email=data["email"],
            name=data["name"],
            profile_picture="",  # default empty string
            is_active=is_active,
            role=data.get("role", "student"),
            department=department_obj,
        )
        user.set_password(data["password"])

        # handle profile picture file -> upload to cloudinary and store URL
        if "profile_picture" in request.FILES:
            try:
                user.profile_picture = upload_image(request.FILES["profile_picture"])
            except Exception as e:
                return Response({"error": "Image upload failed", "detail": str(e)}, status=500)

        user.save()
        create_and_send_otp(user)
        return Response({"message": "User created. OTP sent to email."}, status=201)


# Login -> returns JWT if verified
class LoginAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        data = serializer.validated_data
        user = User.objects(email=data["email"]).first()
        if not user:
            return Response({"error": "Invalid credentials"}, status=401)

        if not user.check_password(data["password"]):
            try:
                user.otp_count = (user.otp_count or 0) + 1
            except Exception:
                user.otp_count = 1
            user.save()
            return Response({"error": "Invalid credentials"}, status=401)


        if user.is_verified != "yes":
            return Response({"error": "Email not verified. Please verify OTP."}, status=403)
        if user.is_active != "yes":
            return Response({"error": "Email is from outside. wait for admin activation."}, status=401)

        # Build JWT token
        try:
            user.otp_count = 0
        except Exception:
            user.otp_count = 0
        user.save()
        token = generate_jwt(user.id, days=7)
        profile_data = ProfileSerializer(user).data

        return Response({"token": token, "user": profile_data})


# Verify OTP
class VerifyOTPAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        user = User.objects(email=email).first()
        if not user:
            return Response({"error": "User not found"}, status=404)

        if not user.otp or user.otp != otp:
            try:
                user.otp_count = (user.otp_count or 0) + 1
            except Exception:
                user.otp_count = 1
            user.save()
            return Response({"error": "Invalid OTP"}, status=400)

        # check expiry (10 minutes)
        if not user.otp_created_at:
            return Response({"error": "OTP timestamp missing"}, status=400)


        now = timezone.now()
        
        try:
            if timezone.is_naive(user.otp_created_at):
                from django.utils import timezone as tz_util
                user_ts = tz_util.make_aware(user.otp_created_at)
            else:
                user_ts = user.otp_created_at
        except Exception:
            user_ts = user.otp_created_at

        ttl = datetime.timedelta(minutes=10)
        if now > user_ts + ttl:
            return Response({"error": "OTP expired"}, status=400)


        # verified
        user.otp_count = '0'
        user.is_verified = "yes"
        user.otp = None
        user.otp_created_at = None
        user.save()
        return Response({"message": "Email verified successfully"})


# Resend OTP
# Resend OTP with cooldown protection
class ResendOTPAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=400)

        user = User.objects(email=email).first()
        if not user:
            return Response({"error": "User not found"}, status=404)

        if user.is_verified == "yes":
            return Response({"message": "Email already verified."}, status=200)

        # 1-minute cooldown protection
        if user.otp_created_at:
            cooldown = datetime.timedelta(minutes=1)
            now = timezone.now()

            # ensure otp_created_at is aware
            try:
                user_ts = user.otp_created_at
                if timezone.is_naive(user_ts):
                    from django.utils import timezone as tz_util
                    user_ts = tz_util.make_aware(user_ts)
            except Exception:
                user_ts = user.otp_created_at

            delta = (user_ts + cooldown) - now
            remaining = int(delta.total_seconds()) if delta.total_seconds() > 0 else 0
            if remaining > 0:
                return Response({"error": f"Please wait {remaining} seconds before requesting a new OTP."}, status=429)

        try:
            create_and_send_otp(user)
            return Response({"message": "A new OTP has been sent to your email."}, status=200)
        except Exception as e:
            return Response({"error": "Failed to resend OTP", "detail": str(e)}, status=500)


class ProfileAPIView(APIView):
    authentication_classes = (JWTAuthentication,)


    def get(self, request):
        user = request.user

        data = {
            "id": str(user.id),
            "student_id": user.student_id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "department": user.department.code if user.department else None,
            "batch": user.batch,
            "profile_picture": user.profile_picture,
            "is_verified": user.is_verified,
            "is_active": user.is_active
        }
        return Response(data)

    def put(self, request):
        user = request.user
        serializer = ProfileUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        validated = serializer.validated_data
        for field in ["name", "batch"]:
            if field in validated:
                setattr(user, field, validated[field])
                
        if "department" in validated:
            code = validated["department"]
            dept = Department.objects(code=code).first()
            if not dept:
                return Response({"error": "Invalid department code"}, status=400)
            user.department = dept

        if "profile_picture" in request.FILES:
            try:
                if user.profile_picture and len(user.profile_picture) > 10:
                    try:
                        old_id = extract_public_id(user.profile_picture)
                        delete_image(old_id)
                    except Exception:
                        pass
                user.profile_picture = upload_image(request.FILES["profile_picture"])
            except Exception as e:
                return Response({"error": "Image upload failed", "detail": str(e)}, status=500)

        user.save()
        return Response({"message": "Profile updated successfully"})
    
    



# Manager/Admin: Add Department
class DepartmentCreateAPIView(APIView):
    authentication_classes = (JWTAuthentication,)

    def post(self, request):
        # Only admin allowed
        if request.user.role != "admin":
            return Response({"error": "Permission denied"}, status=403)

        serializer = DepartmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data
        if Department.objects(name=data["name"]).first() or Department.objects(code=data["code"]).first():
            return Response({"error": "Department already exists"}, status=400)

        dept = Department(
            name=data["name"],
            code=data["code"],
            is_active="yes"
        )
        dept.save()
        return Response({"message": "Department created successfully"}, status=201)


# Manager/Admin: List inactive users + activate
class InactiveUsersAPIView(APIView):
    authentication_classes = (JWTAuthentication,)

    def get(self, request):
        # Only admin allowed
        if request.user.role != "admin":
            return Response({"error": "Permission denied"}, status=403)

        inactive_users = User.objects(is_active="no")
        serializer = UserActivationSerializer(inactive_users, many=True)
        return Response(serializer.data)

    def put(self, request):
        if request.user.role != "admin":
            return Response({"error": "Permission denied"}, status=403)

        user_id = request.data.get("id")
        user = User.objects(id=user_id).first()
        if not user:
            return Response({"error": "User not found"}, status=404)

        user.is_active = "yes"
        user.save()
        return Response({"message": "User activated successfully"})

# List active departments (all users can access)
class DepartmentListAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        departments = Department.objects(is_active="yes")
        serializer = DepartmentListSerializer(departments, many=True)
        return Response(serializer.data)
