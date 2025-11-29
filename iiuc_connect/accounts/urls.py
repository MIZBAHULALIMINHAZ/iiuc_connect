# accounts/urls.py
from django.urls import path
from accounts.views import DepartmentCreateAPIView, DepartmentListAPIView, InactiveUsersAPIView, RegisterAPIView, LoginAPIView, ResendOTPAPIView, VerifyOTPAPIView, ProfileAPIView,countuserAPIView

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("verify-otp/", VerifyOTPAPIView.as_view(), name="verify-otp"),
    path('resend-otp/', ResendOTPAPIView.as_view(), name='resend-otp'),
    path("me/", ProfileAPIView.as_view(), name="profile"),
    
    path("departments/add/", DepartmentCreateAPIView.as_view(), name="add-department"),
    path("departments/", DepartmentListAPIView.as_view(), name="list-departments"),

    path("users/inactive/", InactiveUsersAPIView.as_view(), name="inactive-users"),
    
    path("total_user/",countuserAPIView.as_view(),name="total_user"),
]
