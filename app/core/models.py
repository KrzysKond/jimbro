from django.db import models
from django.contrib.auth.models import (
    BaseUserManager,
    AbstractUser,
    PermissionsMixin
)

"""
Database models
"""


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


class User(AbstractUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME = 'email'
