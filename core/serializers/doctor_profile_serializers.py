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
    # specialty = serializers.PrimaryKeyRelatedField(queryset=Specialty.objects.all())
    user = UserSerializer(read_only=True)
    specialty = SpecialtySerializer(read_only=True)
    class Meta:
        model = DoctorProfile
        fields = ['id', 'user', 'specialty', 'bio', 'contact_number']

    def validate_contact_number(self, value):
        if not value.startswith('+') or not value[1:].isdigit():
            raise serializers.ValidationError("Contact number must start with '+' followed by digits.")
        if len(value) < 10 or len(value) > 15:
            raise serializers.ValidationError("Contact number must be between 10 and 15 digits long.")
        return value

    def validate_bio(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Bio is required.")
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Bio must be at least 10 characters long.")
        return value

    def validate_specialty(self, value):
        if not Specialty.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Specialty not found.")
        return value

    def validate(self, attrs):
        # You can validate multiple fields together here if needed
        contact_number = attrs.get('contact_number', '')
        if "0000" in contact_number:
            raise serializers.ValidationError("Contact number cannot contain repeated zeros.")
        return attrs