
from datetime import date
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Workout, Comment
from workout.serializers import CommentSerializer


def create_workout(user, given_date=None):
    if given_date is None:
        given_date = date.today()
    workout = Workout.objects.create(user=user, date=given_date)
    return workout


def comment_list_url(workout_id):
    """Create and return the comments list URL for a specific workout."""
    return reverse('workout:workout-comment', args=[workout_id])


def comment_detail_url(workout_id, comment_id):
    """Create and return the comment detail URL."""
    return reverse('workout:comment-detail', args=[workout_id, comment_id])


class PublicCommentAPITests(TestCase):
    """Tests for unauthenticated comment API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required to access comments."""
        workout = create_workout(user=get_user_model().objects.create_user(
            'testuser@example.com', 'password123'
        ))
        res = self.client.get(comment_list_url(workout.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateCommentAPITests(TestCase):
    """Tests for authenticated comment API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'testuser@example.com', 'password123'
        )
        self.client.force_authenticate(self.user)
        self.workout = create_workout(user=self.user)

    def test_retrieve_comments(self):
        """Test retrieving comments for a specific workout."""
        res = self.client.get(comment_list_url(self.workout.id))
        comments = Comment.objects.filter(workout=self.workout)
        serializer = CommentSerializer(comments, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_comment(self):
        """Test creating a comment on a workout."""
        text = 'this workout was so tiring!'
        url = comment_list_url(self.workout.id)
        res = self.client.post(url, {
            'text': text
        }, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Comment.objects.filter(
            workout=self.workout,
            author=self.user,
            text=text
        ).exists())

    def test_delete_comment(self):
        """Test deleting a comment."""
        comment = Comment.objects.create(
            workout=self.workout, author=self.user, text="My comment"
        )
        url = comment_detail_url(self.workout.id, comment.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(id=comment.id).exists())

    def test_delete_other_users_comment(self):
        """Test that a user cannot delete someone else's comment."""
        other_user = get_user_model().objects.create_user(
            'other@example.com', 'password123'
        )
        comment = Comment.objects.create(
            workout=self.workout,
            author=other_user,
            text="Other user's comment"
        )
        url = comment_detail_url(self.workout.id, comment.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Comment.objects.filter(id=comment.id).exists())
