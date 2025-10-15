from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import CharField


# Create your models here.
class BankDetails(models.Model):
    account_holder_first_name = models.CharField(max_length=100,null=True)
    account_holder_last_name = models.CharField(max_length=100,null=True)
    account_holder_address = models.CharField(max_length=255)
    account_holder_phn_no = models.CharField(max_length=15, blank=True, null=True)
    bank_name = models.CharField(max_length=100)
    branch_name = models.CharField(max_length=100, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    account_no = models.CharField(max_length=50)
    upi_id = models.CharField(max_length=100, blank=True, null=True)
    table_status = models.BooleanField(default=True)

    def __str__(self):
        return f"Bank details for {self.account_holder_first_name}  {self.account_holder_last_name}"



class Institution(models.Model):
    institution_name = models.CharField(max_length=255,)
    address = models.TextField()
    phn = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    email_app_password = CharField(max_length=255, blank=True, null=True)
    default_bank = models.ForeignKey(BankDetails, on_delete=models.SET_NULL, null=True, blank=True,)
    institution_img = models.ImageField(upload_to='institution_img/', blank=True, null=True)
    table_status = models.BooleanField(default=True)

    def __str__(self):
        return self.institution_name


class CustomUser(AbstractUser):
    email = models.EmailField(null=False, blank=False)
    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True)
    phn_no = models.CharField(max_length=15, blank=True, null=True)
    profile_pic = models.ImageField(upload_to='user_profile_pics/', blank=True, null=True)
    table_status = models.BooleanField(default=True)

    def __str__(self):
        return f"User: {self.email}"


class Beneficial(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField()
    age = models.IntegerField()
    profile_pic = models.ImageField(upload_to='beneficiar_pics/', blank=True, null=True)
    table_status = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    beneficiary = models.ForeignKey(Beneficial, on_delete=models.CASCADE)
    funding_goal = models.DecimalField(max_digits=19, decimal_places=2)
    current_amount = models.DecimalField(max_digits=19, decimal_places=2, default=0)
    tile_value = models.DecimalField(max_digits=19, decimal_places=2)
    created_by =  models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    closed_by = models.DateTimeField(null=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    table_status = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class ProjectImage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='images')
    project_img = models.ImageField(upload_to='project_images/')
    table_status = models.BooleanField(default=True)

    def __str__(self):
        return f"Image for {self.project.title}"


class Reports(models.Model):
    project = models.ForeignKey(Project,on_delete=models.CASCADE,)
    report_pdf = models.FileField(upload_to='reports/')
    table_status = models.BooleanField(default=True)

    def __str__(self):
        return f"Report for Project {self.project.title}"