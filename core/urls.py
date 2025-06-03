from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    RegisterUserViewSet, 
    UserViewSet,
    # DoctorProfileViewSet, 
    PatientProfileViewSet,
    SpecialtyViewSet, 
    AvailabilityViewSet,
    AppointmentViewSet, 
    NotificationViewSet,
    DoctorProfileDetailAPIView,
    DoctorProfileByUserIDAPIView,
    DoctorListAPIView
)

from .views import (
    CustomLoginView,
    DoctorProfileCreateAPIView,
    DoctorProfileRetrieveUpdateAPIView,
)

router = DefaultRouter()
router.register(r'register', RegisterUserViewSet, basename='register')
router.register(r'users', UserViewSet)
""" router.register(r'doctors', DoctorProfileViewSet) """
router.register(r'patients', PatientProfileViewSet)
router.register(r'specialties', SpecialtyViewSet)
router.register(r'availability', AvailabilityViewSet)
router.register(r'appointments', AppointmentViewSet)
router.register(r'notifications', NotificationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]