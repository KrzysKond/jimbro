import os
import tempfile

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from core.models import Workout
from rest_framework import status
from rest_framework.test import APIClient
from workout.serializers import WorkoutSerializer
from datetime import date

WORKOUT_URL = reverse('workout:workout-list')


def workout_detail(workout_id):
    """Create and return an workout detail URL"""
    return reverse('workout:workout-detail', args=[workout_id])


def image_upload_url(workout_id):
    """Create and return an image uplopad URL"""
    return reverse('workout:workout-upload-image', args=[workout_id])


def create_workout(user):
    workout = Workout.objects.create(user=user, date=date.today())
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
        other_user = get_user_model().objects.create_user(
            'other@example.com',
            'password123',
        )
        create_workout(user=other_user)
        create_workout(user=self.user)

        res = self.client.get(WORKOUT_URL)

        workout = Workout.objects.filter(user=self.user)
        serializer = WorkoutSerializer(workout, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_workout(self):
        """Test for creating workout"""
        title = 'Jazda z kurczaczkami'
        res = self.client.post(WORKOUT_URL,  {
                'title': title,
                'date': date.today()},
                format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        workout = Workout.objects.get(id=res.data['id'])
        self.assertEqual(workout.date, workout.date)
        self.assertEqual(workout.user, self.user)
        self.assertEqual(workout.title, title)


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