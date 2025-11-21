
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/accounts/", include("accounts.urls")),
    path("api/course/", include("course.urls")),
    path("api/routine/", include("routine.urls")),
    path("api/notification/", include("notification.urls")),
    path("api/event/", include("event.urls")),
    
]
