"""
Serialzers for the user api view
"""
import string
import random

from django.contrib.auth import (
    get_user_model,
    authenticate
)

from django.utils.translation import gettext as _
from rest_framework import serializers
from core.models import Group


def generate_unique_invite_code(length=6):
    characters = string.ascii_uppercase + string.digits
    while True:
        invite_code = ''.join(random.choice(characters) for _ in range(length))
        if not Group.objects.filter(invite_code=invite_code).exists():
            return invite_code


class UserNameSerializer(serializers.ModelSerializer):
    """Serializer to return just the name of the user"""

    class Meta:
        model = get_user_model()
        fields = ['name', 'id']
        read_only_fields = ['id']


class UserInfoSerializer(serializers.ModelSerializer):
    """Serializer for basic user info"""

    class Meta:
        model = get_user_model()
        fields = ['email', 'id', 'name']
        read_only_fields = ['id', 'email', 'name']


class UserImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images"""

    class Meta:
        model = get_user_model()
        fields = ['id', 'profile_picture']
        read_only_fields = ['id']
        extra_kwargs = {'profile_picture': {'required': True}}


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object"""

    class Meta:
        model = get_user_model()
        fields = ['email', 'password', 'name']
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}

    def create(self, validated_data):
        """Create and return user"""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update and return user"""
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()

        return user


class GroupSerializer(serializers.ModelSerializer):
    members = UserNameSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ['id', 'name', 'members', 'invite_code']
        read_only_fields = ['id', 'invite_code']

    def create(self, validated_data):
        members_data = validated_data.pop('members', None)
        group = Group.objects.create(**validated_data)
        request_user = self.context['request'].user
        group.members.add(request_user)

        if members_data is not None:
            group.members.set(members_data)
        return group

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for the user auth token"""
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        """Validate and auth the user"""
        email = attrs.get("email")
        password = attrs.get("password")
        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password
        )
        if not user:
            msg = _('Unable to authenticate with provided credentials')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user

        return attrs
