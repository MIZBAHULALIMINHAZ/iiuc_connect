from rest_framework import serializers
from .models import Routine
from course.models import Course
from accounts.models import User, Department

class RoutineSerializer(serializers.Serializer):
    course = serializers.CharField(required=False)
    teacher = serializers.CharField(required=False)
    department = serializers.CharField(required=False)
    day = serializers.CharField(required=False)
    period = serializers.IntegerField(required=False, min_value=1, max_value=6)
    room_number = serializers.CharField(required=False)
    section = serializers.CharField(required=False)

    def validate(self, data):
        instance = getattr(self, "instance", None)  # Existing instance in update

        # ------------------------
        # 1) Resolve IDs or fallback to instance
        # ------------------------
        course_id = data.get("course") or (str(instance.course.id) if instance else None)
        teacher_id = data.get("teacher") or (str(instance.teacher.id) if instance else None)
        dept_id = data.get("department") or (str(instance.department.id) if instance else None)

        course = Course.objects(id=course_id).first()
        teacher = User.objects(id=teacher_id).first()
        department = Department.objects(id=dept_id).first()

        if not course:
            raise serializers.ValidationError("Invalid course ID")
        if not teacher:
            raise serializers.ValidationError("Invalid teacher ID")
        if not department:
            raise serializers.ValidationError("Invalid department ID")

        # ------------------------
        # 2) Resolve other fields
        # ------------------------
        day = data.get("day") or (instance.day if instance else None)
        period = data.get("period") or (instance.period if instance else None)
        section = data.get("section") or (instance.section if instance else None)
        room = data.get("room_number") or (instance.room_number if instance else None)

        qs = Routine.objects

        # ------------------------
        # 3) Conflict checks (ignore self during update)
        # ------------------------

        # Teacher conflict
        conflict = qs(teacher=teacher, day=day, period=period, section=section)
        if instance:
            conflict = conflict.filter(id__ne=instance.id)
        if conflict.first():
            raise serializers.ValidationError("Teacher already has a routine at this time")

        # Room conflict
        conflict = qs(room_number=room, day=day, period=period)
        if instance:
            conflict = conflict.filter(id__ne=instance.id)
        if conflict.first():
            raise serializers.ValidationError("Room already occupied at this time")

        # Course-section conflict
        conflict = qs(course=course, day=day, period=period, section=section)
        if instance:
            conflict = conflict.filter(id__ne=instance.id)
        if conflict.first():
            raise serializers.ValidationError("Course already scheduled at this time for this section")

        # ------------------------
        # 4) Attach objects and resolved fields
        # ------------------------
        data["course"] = course
        data["teacher"] = teacher
        data["department"] = department
        data["day"] = day
        data["period"] = period
        data["section"] = section
        data["room_number"] = room

        return data

    def create(self, validated_data):
        routine = Routine(**validated_data)
        routine.save()
        return routine

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        return {
            "id": str(instance.id),
            "course": {
                "id": str(instance.course.id),
                "code": instance.course.course_code
            },
            "teacher": {
                "id": str(instance.teacher.id),
                "name": instance.teacher.name
            },
            "department": {
                "id": str(instance.department.id),
                "name": instance.department.name
            },
            "day": instance.day,
            "period": instance.period,
            "room_number": instance.room_number,
            "section": instance.section
        }
