from rest_framework import serializers
from ..models import Appointment, DoctorAvailability
from datetime import datetime
from django.utils import timezone

class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorAvailability
        fields = ['id', 'day_of_week', 'start_time', 'end_time']

class AppointmentSerializer(serializers.ModelSerializer):
    patient = serializers.SerializerMethodField()
    doctor = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'doctor', 'date', 'start_time',
            'end_time', 'status', 'notes', 'created_at'
        ]

    def get_patient(self, obj):
        return {
            'id': obj.patient.id,
            'name': obj.patient.user.get_full_name(),
        }

    def get_doctor(self, obj):
        return {
            'id': obj.doctor.id,
            'name': obj.doctor.user.get_full_name(),
        }

class AppointmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['doctor', 'date', 'start_time', 'end_time', 'notes']
        # This disables the default unique_together validator
        validators = []
    def validate(self, data):
        doctor = data.get('doctor')
        date = data.get('date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        # Ensure all required fields are present
        if not all([doctor, date, start_time, end_time]):
            raise serializers.ValidationError("Doctor, date, start time, and end time are required.")

        # Ensure the start time is before the end time
        if start_time >= end_time:
            raise serializers.ValidationError("Start time must be before end time.")

        # Get the day of the week (e.g., 'Monday')
        day_of_week = date.strftime('%A')

        # Check if doctor has availability on this day
        availability_slots = DoctorAvailability.objects.filter(
            doctor=doctor,
            day_of_week=day_of_week
        )

        if not availability_slots.exists():
            raise serializers.ValidationError(f"Doctor is not available on {day_of_week}s.")

        # Check if requested time fits within any available slot
        is_valid_time = False
        for slot in availability_slots:
            if slot.start_time <= start_time and slot.end_time >= end_time:
                is_valid_time = True
                break

        if not is_valid_time:
            raise serializers.ValidationError("Requested time is outside the doctor's available hours.")

        # Check for appointment time conflicts
        overlapping_appointments = Appointment.objects.filter(
            doctor=doctor,
            date=date,
            start_time__lt=end_time,
            end_time__gt=start_time,
            status__in=['pending', 'confirmed']
        )

        if overlapping_appointments.exists():
            raise serializers.ValidationError("This time slot is already booked.")

        # Optional: prevent booking in the past
        if date < timezone.now().date():
            raise serializers.ValidationError("Cannot book appointments in the past.")
        
        if Appointment.objects.filter(
            doctor=data['doctor'],
            date=data['date'],
            start_time=data['start_time']
        ).exists():
            raise serializers.ValidationError("This time slot is already taken for this doctor.")

        
        return data
    def create(self, validated_data):
        # Get the logged-in user from request context
        user = self.context['request'].user

        # Get the related patient profile (assuming one-to-one relation)
        try:
            patient_profile = user.patient_profile
        except AttributeError:
            raise serializers.ValidationError("Only patients can create appointments.")

        # Create the appointment with patient injected
        appointment = Appointment.objects.create(
            patient=patient_profile,
            **validated_data
        )

        return appointment

