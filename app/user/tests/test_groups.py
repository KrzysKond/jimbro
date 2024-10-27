from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Group

# Define the URLs for the group API
GROUPS_URL = reverse('user:group-list')  # List groups endpoint


def leave_group_url(group_id):
    return reverse('user:group-leave-group',
                   args=[group_id])


def join_group_url(group_id):
    """Create and return join group URL"""
    return reverse('user:group-join-group',
                   args=[group_id])


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


def create_group(**params):
    """Create and return a new group."""
    return Group.objects.create(**params)


def group_detail_url(group_id):
    """Create and return group detail URL"""
    return reverse('user:group-detail',
                   args=[group_id])  # Use the correct URL name


class PublicGroupApiTests(TestCase):
    """Test the public features of the group API."""

    def setUp(self):
        self.client = APIClient()

    def test_join_group_requires_authentication(self):
        """Test that authentication is required to join a group."""
        group = create_group(name='Test Group')
        payload = {'name': 'Test Name'}
        res = (self.client
               .post(join_group_url(group.id), payload))
        self.assertEqual(res.status_code,
                         status.HTTP_401_UNAUTHORIZED)


class PrivateGroupApiTests(TestCase):
    """Test API requests that require authentication."""

    def setUp(self):
        self.user = create_user(
            email='test@example.com',
            password='testpass123',
            name='Test Name',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_group(self):
        """Test creating a new group."""
        payload = {'name': 'New Group'}
        res = self.client.post(GROUPS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        group = Group.objects.get(id=res.data['id'])
        self.assertEqual(group.name, payload['name'])

    def test_join_group_success(self):
        """Test joining a group successfully."""
        group = create_group(name='Test Group')
        res = (self.client
               .post(join_group_url(group.id)))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(self.user, group.members.all())

    def test_join_group_already_member(self):
        """Test that a user cannot join a group they are already a member of"""
        group = create_group(name='Test Group')
        group.members.add(self.user)
        res = (self.client
               .post(join_group_url(group.id)))
        self.assertEqual(res.status_code,
                         status.HTTP_409_CONFLICT)
        self.assertIn('User is already a member of this group.',
                      res.data['detail'])

    def test_list_groups(self):
        """Test listing groups."""
        create_group(name='Group 1')
        create_group(name='Group 2')
        res = self.client.get(GROUPS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_update_group(self):
        """Test updating a group."""
        group = create_group(name='Old Name')
        payload = {'name': 'Updated Name'}
        url = group_detail_url(group.id)
        res = self.client.patch(url, payload)
        group.refresh_from_db()
        self.assertEqual(group.name, payload['name'])
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_delete_group(self):
        """Test deleting a group."""
        group = create_group(name='Group to Delete')
        url = group_detail_url(group.id)  # Use the group_detail_url function
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        exists = Group.objects.filter(id=group.id).exists()
        self.assertFalse(exists)

    def test_leave_group_success(self):
        """Test leaving a group successfully."""
        group = create_group(name='Test Group')
        group.members.add(self.user)  # Add the user to the group
        url = leave_group_url(group.id)  # Use the leave_group_url function

        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['detail'], 'User deleted from the group')
        self.assertNotIn(self.user, group.members.all())

    def test_leave_group_not_member(self):
        """Test that a user cannot leave a
         group if they are not a member."""
        group = create_group(name='Test Group')
        url = leave_group_url(group.id)

        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data['detail'], 'User is not a member of a group')
