from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterUserViewSet, UserViewSet,
    DoctorProfileViewSet, PatientProfileViewSet,
    SpecialtyViewSet, AvailabilityViewSet,
    AppointmentViewSet, NotificationViewSet
)

router = DefaultRouter()
router.register(r'register', RegisterUserViewSet, basename='register')
router.register(r'users', UserViewSet)
router.register(r'doctor-profiles', DoctorProfileViewSet)
router.register(r'patient-profiles', PatientProfileViewSet)
router.register(r'specialties', SpecialtyViewSet)
router.register(r'availability', AvailabilityViewSet)
router.register(r'appointments', AppointmentViewSet)
router.register(r'notifications', NotificationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
