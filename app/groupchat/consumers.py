from channels.generic.websocket import AsyncWebsocketConsumer
import json
from core.models import Group, Message
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async


User = get_user_model()


class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.room_group_name = f'group_{self.group_id}'

        # Check if the user is a member of the group before allowing connection
        if not await self.is_member(self.group_id, self.scope['user']):
            await self.close()  # Close the connection if not a member
            return

        # Add the connection to the group room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Remove the connection from the group room
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_content = data['content']
        user = self.scope['user']
        sender_id = user.id

    # Check if the sender is a member of the group before saving the message
        if not await self.is_member(
                self.group_id,
                sender_id):
            return  # Do not process message if sender is not a member

        # Save the message to the database
        await self.save_message(
            sender_id,
            self.group_id, message_content)

        # Broadcast the message to the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_content,
                'sender_id': sender_id,
                'sender_name': user.name
            }
        )

    async def chat_message(self, event):
        # Send the message to WebSocket
        await self.send(text_data=json.dumps({
            'content': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name']
        }))

    @database_sync_to_async
    def save_message(self, sender_id, group_id, content):
        try:
            group = Group.objects.get(id=group_id)
            sender = User.objects.get(id=sender_id)
            Message.objects.create(group=group, sender=sender, content=content)
        except Exception as e:
            print(e)

    @sync_to_async
    def is_member(self, group_id, user):
        """Check if the user is a member of the group."""
        try:
            group = Group.objects.get(id=group_id)

            if isinstance(user, int):
                user = User.objects.get(id=user)

            return group.members.filter(id=user.id).exists()
        except Group.DoesNotExist:
            return False
        except User.DoesNotExist:
            return False
