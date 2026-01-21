# accounts/serializers.py
from rest_framework import serializers

class RegisterSerializer(serializers.Serializer):
    student_id = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    name = serializers.CharField(max_length=200)
    password = serializers.CharField(write_only=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    role = serializers.ChoiceField(choices=['student', 'teacher'], default='student')
    department = serializers.CharField(required=False, allow_null=True)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()

class ProfileUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    name = serializers.CharField(required=False)
    department = serializers.CharField(required=False, allow_null=True)
    batch = serializers.CharField(required=False, allow_null=True)
    profile_picture = serializers.ImageField(required=False)

class ProfileSerializer(serializers.Serializer):
    id = serializers.CharField()
    student_id = serializers.CharField()
    email = serializers.EmailField()
    name = serializers.CharField()
    role = serializers.CharField()
    department = serializers.CharField(allow_null=True)
    batch = serializers.CharField(allow_null=True)
    profile_picture = serializers.CharField(allow_null=True)
    is_verified = serializers.CharField()
    is_active = serializers.CharField()


class DepartmentSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=200)
    code = serializers.CharField(max_length=50)
    is_active = serializers.CharField(read_only=True)

class UserActivationSerializer(serializers.Serializer):
    id = serializers.CharField()
    email = serializers.EmailField()
    student_id = serializers.CharField()
    name = serializers.CharField()
    is_active = serializers.CharField()
    role = serializers.CharField()

class TeacherListSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    email = serializers.EmailField()
    student_id = serializers.CharField()
    department = serializers.CharField(source="department.name", allow_null=True)
    profile_picture = serializers.CharField(allow_null=True)


class DepartmentListSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    code = serializers.CharField()
    is_active = serializers.CharField()

