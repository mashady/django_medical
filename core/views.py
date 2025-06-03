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

class DoctorListAPIView(generics.ListAPIView):
    serializer_class = DoctorProfileSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = DoctorProfile.objects.select_related('user', 'specialty').all()
        specialty_id = self.request.query_params.get('specialty')
        if specialty_id:
            queryset = queryset.filter(specialty_id=specialty_id)
        return queryset

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
    permission_classes = [IsAuthenticated] 

class DoctorProfileByUserIDAPIView(generics.RetrieveAPIView):
    serializer_class = DoctorProfileSerializer
    permission_classes = [IsAuthenticated]

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
