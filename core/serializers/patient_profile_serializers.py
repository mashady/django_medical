from rest_framework import serializers
from ..models import PatientProfile

class PatientProfileSerializer(serializers.ModelSerializer):
    from .user_serializers import UserSerializer

    class Meta:
        model = PatientProfile
        fields = ['id', 'user', 'phone_number', 'address']

class PatientProfileCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['phone_number', 'address']
