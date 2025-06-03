from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import *
from .serializers import *

from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdminUser, IsDoctorUser, IsPatientUser

from rest_framework.decorators import action
from django.shortcuts import get_object_or_404


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
    # permission_classes = [IsAdminUser]



class DoctorProfileViewSet(viewsets.ModelViewSet):
    queryset = DoctorProfile.objects.select_related('user', 'specialty').all()
    serializer_class = DoctorProfileSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsDoctorUser()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'], url_path='by-specialty')
    def by_specialty(self, request):
        specialty_name = request.query_params.get('specialty')

        if specialty_name:
            doctors = self.queryset.filter(specialty__name__icontains=specialty_name)
        else:
            doctors = self.queryset.all()

        serializer = self.get_serializer(doctors, many=True)
        return Response(serializer.data)


class PatientProfileViewSet(viewsets.ModelViewSet):
    queryset = PatientProfile.objects.select_related('user').all()
    serializer_class = PatientProfileSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsPatientUser()]
        return [IsAuthenticated()]  



class AvailabilityViewSet(viewsets.ModelViewSet):
    queryset = DoctorAvailability.objects.select_related('doctor').all()
    serializer_class = DoctorAvailabilitySerializer
    # permission_classes = [IsDoctorUser]

    @action(detail=False, methods=['get'], url_path='doctor')
    def by_doctor(self, request):
        doctor_id = request.query_params.get('doctor_id')

        if doctor_id: 
            doctor_profile = get_object_or_404(DoctorProfile, id=doctor_id)
            availabilities = self.queryset.filter(doctor=doctor_id)
        else:
            availabilities = self.queryset.all()

        serializer = self.get_serializer(availabilities, many=True)
        return Response(serializer.data)


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return AppointmentCreateSerializer
        return AppointmentSerializer

    def get_permissions(self):
        if self.request.user.role == 'admin':
            return [IsAdminUser()]
        elif self.request.user.role == 'doctor':
            return [IsDoctorUser()]
        elif self.request.user.role == 'patient':
            return [IsPatientUser()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        try:
            serializer.save()
        except IntegrityError:
            raise ValidationError("This exact appointment time is already taken for this doctor.")
    
    @action(detail=False, methods=['get'], url_path='doctor')
    def by_doctor(self, request):
        doctor_id = request.query_params.get('doctor')

        if doctor_id: 
             appointments = self.queryset.filter(doctor=doctor_id)
        else:
            appointments = self.queryset.all()

        serializer = self.get_serializer(appointments, many=True)
        return Response(serializer.data)


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
