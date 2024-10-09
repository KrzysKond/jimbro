import io
import os
import random
import string
import uuid

from django.db import models
from django.contrib.auth.models import (
    BaseUserManager,
    AbstractBaseUser,
    PermissionsMixin
)
from django.conf import settings
from PIL import Image as PilImage
from django.core.files.base import ContentFile


def process_image(image):
    img = PilImage.open(image)
    img_io = io.BytesIO()
    img = img.convert("RGB")
    img.save(img_io, format='JPEG', quality=80)
    img_file = ContentFile(img_io.getvalue(), name=image.name)
    return img_file


def workout_image_file_path(instance, filename):
    """Generate new file path for workout image."""
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'

    return os.path.join('uploads', 'workout', filename)


def create_unique_invite_code(length=6):
    characters = string.ascii_uppercase + string.digits
    code = ''.join(random.choice(characters) for _ in range(length))
    return code


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """Create, save, and return a new user."""
        if not email:
            raise ValueError('User must have an email address.')

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create, save, and return a new superuser."""
        user = self.create_user(email, password, **extra_fields)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'


class Group(models.Model):
    """Group model."""
    name = models.CharField(max_length=255)
    invite_code = models.CharField(
        max_length=6, unique=True,
        default=create_unique_invite_code, null=True)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='group_memberships')

    def __str__(self):
        return self.name


class Workout(models.Model):
    """Workout model."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    title = models.CharField(max_length=255)
    image = models.ImageField(null=True, upload_to=workout_image_file_path)
    date = models.DateField()

    def save(self, *args, **kwargs):
        if self.image:
            self.image = process_image(self.image)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Message(models.Model):
    """Message model"""
    content = models.TextField(max_length=1024)
    group = models.ForeignKey(Group, on_delete=models.PROTECT)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL,
                               on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
