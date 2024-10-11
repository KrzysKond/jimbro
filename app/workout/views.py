# from django.shortcuts import render

# Create your views here.
"""
Views for the workout APIs
"""
from datetime import datetime

from django.contrib.auth import get_user_model
from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from core.models import Workout
from rest_framework.response import Response
from workout import serializers


class WorkoutViewSet(viewsets.ModelViewSet):
    """View for manage recipe APIs."""
    serializer_class = serializers.WorkoutSerializer
    queryset = Workout.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        """Convert a list of strings to integers"""
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """Retrieve workouts for authenticated user."""
        queryset = self.queryset
        return queryset.filter().order_by('-id').distinct()

    def get_serializer_class(self):
        """Return the serializer class for request"""
        if self.action == 'list':
            return serializers.WorkoutSerializer
        elif self.action == 'upload_image':
            return serializers.WorkoutImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new workout."""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to a workout."""
        workout = self.get_object()
        serializer = self.get_serializer(workout, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST'], detail=True, url_path='toggle_like')
    def toggle_like(self, request, pk=None):
        """Hande liking a workout"""
        workout = self.get_object()
        if request.user not in workout.liked_by.all():
            workout.fires += 1
            workout.liked_by.add(request.user)
        else:
            workout.liked_by.remove(request.user)
            workout.fires -= 1
        workout.save()
        return Response({'fires': workout.fires}, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='get-by-date')
    def get_by_date(self, request, pk=None):
        date_str = request.query_params.get('date', None)

        if date_str:
            try:
                query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'detail': 'Invalid date format. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST)
        else:
            query_date = datetime.today().date()

        # Get the user model
        User = get_user_model()

        # Get groups of the authenticated user
        user_groups = request.user.group_memberships.all()

        # Get IDs of members in those groups
        group_member_ids = User.objects.filter(
            group_memberships__in=user_groups
        ).values_list('id', flat=True).distinct()

        # Retrieve workouts for users in the same groups on the specified date
        workouts = self.get_queryset().filter(
            user__in=group_member_ids, date=query_date
        )
        print(workouts, user_groups, user_groups)

        # retrieve just user workouts if user is not assigned to a group
        if workouts.exists() is False:
            workouts = self.get_queryset().filter(
                date=query_date,
                user=request.user
            )

        if workouts.exists():
            workout_serializer = self.get_serializer(workouts, many=True)
            combined_data = []

            for workout, workout_data in (
                    zip(workouts, workout_serializer.data)):
                if request.user in workout.liked_by.all():
                    workout_data['isLiked'] = True
                else:
                    workout_data['isLiked'] = False
                image_serializer = serializers.WorkoutImageSerializer(workout)
                image_url = image_serializer.data.get('image', None)
                if image_url:
                    image_url = request.build_absolute_uri(image_url)
                workout_data['image'] = image_url
                combined_data.append(workout_data)

            return Response(combined_data, status=status.HTTP_200_OK)

        return Response({'detail': 'No workouts found for the given date.'},
                        status=status.HTTP_404_NOT_FOUND)
