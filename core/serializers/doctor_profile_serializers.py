from rest_framework import serializers
from ..models import Specialty, DoctorProfile

class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ['id', 'name', 'description']

class DoctorProfileSerializer(serializers.ModelSerializer):
    from .user_serializers import UserSerializer
    specialty = SpecialtySerializer()

    class Meta:
        model = DoctorProfile
        fields = ['id', 'user', 'specialty', 'bio', 'contact_number']

class DoctorProfileCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorProfile
        fields = ['specialty', 'bio', 'contact_number']

