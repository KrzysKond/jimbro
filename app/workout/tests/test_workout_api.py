import os
import tempfile

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from core.models import Workout, Group
from rest_framework import status
from rest_framework.test import APIClient
from workout.serializers import WorkoutSerializer
from datetime import date

WORKOUT_URL = reverse('workout:workout-list')
WORKOUT_BY_DATE = reverse('workout:workout-get-by-date')


def workout_detail(workout_id):
    """Create and return an workout detail URL"""
    return reverse('workout:workout-detail', args=[workout_id])


def toggle_like_url(workout_id):
    """Create and return a workout like URL"""
    return reverse('workout:workout-toggle-like', args=[workout_id])


def image_upload_url(workout_id):
    """Create and return an image uplopad URL"""
    return reverse('workout:workout-upload-image', args=[workout_id])


def create_workout(user, given_date=None):
    if given_date is None:
        given_date = date.today()
    workout = Workout.objects.create(user=user, date=given_date)
    return workout


class PublicWorkoutAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(WORKOUT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateWorkoutAPITests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'testpass123',
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_workouts(self):
        """Test retrieving workouts"""
        create_workout(user=self.user)

        res = self.client.get(WORKOUT_URL)

        workout = Workout.objects.filter(user=self.user)
        serializer = WorkoutSerializer(workout, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_workout(self):
        """Test for creating workout"""
        title = 'Jazda z kurczaczkami'
        res = self.client.post(WORKOUT_URL, {
            'title': title,
            'date': date.today()},
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        workout = Workout.objects.get(id=res.data['id'])
        self.assertEqual(workout.date, workout.date)
        self.assertEqual(workout.user, self.user)
        self.assertEqual(workout.title, title)

    def test_retrieve_workouts_by_date(self):
        """Test retrieving workouts
             for the authenticated user by a specific date."""
        group = Group.objects.create(name="TestGroup")
        group.members.add(self.user)
        create_workout(user=self.user, given_date=date(2023, 9, 22))

        create_workout(user=self.user, given_date=date(2023, 9, 23))

        res = self.client.get(WORKOUT_BY_DATE, {'date': '2023-09-22'})

        workouts = Workout.objects.filter(user=self.user, date='2023-09-22')
        serializer = WorkoutSerializer(workouts, many=True)
        for workout in res.data:
            workout.pop('image', None)
            workout.pop('isLiked')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_workouts_by_date_no_groups(self):
        """Test retrieving workouts
             for the authenticated user by a specific date."""
        create_workout(user=self.user, given_date=date(2023, 9, 22))

        create_workout(user=self.user, given_date=date(2023, 9, 23))

        res = self.client.get(WORKOUT_BY_DATE, {'date': '2023-09-22'})

        workouts = Workout.objects.filter(user=self.user, date='2023-09-22')
        serializer = WorkoutSerializer(workouts, many=True)
        for workout in res.data:
            workout.pop('image', None)
            workout.pop('isLiked')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


class ImageUploadTests(TestCase):
    """Tests for the image upload API."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'password123',
        )
        self.client.force_authenticate(self.user)
        self.workout = create_workout(user=self.user)

    def tearDown(self):
        self.workout.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a workout"""
        url = image_upload_url(self.workout.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')

        self.workout.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.workout.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image."""
        url = image_upload_url(self.workout.id)
        payload = {'image': 'notanimage'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_toggle_like_workout(self):
        """Test liking and unliking a workout (toggle behavior)."""
        workout = create_workout(user=self.user)
        url = toggle_like_url(workout.id)

        # First like
        res = self.client.post(url)
        workout.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(workout.fires, 1)
        self.assertEqual(res.data['fires'], 1)

        # Unlike (toggle)
        res = self.client.post(url)
        workout.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(workout.fires, 0)
        self.assertEqual(res.data['fires'], 0)
