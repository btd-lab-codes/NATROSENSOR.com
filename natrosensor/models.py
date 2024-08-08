from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.conf import settings

class CustomUserManager(BaseUserManager):
    def _create_user(self, email, password, first_name, last_name, institution, **extra_fields):
        if not email or not password:
            raise ValueError("Required credentials must be provided")
        
        user = self.model(
            email = self.normalize_email(email),              
            first_name = first_name,
            last_name = last_name,
            institution = institution,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, email, password, first_name, last_name, institution, **extra_fields):
        extra_fields.setdefault('is_active', True)
        return self._create_user(email, password, first_name, last_name, institution, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    institution = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'institution']

    def __str__(self):
        return self.email
    
class Records(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    antibiotics = models.CharField(max_length=255)
    trials = models.IntegerField(default=1)
    temperature = models.CharField(max_length=255, null=True)
    ph = models.CharField(max_length=255, blank=True, null=True)
    note = models.TextField(blank=True, null=True)

class Otp(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="otp")
    code = models.CharField(max_length=6)

    def __str__(self):
        return self.user.email
