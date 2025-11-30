from notification.utils import create_notification
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Course, CourseRegistration, Payment
from .serializers import CourseRegistrationSerializer, CourseSerializer, PaymentSerializer
from accounts.models import Department, User
from accounts.views import upload_image, delete_image, extract_public_id
from accounts.authentication import JWTAuthentication
from rest_framework import viewsets, status

class CourseViewSet(viewsets.ViewSet):
    authentication_classes = (JWTAuthentication,)

    def is_admin(self, user):
        return getattr(user, "role", None) in ["admin"]

    #  List Courses 
    def list(self, request):
        courses = Course.objects.all()
        data = []
        for course in courses:
            data.append({
                "id": str(course.id),
                "course_code": course.course_code,
                "department": str(course.department.name) if course.department else None,
                "credit_hour": course.credit_hour
            })
        return Response(data)

    # Create Course 
    def create(self, request):
        if not self.is_admin(request.user):
            return Response({"error": "Permission denied"}, status=403)
        
        serializer = CourseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if Course.objects(course_code=serializer.validated_data["course_code"]).first():
            return Response({"error": "Course code already exists"}, status=400)
        
        course = serializer.save()
        return Response(CourseSerializer(course).data, status=status.HTTP_201_CREATED)

    #  Retrieve Course 
    def retrieve(self, request, pk=None):
        course = Course.objects(id=pk).first()
        if not course:
            return Response({"error": "Course not found"}, status=404)
        return Response(CourseSerializer(course).data)

    #  Update Course 
    def update(self, request, pk=None):
        if not self.is_admin(request.user):
            return Response({"error": "Permission denied"}, status=403)
        course = Course.objects(id=pk).first()
        if not course:
            return Response({"error": "Course not found"}, status=404)
        serializer = CourseSerializer(course, data=request.data)
        serializer.is_valid(raise_exception=True)
        course = serializer.save()
        return Response(CourseSerializer(course).data)

    # Delete Course 
    def destroy(self, request, pk=None):
        if not self.is_admin(request.user):
            return Response({"error": "Permission denied"}, status=403)
        course = Course.objects(id=pk).first()
        if not course:
            return Response({"error": "Course not found"}, status=404)
        course.delete()
        return Response({"message": "Course deleted"})

    # Resources 
    @action(detail=True, methods=["post"])
    def add_resource(self, request, pk=None):
        if not self.is_admin(request.user):
            return Response({"error": "Permission denied"}, status=403)

        course = Course.objects(id=pk).first()
        if not course:
            return Response({"error": "Course not found"}, status=404)

        file_obj = request.FILES.get("file")
        field_name = request.data.get("field")
        VALID_FIELDS = {
        "mid_theory_resources",
        "mid_previous_solves",
        "final_resources",
        "final_previous_solves",
        }

        if not file_obj:
         return Response({"error": "File missing"}, status=400)
        if not field_name:
            return Response({"error": "Field name missing"}, status=400)
        if field_name not in VALID_FIELDS:
            return Response({"error": f"Invalid field name: {field_name}"}, status=400)

        url = upload_image(file_obj, folder="iiuc_connect_courses")
        resources = list(getattr(course, field_name))
        resources.append(url)
        setattr(course, field_name, resources)
        course.save()

        return Response({"message": "Resource added", "url": url})


    @action(detail=True, methods=["put"])
    def update_resource(self, request, pk=None):
        if not self.is_admin(request.user):
            return Response({"error": "Permission denied"}, status=403)

        course = Course.objects(id=pk).first()
        if not course:
            return Response({"error": "Course not found"}, status=404)

        file_obj = request.FILES.get("file")
        field_name = request.data.get("field")
        old_url = request.data.get("old_url")

        VALID_FIELDS = {
        "mid_theory_resources",
        "mid_previous_solves",
        "final_resources",
        "final_previous_solves",
        }

    # Validation
        if not file_obj:
            return Response({"error": "File missing"}, status=400)
        if not field_name:
            return Response({"error": "Field name missing"}, status=400)
        if field_name not in VALID_FIELDS:
            return Response({"error": f"Invalid field name: {field_name}"}, status=400)
        if not old_url:
            return Response({"error": "Old URL missing"}, status=400)

        resources = list(getattr(course, field_name))

        if old_url not in resources:
            return Response({"error": "Old URL not found"}, status=400)

    # Delete old file
        delete_image(extract_public_id(old_url))

    # Upload new file
        new_url = upload_image(file_obj, folder="iiuc_connect_courses")

    # Replace in list
        idx = resources.index(old_url)
        resources[idx] = new_url
        setattr(course, field_name, resources)
        course.save()

    # Notify students with confirmed registration in this course
        confirmed_regs = CourseRegistration.objects(course=course, status="confirmed")
        for reg in confirmed_regs:
            create_notification(
            user=reg.student,
            title=f"Resource updated",
            message=f"A resource in {course.course_code} has been updated.",
            notification_type="announcement"
            )

        return Response({"message": "Resource updated", "url": new_url})



    @action(detail=True, methods=["delete"])
    def delete_resource(self, request, pk=None):
        if not self.is_admin(request.user):
            return Response({"error": "Permission denied"}, status=403)

        course = Course.objects(id=pk).first()
        if not course:
            return Response({"error": "Course not found"}, status=404)

    # Use get() with default None to avoid KeyError / empty data crash
        field_name = request.data.get("field", None)
        target_url = request.data.get("url", None)

        VALID_FIELDS = {
        "mid_theory_resources",
        "mid_previous_solves",
        "final_resources",
        "final_previous_solves",
        }

    # Only return 400 if really missing
        if not field_name or field_name not in VALID_FIELDS:
            return Response({"error": "Invalid or missing field name"}, status=400)
        if not target_url:
            return Response({"error": "URL missing"}, status=400)

        resources = list(getattr(course, field_name))
        if target_url not in resources:
            return Response({"error": "URL not found"}, status=400)

    # Delete the file from cloud
        delete_image(extract_public_id(target_url))

    # Remove URL from list and save
        resources.remove(target_url)
        setattr(course, field_name, resources)
        course.save()

        return Response({"message": "Resource deleted"})




