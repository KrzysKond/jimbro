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
from PIL import Image as PilImage, ExifTags
from django.core.files.base import ContentFile


def workout_image_file_path(instance, filename):
    """Generate new file path for workout image."""
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'

    return os.path.join('uploads', 'workout', filename)


def process_image(image):
    img = PilImage.open(image)

    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = img._getexif()
        if exif is not None:
            orientation_value = exif.get(orientation)
            if orientation_value is not None:
                if orientation_value == 3:
                    img = img.rotate(180, expand=True)
                elif orientation_value == 6:
                    img = img.rotate(270, expand=True)
                elif orientation_value == 8:
                    img = img.rotate(90, expand=True)
    except Exception as e:
        print(f"Error while processing EXIF data: {e}")

    img_io = io.BytesIO()
    img = img.convert("RGB")
    img.save(img_io, format='JPEG', quality=80)
    img_file = ContentFile(img_io.getvalue(), name=image.name)
    return img_file


def user_image_file_path(instance, filename):
    """Generate new file path for user profile pic."""
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'

    return os.path.join('uploads', 'user', filename)


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
    profile_picture = models.ImageField(
        null=True,
        upload_to=user_image_file_path)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    def save(self, *args, **kwargs):
        if self.profile_picture:
            self.profile_picture = process_image(self.profile_picture)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


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
    fires = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    liked_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='liked_workouts',
        blank=True)

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


class Comment(models.Model):
    """Comments model"""
    text = models.TextField()
    workout = models.ForeignKey(
        Workout,
        on_delete=models.CASCADE,
        related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new_comment = self.pk is None
        super().save(*args, **kwargs)

        if is_new_comment:
            self.workout.comments_count += 1
            self.workout.save()

    def delete(self, *args, **kwargs):
        workout = self.workout
        workout.comments_count -= 1
        workout.save()  # Update the count before deleting
        super().delete(*args, **kwargs)
