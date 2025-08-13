from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from adminModule.models import Project, Institution, BankDetails


# Create your models here.
class CustomUser(AbstractUser):
    email = models.EmailField(null=False, blank=False)
    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True)
    phn_no = models.CharField(max_length=15, blank=True, null=True)
    default_bank = models.ForeignKey(BankDetails, on_delete=models.SET_NULL, null=True, blank=True,)
    profile_pic = models.ImageField(upload_to='user_profile_pics/', blank=True, null=True)
    table_status = models.BooleanField(default=True)

    def __str__(self):
        return f"User: {self.email}"


class SelectedTile(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='projects')
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    tiles = models.CharField(max_length=255)
    funded_at = models.DateTimeField(auto_now_add=True)
    table_status = models.BooleanField(default=True)

    def __str__(self):
        return f"Tiles for {self.user.username} on {self.project.title}"