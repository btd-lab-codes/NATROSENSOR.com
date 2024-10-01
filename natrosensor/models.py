from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.conf import settings
from django.utils import timezone

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
    created_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255)
    antibiotics = models.CharField(max_length=255)
    trial = models.IntegerField(default=1)
    temperature = models.CharField(max_length=255, null=True)
    ph = models.CharField(max_length=255, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    graph = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name
    
    def getData(self):
        record = {
            'name': self.name,
            'created_date': timezone.localtime(self.created_at).strftime("%B %d, %Y"),
            'created_time': timezone.localtime(self.created_at).strftime("%I:%M %p"),
            'antibiotics': self.antibiotics,
            'trial': self.trial,
            'temperature': self.temperature,
            'ph': self.ph,
            'note': self.note,
            'graph': self.graph
        }

        return record

class Event(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    date = models.DateField(null=False)
    time = models.TimeField(null=False)
    detail = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['date', 'time']

    def __str__(self):
        return self.name
    
    def getData(self):
        event = {
            'name': self.name,
            'date': self.date.strftime("%B %d, %Y"),
            'time': self.time.strftime("%I:%M %p"),
            'detail': self.detail
        }

        return event
    
    def getYear(self):
        return self.date.year
    
    def getMonth(self):
        return self.date.month
    
    def getDay(self):
        return self.date.day

class Otp(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="otp")
    code = models.CharField(max_length=6)

    def __str__(self):
        return self.user.email
