from rest_framework import serializers
from ..models import PatientProfile , DoctorReview
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



class DoctorReviewSerializer(serializers.ModelSerializer):
    patient = serializers.SerializerMethodField()
    class Meta:
        model = DoctorReview
        fields = ['id', 'doctor', 'patient', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'patient', 'created_at']



    def get_patient(self, obj):
        user = obj.patient.user
        return {
            "id": obj.patient.user.id,
            "name": f"{user.first_name} {user.last_name}".strip() or user.username,
            "image": self.context['request'].build_absolute_uri(obj.patient.image.url) if obj.patient.image else None
        }

    

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
    def validate_comment(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Comment is required.")
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Comment must be at least 10 characters long.")
        return value
    
    
