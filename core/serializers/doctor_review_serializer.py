from rest_framework import serializers
from core.models import DoctorReview


class DoctorReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorReview
        fields = ['id', 'doctor', 'patient', 'rating', 'comment', 'created_at']


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
    
    