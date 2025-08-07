from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class CustomUser(AbstractUser):
    email = models.EmailField(
        null=False,
        blank=False,
        help_text="Required. Must be an email address."
    )
    phn_no = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        help_text="Optional. Phone number for contact.")
    profile_pic = models.ImageField(
        upload_to='user_profile_pics/',
        blank=True,
        null=True,
        help_text="Optional. User's profile picture."
    )
    table_status = models.BooleanField(default=True)
