from django.urls import path
from course.views import CourseViewSet, CourseResourcesAPIView, CourseRegistrationViewSet,  PaymentViewSet

urlpatterns = [
    # Course Management
    path("", CourseViewSet.as_view({'get': 'list', 'post': 'create'}), name="course-list-create"),
    path("one/<str:pk>/", CourseViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name="course-detail"),

    # Course Resource Management
    path("<str:pk>/add_resource/", CourseViewSet.as_view({'post': 'add_resource'}), name="course-add-resource"),
    path("<str:pk>/update_resource/", CourseViewSet.as_view({'put': 'update_resource'}), name="course-update-resource"),
    path("<str:pk>/delete_resource/", CourseViewSet.as_view({'delete': 'delete_resource'}), name="course-delete-resource"),

    # List Courses with Resources (student / teacher view)
    path("allcheck/", CourseResourcesAPIView.as_view(), name="course-resources"),

    # Course Registration
    path("register/", CourseRegistrationViewSet.as_view({'post': 'create', 'get': 'list'}), name="course-registration"),
    path("register/<str:pk>/", CourseRegistrationViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name="course-registration-detail"),

    # Payment
    path("payment/", PaymentViewSet.as_view({'post': 'create', 'get': 'list'}), name="payment"),
    path("payment/<str:pk>/", PaymentViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name="payment-detail"),
]