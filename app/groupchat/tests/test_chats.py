from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from asgiref.sync import sync_to_async
from core.models import Group, Message
from groupchat.consumers import GroupChatConsumer
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


def create_user(**params):
    """Create and return a new user."""
    return User.objects.create_user(**params)


def create_group(**params):
    """Create and return a new group."""
    return Group.objects.create(**params)


class GroupChatConsumerTestCase(TestCase):
    """Test case for GroupChatConsumer."""

    def setUp(self):
        """Set up the test case environment."""
        self.user = create_user(
            email='user@example.com',
            password='testpassword'
        )
        self.group = create_group(name='Test Group')
        self.group.members.add(self.user)  # Ensure the user is a member

    async def asyncTearDown(self):
        """Clean up after tests."""
        await sync_to_async(self.group.delete)()
        await sync_to_async(self.user.delete)()

    async def test_connect(self):
        """Test WebSocket connection and join group."""
        communicator = WebsocketCommunicator(
            GroupChatConsumer.as_asgi(),
            f"/ws/chat/{self.group.id}/"
        )

        communicator.scope['url_route'] = {
            'kwargs': {'group_id': self.group.id}}

        # Simulate user authentication for connection
        communicator.scope['user'] = self.user
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.disconnect()

    async def test_send_receive_message(self):
        """Test sending and receiving messages via WebSocket."""
        communicator = WebsocketCommunicator(
            GroupChatConsumer.as_asgi(),
            f"/ws/chat/{self.group.id}/"
        )

        communicator.scope['url_route'] = {
            'kwargs': {'group_id': self.group.id}}

        # Simulate user authentication for connection
        communicator.scope['user'] = self.user
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Simulate sending a message
        message_data = {
            'content': 'Hello, World!',
        }
        await communicator.send_json_to(message_data)

        # Check if the group received the message
        response = await communicator.receive_json_from()
        self.assertEqual(response['content'], 'Hello, World!')
        self.assertEqual(response['sender_id'], self.user.id)

        await communicator.disconnect()

    async def test_connect_not_member(self):
        """Test WebSocket connection for
         a user who is not a member of the group."""
        another_user = await sync_to_async(create_user)(
            email='other_user@example.com',
            password='otherpassword'
        )

        communicator = WebsocketCommunicator(
            GroupChatConsumer.as_asgi(),
            f"/ws/chat/{self.group.id}/"
        )

        communicator.scope['url_route'] = {
            'kwargs': {'group_id': self.group.id}}

        # Simulate user authentication for connection
        communicator.scope['user'] = another_user
        connected, _ = await communicator.connect()
        self.assertFalse(connected)

        await communicator.disconnect()


class GroupMessagesViewTestCase(TestCase):
    """Test case for GroupMessagesView API."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='user@example.com', password='testpassword'
        )
        self.group = Group.objects.create(name='Test Group')
        self.group.members.add(self.user)
        self.client.force_authenticate(user=self.user)

    def test_get_group_messages(self):
        """""""Test retrieving group messages."""""""
        message = Message.objects.create(
            group=self.group,
            sender=self.user,
            content='Test Message'
        )

        url = reverse('group_messages', kwargs={'group_id': self.group.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['content'], message.content)

    def test_get_group_messages_not_a_member(self):
        """""""Test retrieving group messages when user is not a member."""""""
        other_user = User.objects.create_user(
            email='other_user@example.com', password='testpassword'
        )
        self.client.force_authenticate(user=other_user)

        url = reverse('group_messages',
                      kwargs={'group_id': self.group.id}) + '?page=1'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class GroupListViewTestCase(TestCase):
    """Test case for GroupListView API."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='user@example.com', password='testpassword'
        )
        self.group = Group.objects.create(
            name='Test Group',
            invite_code='ABC123')
        self.group.members.add(self.user)
        self.client.force_authenticate(user=self.user)

    def test_get_user_groups(self):
        """""""Test retrieving the authenticated user's groups."""""""
        url = reverse('user_chatrooms')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['name'], 'Test Group')
        self.assertEqual(response.data['data'][0]['invite_code'], 'ABC123')

    def test_get_user_groups_not_a_member(self):
        """""""Test retrieving groups when user is not a member."""""""
        other_user = User.objects.create_user(
            email='other_user@example.com', password='testpassword'
        )
        self.client.force_authenticate(user=other_user)

        url = reverse('user_chatrooms')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data'], [])
