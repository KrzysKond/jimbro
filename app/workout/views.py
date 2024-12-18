# from django.shortcuts import render

# Create your views here.
"""
Views for the workout APIs
"""
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from rest_framework import viewsets, status, generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from core.models import Workout, Comment
from rest_framework.response import Response
from workout import serializers
from user.serializers import UserImageSerializer


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
                    'detail': 'Invalid date format. Use YYYY-MM-DD.'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            query_date = datetime.today().date()

        # Get the user model
        User = get_user_model()
        user_groups = request.user.group_memberships.all()
        group_member_ids = (User.objects
                            .filter(group_memberships__in=user_groups)
                            .values_list('id',
                                         flat=True).distinct())

        # Retrieve workouts for users in the same groups on the specified date
        workouts = (self.get_queryset()
                    .filter(user__in=group_member_ids, date=query_date))

        # If no workouts found, retrieve just user workouts
        if not workouts.exists():
            workouts = (self.get_queryset()
                        .filter(date=query_date, user=request.user))

        if workouts.exists():
            return Response(self._prepare_workout_data(workouts, request),
                            status=status.HTTP_200_OK)

        return Response({
            'detail': 'No workouts found for the given date.'},
            status=status.HTTP_404_NOT_FOUND)

    @action(methods=['GET'], detail=False, url_path='last-week-workouts')
    def get_last_week_workouts(self, request):
        user_id = request.query_params.get('user_id', None)
        today = datetime.today().date()
        start_date = today - timedelta(days=7)

        if user_id:
            try:
                user = get_user_model().objects.get(id=user_id)
            except get_user_model().DoesNotExist:
                return Response({'detail': 'User not found.'},
                                status=status.HTTP_404_NOT_FOUND)
        else:
            user = request.user

        workouts = self.get_queryset().filter(
            user=user,
            date__range=[start_date, today]).order_by('-date')

        if workouts.exists():
            return Response(self._prepare_workout_data(workouts, request),
                            status=status.HTTP_200_OK)

        return Response({'detail':
                        'No workouts found for the user in the last week.'},
                        status=status.HTTP_404_NOT_FOUND)

    def _prepare_workout_data(self, workouts, request):
        """Helper method to prepare combined workout data."""
        workout_serializer = self.get_serializer(workouts, many=True)
        combined_data = []

        for workout, workout_data in zip(workouts, workout_serializer.data):
            workout_data['isLiked'] = request.user in workout.liked_by.all()

            # Serialize and build absolute URL for the workout image
            image_serializer = serializers.WorkoutImageSerializer(workout)
            image_url = image_serializer.data.get('image', None)
            workout_data['image'] = (request
                                     .build_absolute_uri(image_url)) \
                if image_url else None
            # Get user profile picture
            profile_pic_serializer = UserImageSerializer(workout.user)
            profile_picture = (profile_pic_serializer
                               .data
                               .get('profile_picture', None))
            workout_data['profile_picture'] = \
                (request.build_absolute_uri(profile_picture)) \
                if profile_picture else None

            combined_data.append(workout_data)

        return combined_data


class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = serializers.CommentSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_workout(self):
        workout_id = self.kwargs.get('workout_id')
        return Workout.objects.get(id=workout_id)

    def get_queryset(self):
        workout = self.get_workout()
        return Comment.objects.filter(workout=workout).order_by('-created_at')

    def perform_create(self, serializer):
        workout = self.get_workout()
        serializer.save(author=self.request.user, workout=workout)


class CommentDetailView(generics.RetrieveDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = serializers.CommentSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        comment = self.get_object()
        text = "You do not have permission to delete this comment."
        if request.user != comment.author and not request.user.is_staff:
            return Response(
                {'detail': text},
                status=status.HTTP_403_FORBIDDEN)
        return super().delete(request, *args, **kwargs)
