from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from core.models import Group, Message

User = get_user_model()


class GroupMessagesView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, group_id):
        """Retrieve all messages for a specific group,
            ensuring user is a member."""
        group = Group.objects.filter(id=group_id).first()

        if group is None:
            return Response({"status": False, "message": "Group not found."},
                            status=status.HTTP_404_NOT_FOUND)

        if not group.members.filter(id=request.user.id).exists():
            return Response({
                "status": False,
                "message": "You are not a member of this group."},
                status=status.HTTP_403_FORBIDDEN)

        messages = list(Message.objects
                        .filter(group__id=group_id).order_by('timestamp')
                        .values(
                            'id',
                            'sender__id',
                            'sender__name',
                            'content',
                            'timestamp'))

        transformed_messages = []
        for msg in messages:
            transformed_msg = {
                '-id': msg['id'],
                'sender_id': msg['sender__id'],
                'sender_name': msg['sender__name'],
                'content': msg['content'],
                'timestamp': msg['timestamp'],
            }
            transformed_messages.append(transformed_msg)

        response_content = {
            'status': True,
            'message': 'Group Messages Retrieved',
            'data': transformed_messages
        }

        return Response(response_content, status=status.HTTP_200_OK)


class GroupListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retrieve all groups for the authenticated user,
            ensuring they are members."""
        user = request.user

        groups = list(Group.objects.filter(members=user).values(
            'id', 'name', 'invite_code'))

        response_content = {
            'status': True,
            'message': 'User Groups Retrieved',
            'data': groups
        }

        return Response(response_content, status=status.HTTP_200_OK)
