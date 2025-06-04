from rest_framework import serializers
from ..models import Appointment, DoctorAvailability
from datetime import datetime

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

    def validate(self, data):
        doctor = data['doctor']
        date = data['date']
        start_time = data['start_time']
        end_time = data['end_time']

        if start_time >= end_time:
            raise serializers.ValidationError("Start time must be before end time.")

 # Check if doctor is available on the selected day
        day_of_week = date.strftime('%A')
        availability = DoctorAvailability.objects.filter(
            doctor=doctor,
            day_of_week=day_of_week
        )

        if not availability.exists():
            raise serializers.ValidationError("Doctor is not available on this day.")

        # Check if time is within any available slot
        is_in_available_slot = any(
            slot.start_time <= start_time and slot.end_time >= end_time
            for slot in availability
        )

        if not is_in_available_slot:
            raise serializers.ValidationError("Selected time is outside doctor's availability.")

        # Check for overlapping appointments
        conflicts = Appointment.objects.filter(
            doctor=doctor,
            date=date,
            start_time__lt=end_time,
            end_time__gt=start_time,
            status__in=['pending', 'confirmed']
        )

        if conflicts.exists():
            raise serializers.ValidationError("This time slot is already booked.")

        # Check for exact duplicate appointment (to override unique_together error)
        if Appointment.objects.filter(
            doctor=doctor,
            date=date,
            start_time=start_time
        ).exists():
            raise serializers.ValidationError("This exact appointment already exists.")

        return data

