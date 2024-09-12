"""
Database models
"""
import os
import uuid

from django.db import models
from django.contrib.auth.models import (
    BaseUserManager,
    AbstractBaseUser,
    PermissionsMixin
)
from django.conf import settings


def workout_image_file_path(instance, filename):
    """generate new file path for new workout image"""
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'

    return os.path.join('uploads', 'workout', filename)


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_field):
        """create save and return a new user"""
        if not email:
            raise ValueError('user must have an email adress')

        user = self.model(email=self.normalize_email(email), **extra_field)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_field):
        """create save and return a new superuser"""
        user = self.create_user(email, password, **extra_field)
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


class Workout(models.Model):
    """Workout model"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    image = models.ImageField(null=True, upload_to=workout_image_file_path)

    def __str__(self):
        return self.title
