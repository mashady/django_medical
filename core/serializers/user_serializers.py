from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from ..models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_approved']

class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    # first_name = serializers.CharField(required=True)
    # last_name = serializers.CharField(required=True)
    role = serializers.ChoiceField(choices=[('doctor', 'Doctor'), ('patient', 'Patient')], required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'role']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)
    