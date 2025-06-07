from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from .models import *
from .serializers import *
from .permissions import IsAdminUser, IsDoctor, IsPatientUser,IsOwnerDoctor
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .serializers import PatientProfileSerializer, PatientProfileUpdateSerializer
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError

class CustomLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        user = authenticate(request, username=username, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response({
                'access': access_token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                }
            }, status=status.HTTP_200_OK)

        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class RegisterUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterUserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Create profile based on user role
        if user.role == 'doctor':
            DoctorProfile.objects.create(user=user)
        elif user.role == 'patient':
            PatientProfile.objects.create(user=user)

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

class CombinedUserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        if not (request.user.is_staff or request.user.id == int(user_id)):
            return Response(
                {"error": "You don't have permission to access this data"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        response_data = {
            'user': UserSerializer(user).data
        }

        if user.role == 'doctor':
            try:
                profile = DoctorProfile.objects.get(user=user)
                response_data['profile'] = DoctorProfileSerializer(profile).data
            except DoctorProfile.DoesNotExist:
                response_data['profile'] = None
        elif user.role == 'patient':
            try:
                profile = PatientProfile.objects.get(user=user)
                response_data['profile'] = PatientProfileSerializer(profile).data
            except PatientProfile.DoesNotExist:
                response_data['profile'] = None

        return Response(response_data)

class UpdateUserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, user_id): 
        if not (request.user.is_staff or request.user.id == int(user_id)):
            return Response(
                {"error": "You don't have permission to update this data"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        user_serializer = UserSerializer(user, data=request.data.get('user', {}), partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        profile_data = request.data.get('profile', {})
        if user.role == 'doctor':
            try:
                profile = DoctorProfile.objects.get(user=user)
                profile_serializer = DoctorProfileSerializer(profile, data=profile_data, partial=True)
            except DoctorProfile.DoesNotExist:
                return Response(
                    {"error": "Doctor profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        elif user.role == 'patient':
            try:
                profile = PatientProfile.objects.get(user=user)
                profile_serializer = PatientProfileSerializer(profile, data=profile_data, partial=True)
            except PatientProfile.DoesNotExist:
                return Response(
                    {"error": "Patient profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response(
                {"user": user_serializer.data},
                status=status.HTTP_200_OK
            )

        if profile_serializer.is_valid():
            profile_serializer.save()
            return Response({
                "user": user_serializer.data,
                "profile": profile_serializer.data
            })
        else:
            return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DoctorListAPIView(generics.ListAPIView):
    queryset = DoctorProfile.objects.select_related('user', 'specialty').all()
    serializer_class = DoctorProfileSerializer
    permission_classes = [permissions.AllowAny]
    
class DoctorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DoctorProfile.objects.select_related('user', 'specialty').all()
    serializer_class = DoctorProfileSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'], url_path='by-specialty')
    def by_specialty(self, request):
        specialty_name = request.query_params.get('specialty')

        if specialty_name:
            doctors = self.queryset.filter(specialty_name_icontains=specialty_name)
        else:
            doctors = self.queryset.all()

        serializer = self.get_serializer(doctors, many=True)
        return Response(serializer.data)

class DoctorProfileCreateAPIView(generics.CreateAPIView):
    queryset = DoctorProfile.objects.all()
    serializer_class = DoctorProfileSerializer
    permission_classes = [IsAuthenticated, IsDoctor]

    def perform_create(self, serializer):
        if DoctorProfile.objects.filter(user=self.request.user).exists():
            raise serializers.ValidationError("Doctor profile already exists.")
        serializer.save(user=self.request.user)

class DoctorProfileDetailAPIView(generics.RetrieveAPIView):
    queryset = DoctorProfile.objects.all()
    serializer_class = DoctorProfileSerializer

class DoctorProfileByUserIDAPIView(generics.RetrieveAPIView):
    serializer_class = DoctorProfileSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        user_id = self.kwargs['user_id']
        return get_object_or_404(DoctorProfile, user__id=user_id)

class DoctorProfileRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = DoctorProfileSerializer
    permission_classes = [IsAuthenticated, IsDoctor, IsOwnerDoctor]

    def get_object(self):
        return self.request.user.doctor_profile

class PatientProfileViewSet(viewsets.ModelViewSet):
    queryset = PatientProfile.objects.select_related('user').all()
    serializer_class = PatientProfileSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsPatientUser()]
        return [IsAuthenticated()]


    @action(detail=False, methods=['post'], url_path='patients')
    def perform_create(self, serializer):
        if PatientProfile.objects.filter(user=self.request.user).exists():
            raise ValidationError("You already have a profile.")
        serializer.save(user=self.request.user)


    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='by-user/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        """
        Retrieve a patient profile by user ID.
        URL: /patients/by-user/<user_id>/
        """
        patient_profile = get_object_or_404(PatientProfile, user__id=user_id)
        serializer = self.get_serializer(patient_profile)
        return Response(serializer.data)

class AvailabilityViewSet(viewsets.ModelViewSet):
    queryset = DoctorAvailability.objects.select_related('doctor').all()
    serializer_class = DoctorAvailabilitySerializer

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
    permission_classes = [permissions.IsAuthenticated]