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
    DoctorListAPIView,
    DoctorViewSet
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
router.register(r'doctors', DoctorViewSet, basename='doctor'),

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='custom_login'),
    path('', include(router.urls)),
    # path('doctor/profile/<int:pk>/', DoctorProfileDetailAPIView.as_view(), name='doctor-profile-detail'),
    path('doctor/profile/<int:user_id>/', DoctorProfileByUserIDAPIView.as_view(), name='doctor-profile-detail'),
    path('doctor/profile/', DoctorProfileRetrieveUpdateAPIView.as_view(), name='doctor-profile'),
    path('doctor/profile/create/', DoctorProfileCreateAPIView.as_view(), name='doctor-profile-create'),
    # path('doctors/all/', DoctorListAPIView.as_view(), name='all-doctors'),
    ]