from django.db.models.signals import post_save
from django.conf import settings
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Otp

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_token(sender, user, created, **kwargs):
    if created:
        Otp.objects.create(user=user)
        user.is_active = False
        user.save()

        otp = Otp.objects.filter(user=user).last()
        subject = "Verification Code via Email"
        message = "Here is your verification code: {otp.code}"
        sender = "jttagaza@gmail.com"
        receiver = [user.email]

        send_mail(subject, message, sender, receiver, fail_silently=False)