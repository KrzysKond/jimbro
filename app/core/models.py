import io
import os
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
