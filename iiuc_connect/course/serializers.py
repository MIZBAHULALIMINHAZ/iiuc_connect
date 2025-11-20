from rest_framework import serializers
from .models import Course, CourseRegistration, Payment
from accounts.models import Department, User

from rest_framework import serializers
from accounts.models import Department
from .models import Course


class CourseSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    course_code = serializers.CharField()
    department = serializers.CharField(required=True)
    credit_hour = serializers.IntegerField()
    mid_theory_resources = serializers.ListField(child=serializers.CharField(), required=False)
    mid_previous_solves = serializers.ListField(child=serializers.CharField(), required=False)
    final_resources = serializers.ListField(child=serializers.CharField(), required=False)
    final_previous_solves = serializers.ListField(child=serializers.CharField(), required=False)

    def create(self, validated_data):
        dept = validated_data.pop("department", None)
        if dept:
            if isinstance(dept, str):
                dept = Department.objects(id=dept).first()
        course = Course(department=dept, **validated_data)
        course.save()
        return course

    def update(self, instance, validated_data):
        dept = validated_data.pop("department", None)
        if dept:
            if isinstance(dept, str):
                dept = Department.objects(id=dept).first()
            instance.department = dept

        # ⛔ These lists must NOT be overwritten
        skip_fields = [
            "mid_theory_resources",
            "mid_previous_solves",
            "final_resources",
            "final_previous_solves"
        ]

        for key, value in validated_data.items():
            if key not in skip_fields:
                setattr(instance, key, value)

        instance.save()
        return instance

    def to_representation(self, instance):
        return {
            "id": str(instance.id),
            "course_code": instance.course_code,
            "department": {
                "id": str(instance.department.id),
                "name": instance.department.name,
            } if instance.department else None,
            "credit_hour": instance.credit_hour,
            "mid_theory_resources": instance.mid_theory_resources or [],
            "mid_previous_solves": instance.mid_previous_solves or [],
            "final_resources": instance.final_resources or [],
            "final_previous_solves": instance.final_previous_solves or [],
        }



from rest_framework import serializers
from .models import CourseRegistration, Course, Payment
from accounts.models import User

class CourseRegistrationSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    student = serializers.SerializerMethodField()
    course = serializers.SerializerMethodField()
    section = serializers.CharField()
    status = serializers.CharField(read_only=True)

    def get_id(self, obj):
        return str(obj.id)

    def get_student(self, obj):
        return str(obj.student.id)

    def get_course(self, obj):
        return str(obj.course.id)
    
    def create(self, validated_data):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context missing")

        # ✅ student সবসময় লগইন করা ইউজার থেকে নেওয়া হবে
        student = request.user  

        course_id = validated_data.get('course') or request.data.get('course')
        section = validated_data.get('section')

        course = Course.objects(id=course_id).first()

        if not course:
            raise serializers.ValidationError("Invalid course")

        # Prevent duplicate registration
        existing = CourseRegistration.objects(student=student, course=course, section=section).first()
        if existing:
            return existing

        reg = CourseRegistration(student=student, course=course, section=section, status="pending")
        reg.save()
        return reg



from rest_framework import serializers
from .models import Payment, CourseRegistration

class PaymentSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    registration = serializers.CharField()
    amount = serializers.FloatField()
    method = serializers.CharField()
    status = serializers.CharField(read_only=True)
    transaction_id = serializers.CharField()

    def get_id(self, obj):
        return str(obj.id)

    def create(self, validated_data):
        registration_id = validated_data.get('registration')
        reg = CourseRegistration.objects(id=registration_id).first()
        if not reg:
            raise serializers.ValidationError("Invalid registration")

        payment = Payment(
            registration=reg,
            amount=validated_data.get('amount'),
            method=validated_data.get('method'),
            transaction_id=validated_data.get('transaction_id'),
            status="completed"
        )
        payment.save()

        # Update registration status
        reg.status = "confirmed"
        reg.save()

        return payment

