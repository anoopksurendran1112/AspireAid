from django.db import models

# Create your models here.

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
    beneficiary = models.ForeignKey(Beneficial, on_delete=models.CASCADE, related_name='projects')
    funding_goal = models.DecimalField(max_digits=10, decimal_places=2)
    tile_value = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    closing_date = models.DateTimeField()
    table_status = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class BankDetails(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='bank_details')
    account_holder_name = models.CharField(max_length=200)
    account_holder_address = models.CharField(max_length=255)
    account_holder_phn_no = models.CharField(max_length=15, blank=True, null=True)
    bank_name = models.CharField(max_length=100)
    branch_name = models.CharField(max_length=100, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    account_no = models.CharField(max_length=50, unique=True)
    upi_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    table_status = models.BooleanField(default=True)

    def __str__(self):
        return f"Bank details for {self.project.title}"


class ProjectImage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='images')
    project_img = models.ImageField(upload_to='project_images/')
    table_status = models.BooleanField(default=True)

    def __str__(self):
        return f"Image for {self.project.title}"