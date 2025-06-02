from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import *
from .serializers import *

from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdminUser, IsDoctorUser, IsPatientUser



class RegisterUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterUserSerializer
    permission_classes = [permissions.AllowAny]



class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]



class SpecialtyViewSet(viewsets.ModelViewSet):
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer
    permission_classes = [IsAdminUser]


# 
# class DoctorProfileViewSet(viewsets.ModelViewSet):
#     queryset = DoctorProfile.objects.select_related('user', 'specialty').all()
#     serializer_class = DoctorProfileSerializer

#     def get_permissions(self):
#         if self.action in ['create', 'update', 'partial_update', 'destroy']:
#             return [IsDoctorUser()]
#         return [IsAuthenticated()]


# 
# class PatientProfileViewSet(viewsets.ModelViewSet):
#     queryset = PatientProfile.objects.select_related('user').all()
#     serializer_class = PatientProfileSerializer

#     def get_permissions(self):
#         if self.action in ['create', 'update', 'partial_update', 'destroy']:
#             return [IsPatientUser()]
#         return [IsAuthenticated()]


# 
# class AvailabilityViewSet(viewsets.ModelViewSet):
#     queryset = DoctorAvailability.objects.all()
#     serializer_class = DoctorAvailabilitySerializer
#     permission_classes = [IsDoctorUser]


# 
# class AppointmentViewSet(viewsets.ModelViewSet):
#     queryset = Appointment.objects.all()
#     serializer_class = AppointmentSerializer

#     def get_serializer_class(self):
#         if self.action in ['create', 'update']:
#             return AppointmentCreateSerializer
#         return AppointmentSerializer

#     def get_permissions(self):
#         if self.request.user.role == 'admin':
#             return [IsAdminUser()]
#         elif self.request.user.role == 'doctor':
#             return [IsDoctorUser()]
#         elif self.request.user.role == 'patient':
#             return [IsPatientUser()]
#         return [IsAuthenticated()]


#
# class NotificationViewSet(viewsets.ModelViewSet):
#     queryset = Notification.objects.all()
#     serializer_class = NotificationSerializer
#     permission_classes = [IsAuthenticated]
