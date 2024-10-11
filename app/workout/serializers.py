"""
Serializer for workout APIs
"""

from rest_framework import serializers
from core.models import Workout


class WorkoutSerializer(serializers.ModelSerializer):
    """Serializer for workouts"""
    username = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = Workout

        fields = ['id', 'title', 'date', 'username', 'liked_by', 'fires']
        read_only_fields = ['id']

    def create(self, validated_data):
        workout = Workout.objects.create(**validated_data)
        return workout


class WorkoutImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images"""

    class Meta:
        model = Workout
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': 'True'}}
