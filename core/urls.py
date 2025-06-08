from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static

from django.conf import settings
from django.conf.urls.static import static

from .views import (
    RegisterUserViewSet, 
    UserViewSet,
    PatientProfileViewSet,
    SpecialtyViewSet, 
    AvailabilityViewSet,
    AppointmentViewSet, 
    NotificationViewSet,
    DoctorProfileDetailAPIView,
    DoctorProfileByUserIDAPIView,
    DoctorListAPIView,
    DoctorViewSet,
    CombinedUserProfileView,  
    UpdateUserProfileView,
    DoctorReviewViewSet
)

from .views import (
    CustomLoginView,
    DoctorProfileCreateAPIView,
    DoctorProfileRetrieveUpdateAPIView,
)

router = DefaultRouter()
router.register(r'register', RegisterUserViewSet, basename='register')
router.register(r'users', UserViewSet)
router.register(r'patients', PatientProfileViewSet)
router.register(r'specialties', SpecialtyViewSet)
router.register(r'availability', AvailabilityViewSet)
router.register(r'appointments', AppointmentViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'doctors', DoctorViewSet, basename='doctor'),
router.register(r'reviews', DoctorReviewViewSet, basename='review'),

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='custom_login'),
    path('', include(router.urls)),
    path('doctor/profile/<int:user_id>/', DoctorProfileByUserIDAPIView.as_view(), name='doctor-profile-detail'),
    path('doctor/profile/', DoctorProfileRetrieveUpdateAPIView.as_view(), name='doctor-profile'),
    path('doctor/profile/create/', DoctorProfileCreateAPIView.as_view(), name='doctor-profile-create'),
    
    
    path('user-profile/<int:user_id>/', CombinedUserProfileView.as_view(), name='combined-user-profile'),
    path('update-profile/<int:user_id>/', UpdateUserProfileView.as_view(), name='update-user-profile'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

