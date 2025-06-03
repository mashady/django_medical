# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'register', RegisterUserViewSet, basename='register')
router.register(r'users', UserViewSet)
router.register(r'doctors', DoctorProfileViewSet)
router.register(r'patients', PatientProfileViewSet)
router.register(r'availabilities', AvailabilityViewSet)
router.register(r'appointments', AppointmentViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'specialties', SpecialtyViewSet)

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='custom_login'),
    path('', include(router.urls)),
]