# Course Registration
class CourseRegistrationViewSet(viewsets.ViewSet):
    authentication_classes = (JWTAuthentication,)

    # GET /api/course/registration/ 
    def list(self, request):
        regs = CourseRegistration.objects(student=request.user)
        serializer = CourseRegistrationSerializer(regs, many=True)
        return Response(serializer.data)

    # POST /api/course/registration/
    def create(self, request):
        serializer = CourseRegistrationSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        reg = serializer.save()
        return Response(
            CourseRegistrationSerializer(reg).data,
            status=status.HTTP_201_CREATED
        )

    # PUT /api/course/registration/<pk>/
    def update(self, request, pk=None):
        reg = CourseRegistration.objects(id=pk, student=request.user).first()
        if not reg:
            return Response({"error": "Registration not found"}, status=404)

        serializer = CourseRegistrationSerializer(
            reg, data=request.data, partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        reg = serializer.save()
        return Response(CourseRegistrationSerializer(reg).data)

    # DELETE /api/course/registration/<pk>/ 
    def destroy(self, request, pk=None):
        reg = CourseRegistration.objects(id=pk, student=request.user).first()
        if not reg:
            return Response({"error": "Registration not found"}, status=404)

        reg.delete()
        return Response({"message": "Course registration deleted"}, status=200)
    def retrieve(self, request, pk=None):
        reg = CourseRegistration.objects(id=pk, student=request.user).first()
        if not reg:
            return Response({"error": "Registration not found"}, status=404)
        return Response(CourseRegistrationSerializer(reg).data)


# Payment 
class PaymentViewSet(viewsets.ViewSet):
    authentication_classes = (JWTAuthentication,)

    def list(self, request):
        user = request.user
        data = []

        if getattr(user, "role", None) == "student":
            regs = CourseRegistration.objects(student=user).only('id')
            payments = Payment.objects(registration__in=[r.id for r in regs])

        elif getattr(user, "role", None) == "teacher":
            from routine.models import Routine

            assigned_courses = Routine.objects(teacher=user).only('course')

            regs = CourseRegistration.objects(
                course__in=[r.course.id for r in assigned_courses]
            ).only('id')
            payments = Payment.objects(registration__in=[r.id for r in regs])

        else:
            payments = Payment.objects.all()

        for payment in payments:
            data.append(PaymentSerializer(payment).data)

        return Response(data)

    def create(self, request):
        serializer = PaymentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        return Response(PaymentSerializer(payment).data, status=201)
    def retrieve(self, request, pk=None):
        payment = Payment.objects(id=pk).first()
        if not payment:
            return Response({"error": "Payment not found"}, status=404)
        return Response(PaymentSerializer(payment).data)
    def update(self, request, pk=None):
        if getattr(request.user, "role", None) != "admin":
            return Response({"error": f"Permission denied for role {request.user.role}"}, status=403)

        payment = Payment.objects(id=pk).first()
        if not payment:
            return Response({"error": "Payment not found"}, status=404)
        serializer = PaymentSerializer(payment, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        user = payment.registration.student
        create_notification(
                user=user,
                title=f"Payment Updated",
                message=f"Your payment for the course '{payment.registration.course.course_code}' has been updated.",
                notification_type="announcement"
            )
        
        return Response(PaymentSerializer(payment).data)

    def destroy(self, request, pk=None):
        payment = Payment.objects(id=pk).first()
        if not payment:
            return Response({"error": "Payment not found"}, status=404)
        payment.delete()
        return Response({"message": "Payment deleted"})

#  Course Resources API 
class CourseResourcesAPIView(APIView):
    authentication_classes = (JWTAuthentication,)

    def get(self, request):
        user_role = getattr(request.user, "role", None)
        data = []

        if user_role == "student" :
            confirmed_regs = CourseRegistration.objects(student=request.user, status="confirmed")
            paid_regs = []
            for reg in confirmed_regs:
                payment = Payment.objects(registration=reg, status="completed").first()
                if payment:
                    paid_regs.append(reg)

            for reg in paid_regs:
                course = reg.course
                data.append({
                    "id": str(course.id),
                    "course_code": course.course_code,
                    "department": str(course.department.name) if course.department else None,
                    "credit_hour": course.credit_hour,
                    "mid_theory_resources": course.mid_theory_resources,
                    "mid_previous_solves": course.mid_previous_solves,
                    "final_resources": course.final_resources,
                    "final_previous_solves": course.final_previous_solves
                })


        elif user_role == "teacher":
            confirmed_regs = CourseRegistration.objects(student=request.user, status="confirmed")

            seen = set()
            unique_regs = []

            for reg in confirmed_regs:
                if reg.course.id not in seen:
                    seen.add(reg.course.id)
                    unique_regs.append(reg)

            for reg in unique_regs:
                course = reg.course
                data.append({
            "id": str(course.id),
            "course_code": course.course_code,
            "department": str(course.department.name) if course.department else None,
            "credit_hour": course.credit_hour,
            "mid_theory_resources": course.mid_theory_resources,
            "mid_previous_solves": course.mid_previous_solves,
            "final_resources": course.final_resources,
            "final_previous_solves": course.final_previous_solves
        })


        else:
            return Response({"error": "Permission denied"}, status=403)

        return Response({"courses": data})
    
    


