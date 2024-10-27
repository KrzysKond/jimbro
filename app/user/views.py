"""
Views for the user API
"""
from rest_framework import (
    generics, authentication,
    permissions, viewsets, status)
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from user.serializers import (
    UserSerializer,
    AuthTokenSerializer,
    GroupSerializer,
    UserInfoSerializer,
    UserImageSerializer
)

from core.models import Group, User

from core.aws_sns import create_endpoint


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

    @action(methods=['GET'], detail=False, url_path='group-by-invite-code')
    def group_by_invite_code(self, request):
        invite_code = request.query_params.get('invite_code', None)
        if invite_code is None:
            return Response(
                {'error': 'Invitation code is required'},
                status=status.HTTP_400_BAD_REQUEST)
        try:
            group = Group.objects.get(invite_code=invite_code)
            serializer = self.get_serializer(group)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Group.DoesNotExist:
            return Response(
                {'error': 'Group not found or invalid invitation code'},
                status=status.HTTP_404_NOT_FOUND)

    @action(methods=['POST'], detail=True, url_path='leave')
    def leave_group(self, request, pk=None):
        group = self.get_object()
        user = request.user
        if user in group.members.all():
            group.members.remove(user)
            if group.members.count() == 0:
                group.delete()
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
                status=status.HTTP_409_CONFLICT)

        group.members.add(user)
        return Response({'detail': 'User added to the group.'},
                        status=status.HTTP_200_OK)


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system"""
    serializer_class = UserSerializer


class CreateUserTokenView(ObtainAuthToken):
    """Create a new token for user and register the device."""
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

    def post(self, request, *args, **kwargs):
        """Override post method to create token and register device."""
        auth_data = {key: value for key,
        value in request.data.items() if key != 'device_token'}

        serializer = self.serializer_class(data=auth_data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        device_token = request.data.get('device_token')
        if device_token:
            create_endpoint(device_token)

        return Response({'token': token.key}, status=status.HTTP_200_OK)


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


class UserViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserInfoSerializer
    authentication_classes = [authentication.TokenAuthentication]

    @action(methods=['POST'], detail=False, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image for the authenticated user."""
        serializer = UserImageSerializer(data=request.data)

        if serializer.is_valid():
            user = request.user
            user.profile_picture = serializer.validated_data['profile_picture']
            user.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['GET'], detail=False)
    def get_user_info(self, request):
        """Retrieve basic information about a given user
        or the authenticated user if no ID is provided."""
        user_id = request.query_params.get('user_id', None)
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({'error': 'User not found'},
                                status=status.HTTP_404_NOT_FOUND)
        else:
            user = request.user

        serializer = UserInfoSerializer(user)
        image_serializer = UserImageSerializer(user)

        image_url = image_serializer.data.get('profile_picture', None)
        if image_url:
            image_url = request.build_absolute_uri(image_url)

        user_data = serializer.data
        user_data['profile_picture'] = image_url

        return Response(user_data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='profile-picture')
    def get_profile_picture(self, request):
        """Fetch only the profile picture
         of the authenticated user or specified user."""
        user_id = request.query_params.get('user_id', None)

        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({'error': 'User not found'},
                                status=status.HTTP_404_NOT_FOUND)
        else:
            user = request.user

        if user.profile_picture:
            image_url = request.build_absolute_uri(user.profile_picture.url)
            return Response({'profile_picture': image_url},
                            status=status.HTTP_200_OK)

        return Response({'profile_picture': None},
                        status=status.HTTP_404_NOT_FOUND)
