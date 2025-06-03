from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from .models import *
from .serializers import *

from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdminUser, IsDoctor, IsPatientUser

from rest_framework.decorators import action
from django.shortcuts import get_object_or_404


class RegisterUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterUserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        response_data = serializer.data
        response_data['access'] = access_token
        return Response(response_data, status=status.HTTP_201_CREATED)


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
            return [IsDoctor()]
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
    # permission_classes = [IsDoctor]

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
            return [IsDoctor()]
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
        """
        Retrieve appointments for a specific doctor
        URL: /appointments/doctor/?doctor=<doctor_id>
        """
        doctor_id = request.query_params.get('doctor')

        if not doctor_id:
            return Response(
                {"error": "doctor parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Validate that doctor exists
            DoctorProfile.objects.get(id=doctor_id)
        except DoctorProfile.DoesNotExist:
            return Response(
                {"error": "Doctor not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        appointments = self.queryset.filter(doctor=doctor_id)
        serializer = self.get_serializer(appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='patient')
    def by_patient(self, request):
        """
        Retrieve appointments for a specific patient
        URL: /appointments/patient/?patient=<patient_id>
        """
        patient_id = request.query_params.get('patient')

        if not patient_id:
            return Response(
                {"error": "patient parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Validate that patient exists
            PatientProfile.objects.get(id=patient_id)
        except PatientProfile.DoesNotExist:
            return Response(
                {"error": "Patient not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        appointments = self.queryset.filter(patient=patient_id)
        serializer = self.get_serializer(appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='my-appointments')
    def my_appointments(self, request):
        """
        Retrieve appointments for the current logged-in user
        URL: /appointments/my-appointments/
        """
        user = request.user
        
        if user.role == 'doctor':
            try:
                doctor = DoctorProfile.objects.get(user=user)
                appointments = self.queryset.filter(doctor=doctor)
            except DoctorProfile.DoesNotExist:
                return Response(
                    {"error": "Doctor profile not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        elif user.role == 'patient':
            try:
                patient = PatientProfile.objects.get(user=user)
                appointments = self.queryset.filter(patient=patient)
            except PatientProfile.DoesNotExist:
                return Response(
                    {"error": "Patient profile not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response(
                {"error": "Only doctors and patients can access their appointments"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(appointments, many=True)
        return Response(serializer.data)


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
