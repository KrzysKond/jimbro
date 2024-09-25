"""
Views for the user API
"""
from rest_framework import (
    generics, authentication,
    permissions, viewsets, status)
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from user.serializers import (
    UserSerializer,
    AuthTokenSerializer,
    GroupSerializer
)

from core.models import Group, User


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    @action(methods=['GET'], detail=False)
    def my_groups(self, request):
        groups = Group.objects.filter(members=request.user)
        serializer = self.get_serializer(groups, many=True)
        return Response(serializer.data)

    @action(methods=['POST'], detail=True, url_path='leave')
    def leave_group(self, request, pk=None):
        group = self.get_object()
        user = request.user
        if user in group.members.all():
            group.members.remove(user)
            return Response(
                {'detail': 'User deleted from the group'},
                status=status.HTTP_200_OK
            )
        return Response(
            {'detail': 'User is not a member of a group'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(methods=['POST'], detail=True, url_path='join')
    def join_group(self, request, pk=None):
        """Allow a user to join a group."""
        group = self.get_object()
        user = request.user

        if user in group.members.all():
            return Response(
                {'detail': 'User is already a member of this group.'},
                status=status.HTTP_400_BAD_REQUEST)

        group.members.add(user)
        return Response({'detail': 'User added to the group.'},
                        status=status.HTTP_200_OK)


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system"""
    serializer_class = UserSerializer


class CreateUserTokenView(ObtainAuthToken):
    """Create a new token for user"""
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user"""
    serializer_class = UserSerializer
    queryset = User.objects.all()
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """retrieve and return the authenticated user"""
        return self.request.user

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)
