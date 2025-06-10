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
from .serializers import PatientProfileSerializer, PatientProfileUpdateSerializer, DoctorProfileSerializer ,DoctorReviewSerializer
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings

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

            profile_id = None
            if user.role == 'doctor':
                try:
                    profile_id = user.doctor_profile.id
                except DoctorProfile.DoesNotExist:
                    profile_id = None
            elif user.role == 'patient':
                try:
                    profile_id = user.patient_profile.id
                except PatientProfile.DoesNotExist:
                    profile_id = None

            return Response({
                'access': access_token,
                'user': {
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'profile_id': profile_id,
                },
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
        response_data['user_id'] = user.id

        # Add profile_id based on user role
        profile_id = None
        if user.role == 'doctor':
            try:
                profile_id = user.doctor_profile.id
            except DoctorProfile.DoesNotExist:
                profile_id = None
        elif user.role == 'patient':
            try:
                profile_id = user.patient_profile.id
            except PatientProfile.DoesNotExist:
                profile_id = None
        response_data['profile_id'] = profile_id
        return Response(response_data, status=status.HTTP_201_CREATED)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class SpecialtyViewSet(viewsets.ModelViewSet):
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer
    permission_classes = [permissions.AllowAny]
class CombinedUserProfileView(APIView):
    permission_classes = [permissions.AllowAny]

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

                # Support image update via multipart
                if 'image' in request.FILES or 'image' in request.data:
                    profile.image = request.FILES.get("image") or request.data.get("image")
                    profile.save()
                    return Response({
                        "user": user_serializer.data,
                        "profile": DoctorProfileSerializer(profile).data
                    })

                profile_serializer = DoctorProfileSerializer(profile, data=profile_data, partial=True)
                if profile_serializer.is_valid():
                    profile_serializer.save()
                    return Response({
                        "user": user_serializer.data,
                        "profile": profile_serializer.data
                    })
                else:
                    return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except DoctorProfile.DoesNotExist:
                return Response(
                    {"error": "Doctor profile not found"},
                    status=status.HTTP_404_NOT_FOUND
        )

                

        elif user.role == 'patient':
            try:
                profile = PatientProfile.objects.get(user=user)
                profile_serializer = PatientProfileSerializer(profile, data=request.data, partial=True)
                if profile_serializer.is_valid():
                    profile_serializer.save()
                    return Response(profile_serializer.data)
                else:
                    return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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
            doctors = self.queryset.filter(specialty__name__icontains=specialty_name)
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
    queryset = DoctorAvailability.objects.select_related('doctor__user').all()
    serializer_class = DoctorAvailabilitySerializer
    permission_classes = [permissions.AllowAny] 
    
    def get_queryset(self):
        queryset = DoctorAvailability.objects.select_related('doctor__user').all()
        doctor_id = self.request.query_params.get('doctor_id')
        if doctor_id is not None:
            queryset = queryset.filter(doctor_id=doctor_id)
        return queryset

    @action(detail=False, methods=['get'], url_path='doctor/(?P<doctor_id>[^/.]+)')
    def by_doctor(self, request, doctor_id=None):
        try:
            doctor_profile = get_object_or_404(DoctorProfile, id=doctor_id)
            availabilities = DoctorAvailability.objects.filter(
                doctor=doctor_profile
            ).select_related('doctor__user')
            serializer = self.get_serializer(availabilities, many=True)
            return Response({
                'doctor': {
                    'id': doctor_profile.id,
                    'name': doctor_profile.user.get_full_name(),
                },
                'availabilities': serializer.data
            })
        except ValueError:
            return Response(
                {'error': 'Invalid doctor ID'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], url_path='by-day')
    def by_day(self, request):
        day = request.query_params.get('day')
        if not day:
            return Response(
                {'error': 'Day parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        availabilities = self.get_queryset().filter(day_of_week=day)
        serializer = self.get_serializer(availabilities, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='doctors')
    def list_doctors(self, request):
        doctors = DoctorProfile.objects.select_related('user').all()
        doctor_data = [
            {
                'id': doctor.id,
                'name': doctor.user.get_full_name(),
                'username': doctor.user.username,
                'email': doctor.user.email,
            }
            for doctor in doctors
        ]
        return Response(doctor_data)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Create availability entries, replacing existing ones for the same doctor
        """
        try:
            # Extract doctor_id from the first item or from request data
            if isinstance(request.data, list) and len(request.data) > 0:
                doctor_id = request.data[0].get('doctor')
            elif isinstance(request.data, dict):
                doctor_id = request.data.get('doctor_id') or request.data.get('doctor')
            else:
                return Response(
                    {'error': 'Invalid data format'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not doctor_id:
                return Response(
                    {'error': 'Doctor ID is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate that doctor exists
            try:
                doctor_profile = DoctorProfile.objects.get(id=doctor_id)
            except DoctorProfile.DoesNotExist:
                return Response(
                    {'error': f'Doctor with ID {doctor_id} does not exist'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # If data is wrapped in an object, extract the availabilities array
            availability_data = request.data
            if isinstance(request.data, dict) and 'availabilities' in request.data:
                availability_data = request.data['availabilities']
            
            # Validate the data first
            serializer = self.get_serializer(data=availability_data, many=True)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Delete existing availability for this doctor
            DoctorAvailability.objects.filter(doctor_id=doctor_id).delete()
            
            # Create new availability entries one by one to handle unique constraints
            created_availabilities = []
            for item in serializer.validated_data:
                try:
                    # Check if this day already exists for this doctor
                    existing = DoctorAvailability.objects.filter(
                        doctor_id=doctor_id,
                        day_of_week=item['day_of_week']
                    ).first()
                    
                    if existing:
                        # Update existing record
                        existing.start_time = item['start_time']
                        existing.end_time = item['end_time']
                        existing.save()
                        created_availabilities.append(existing)
                    else:
                        # Create new record
                        availability = DoctorAvailability.objects.create(**item)
                        created_availabilities.append(availability)
                        
                except Exception as e:
                    print(f"Error creating availability for {item}: {str(e)}")
                    continue
            
            # Return the created data
            response_serializer = self.get_serializer(created_availabilities, many=True)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'An error occurred: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
        # Auto-assign patient if current user is a patient
        if self.request.user.role == 'patient' and not serializer.validated_data.get('patient'):
            try:
                patient_profile = PatientProfile.objects.get(user=self.request.user)
                serializer.save(patient=patient_profile)
            except PatientProfile.DoesNotExist:
                raise ValidationError("Patient profile not found.")
        else:
            serializer.save()
    
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
    
    @action(detail=True, methods=['patch'], url_path='status')
    def change_status(self, request, pk=None):
        try:
            appointment = self.get_object()
        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        valid_statuses = dict(Appointment.STATUS_CHOICES).keys()

        if new_status not in valid_statuses:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

        appointment.status = new_status
        appointment.save()

        patient_email = appointment.patient.user.email  # adjust if user is accessed differently
        send_mail(
            subject='Appointment Status Updated',
            message=f'Your appointment on {appointment.date} has been updated to "{new_status}".',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[patient_email],
            fail_silently=False
        )
        return Response({'message': f'Appointment status updated to {new_status} and email sent.'})
    @action(detail=True, methods=['put'], url_path='cancel')
    def cancel_appointment(self, request, pk=None):
        appointment = self.get_object()

       
        if appointment.status == 'cancelled':
            return Response({"detail": "Appointment already cancelled."}, status=status.HTTP_400_BAD_REQUEST)

        appointment.status = 'cancelled'
        appointment.save()

        return Response({"detail": "Appointment cancelled successfully."}, status=status.HTTP_200_OK)

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]




class DoctorReviewViewSet(viewsets.ModelViewSet):
    queryset = DoctorReview.objects.all()
    serializer_class = DoctorReviewSerializer

    # def get_permissions(self):
    #     if self.action in ['create', 'update', 'partial_update']:
    #         return [IsAuthenticated()]
        
    
    def perform_create(self, serializer):
        try:
            patient = PatientProfile.objects.get(user=self.request.user)
        except PatientProfile.DoesNotExist:
            raise serializers.ValidationError("Patient profile not found.")
        serializer.save(patient=patient)


    def perform_update(self, serializer):
        try:
            patient = PatientProfile.objects.get(user=self.request.user)
        except PatientProfile.DoesNotExist:
            raise serializers.ValidationError("Patient profile not found.")
        serializer.save(patient=patient)


    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.patient.user != request.user:
            return Response(
                {"detail": "You do not have permission to delete this review."},
                status=status.HTTP_403_FORBIDDEN,
            )

        self.perform_destroy(instance)
        return Response({"detail": "Review deleted successfully."}, status=status.HTTP_204_NO_CONTENT)



    @action(detail=False, methods=['get'], url_path='doctor')
    def by_doctor(self, request):
        """
        Retrieve reviews for a specific doctor
        URL: /reviews/doctor/?doctor=<doctor_id>
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

        reviews = self.queryset.filter(doctor=doctor_id)

        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
    @action(detail=False, methods=['get'], url_path='patient')
    def by_patient(self, request):
        """
        Retrieve reviews for a specific patient
        URL: /reviews/patient/?patient=<patient_id>
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

        reviews = self.queryset.filter(patient=patient_id)

        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
    

    @action(detail=False, methods=['get'], url_path='my-reviews')
    def my_reviews(self, request):
        """
        Retrieve reviews for the current logged-in user
        URL: /reviews/my-reviews/
        """
        user = request.user
        if user.role == 'patient':
            patient = PatientProfile.objects.get(user=user)
            reviews = self.queryset.filter(patient=patient)
        elif user.role == 'doctor':
            doctor = DoctorProfile.objects.get(user=user)
            reviews = self.queryset.filter(doctor=doctor)
        else:
            return Response(
                {"error": "Only doctors and patients can access their reviews"},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
    


