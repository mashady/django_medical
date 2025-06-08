from rest_framework import serializers
from ..models import PatientProfile
from .user_serializers import UserSerializer  

class PatientProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = PatientProfile
        fields = ['id', 'user', 'phone_number', 'address' ,'Blood_Type', 'emergency_contact_phone', 'date_of_birth', 'allergies', 'medical_conditions', 'image']


class PatientProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['phone_number', 'address']
