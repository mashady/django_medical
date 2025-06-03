from rest_framework import serializers
from ..models import Specialty, DoctorProfile
from .user_serializers import UserSerializer  

class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ['id', 'name', 'description']

    def validate_name(self, value):
        if self.instance is None and Specialty.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("A specialty with this name already exists.")
        if self.instance and Specialty.objects.exclude(id=self.instance.id).filter(name__iexact=value).exists():
            raise serializers.ValidationError("Another specialty with this name already exists.")
        return value

class DoctorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    specialty = SpecialtySerializer(read_only=True)

    class Meta:
        model = DoctorProfile
        fields = ['id', 'user', 'specialty', 'bio', 'contact_number']

class DoctorProfileCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorProfile
        fields = ['specialty', 'bio', 'contact_number']

    def validate_bio(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Bio must be at least 10 characters long.")
        return value

    def validate_contact_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Contact number must contain only digits.")
        if len(value) < 8:
            raise serializers.ValidationError("Contact number must be at least 8 digits.")
        return value

    def validate_specialty(self, value):
        if not Specialty.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Specialty does not exist.")
        return value

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except Exception as e:
            raise serializers.ValidationError(f"Error creating doctor profile: {str(e)}")

    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except Exception as e:
            raise serializers.ValidationError(f"Error updating doctor profile: {str(e)}")
