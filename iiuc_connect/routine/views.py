# routine/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from mongoengine.queryset.visitor import Q
from .models import Routine
from .serializers import RoutineSerializer
from course.models import CourseRegistration
from accounts.authentication import JWTAuthentication
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Routine
from notification.utils import create_notification
from notification.utils import send_ws_notification
from rest_framework.exceptions import NotFound
from bson import ObjectId


class RoutineViewSet(viewsets.ModelViewSet):
    serializer_class = RoutineSerializer
    authentication_classes = (JWTAuthentication,)
    def get_object(self):
        pk = self.kwargs.get("pk")

        try:
            obj = Routine.objects.get(id=pk)
        except Routine.DoesNotExist:
            raise NotFound("Routine not found")

        self.check_object_permissions(self.request, obj)
        return obj

    def is_admin(self, user):
        return getattr(user, "role", None) == "admin"

    def is_teacher(self, user):
        return getattr(user, "role", None) == "teacher"

    def get_queryset(self):
        user = self.request.user

        if self.is_admin(user):
            return Routine.objects.all()

        elif self.is_teacher(user):
            return Routine.objects(teacher=user)

        else:
        # Student
            regs = CourseRegistration.objects(student=user, status="confirmed").only('course', 'section')

            if not regs:
                return Routine.objects.none()   # Important: no registration -> no routine

            course_ids = [r.course.id for r in regs]
            sections = [r.section for r in regs]

            return Routine.objects(
                Q(course__in=course_ids) & Q(section__in=sections)
            )


    def create(self, request, *args, **kwargs):
        if not self.is_admin(request.user):
            return Response({"error": "Permission denied"}, status=403)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        routine = serializer.save()

        # Teacher auto-registration
        reg = CourseRegistration.objects(
            student=routine.teacher,
            course=routine.course,
            section=routine.section
        ).first()
        if reg:
            reg.status = "confirmed"
            reg.save()
        else:
            CourseRegistration(
                student=routine.teacher,
                course=routine.course,
                section=routine.section,
                status="confirmed"
            ).save()
        create_notification(
            user=routine.teacher,
            title="Assigned as Teacher",
            message=f"You have been assigned as the teacher for {routine.course.course_code} (Section {routine.section}).",
            notification_type="announcement"
        )
        #send_ws_notification(
            #user_id=routine.teacher.id,
            #title="Assigned as Teacher",
            #message=f"You have been assigned as the teacher for {routine.course.course_code} (Section {routine.section}).",
            #notification_type="course_update"
        #)
        return Response(
            {"message": "Routine created & teacher registered", "routine": serializer.data},
            status=status.HTTP_201_CREATED
        )
        

    def update(self, request, *args, **kwargs):
        routine = self.get_object()
        serializer = self.get_serializer(routine, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        routine = serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        routine = self.get_object()

    # Delete all registrations under this routine
        CourseRegistration.objects(
            course=routine.course,
            section=routine.section
        ).delete()

    # Delete the routine
        routine.delete()

        return Response(
            {"message": "Routine deleted + all related registrations removed"},
            status=status.HTTP_200_OK
        )

