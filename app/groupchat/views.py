from rest_framework import status, generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from core.models import Group, Message

User = get_user_model()


class SmallResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 20

    def get_paginated_response(self, data):
        return Response({
            'status': True,
            'data': data,
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link()
        })


class GroupMessagesView(generics.ListAPIView):
    pagination_class = SmallResultsSetPagination
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        group_id = self.kwargs['group_id']
        group = Group.objects.filter(id=group_id).first()

        if group is None:
            return Message.objects.none()

        if not group.members.filter(id=self.request.user.id).exists():
            return Message.objects.none()

        return (Message.objects.filter(group__id=group_id)
                .order_by('-timestamp'))

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if not queryset.exists():
            return Response({
                "status": False,
                "message": "You are not a member of this group."},
                status=status.HTTP_403_FORBIDDEN)

        if page is not None:
            transformed_messages = [
                {
                    'id': msg.id,
                    'sender_id': msg.sender.id,
                    'sender_name': msg.sender.name,
                    'content': msg.content,
                    'timestamp': msg.timestamp,
                }
                for msg in page
            ]
            return self.get_paginated_response(transformed_messages)

        transformed_messages = [
            {
                'id': msg.id,
                'sender_id': msg.sender.id,
                'sender_name': msg.sender.name,
                'content': msg.content,
                'timestamp': msg.timestamp,
            }
            for msg in queryset
        ]

        if page is not None:
            return self.get_paginated_response(transformed_messages)

        return Response({
            'status': True,
            'message': 'Group Messages Retrieved',
            'data': transformed_messages
        }, status=status.HTTP_200_OK)


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
