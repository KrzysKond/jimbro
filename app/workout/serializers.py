"""
Serializer for workout APIs
"""

from rest_framework import serializers
from core.models import Workout, Comment


class WorkoutSerializer(serializers.ModelSerializer):
    """Serializer for workouts"""
    username = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = Workout

        fields = ['id', 'title', 'date',
                  'username', 'liked_by',
                  'fires', 'comments_count']
        read_only_fields = ['id', 'comments_count']

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


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    workout = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'workout', 'author', 'text', 'created_at']
        read_only_fields = ['id', 'author', 'created_at']
