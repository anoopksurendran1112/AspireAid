from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from adminModule.models import Project, Institution, BankDetails

STATUS_CHOICES = (('PENDING', 'Pending'), ('SUCCESS', 'Success'),('FAILED', 'Failed'),)

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


class Transaction(models.Model):
    tiles_bought = models.ForeignKey(SelectedTile, on_delete=models.SET_NULL, null=True, blank=True,)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,)
    project = models.ForeignKey(Project,on_delete=models.CASCADE,)
    upi_id = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    transaction_id = models.CharField(max_length=255, unique=True)
    transaction_time = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=255, blank=True)
    table_status = models.BooleanField(default=True)

    def __str__(self):
        return f"Transaction {self.transaction_id} by {self.user.username}"


class Screenshot(models.Model):
    transaction = models.ForeignKey(Transaction,on_delete=models.CASCADE,)
    screen_shot = models.ImageField(upload_to='screenshots/')
    table_status = models.BooleanField(default=True)

    def __str__(self):
        return f"Screenshot for Transaction {self.transaction.transaction_id}"


class Receipt(models.Model):
    transaction = models.ForeignKey(Transaction,on_delete=models.CASCADE,)
    receipt_pdf = models.FileField(upload_to='receipts/')
    table_status = models.BooleanField(default=True)

    def __str__(self):
        return f"Receipt for Transaction {self.transaction.transaction_id}"