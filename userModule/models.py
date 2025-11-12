from django.db import models
from adminModule.models import Project, Institution


# Create your models here.
class PersonalDetails(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField(null=True)
    phone = models.CharField(max_length=20)
    address = models.TextField()

    def __str__(self):
        return f"{self.full_name}"


class SelectedTile(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='projects')
    sender = models.ForeignKey(PersonalDetails,on_delete=models.CASCADE, null=True)
    tiles = models.CharField(max_length=255)
    funded_at = models.DateTimeField(auto_now_add=True)
    table_status = models.BooleanField(default=True)

    def __str__(self):
        return f"Tiles for {self.sender.first_name} {self.sender.last_name} on {self.project.title}"


class Transaction(models.Model):
    tiles_bought = models.ForeignKey(SelectedTile, on_delete=models.SET_NULL, null=True, blank=True,)
    sender = models.ForeignKey(PersonalDetails, on_delete=models.CASCADE, null=True)
    project = models.ForeignKey(Project,on_delete=models.CASCADE,)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=10,)
    tracking_id = models.CharField(max_length=255, unique=True)
    transaction_time = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=255, blank=True)
    table_status = models.BooleanField(default=True)

    def __str__(self):
        return f"Transaction {self.tracking_id} by {self.sender.full_name}"


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


class Receipt80mm(models.Model):
    transaction = models.ForeignKey(Transaction,on_delete=models.CASCADE,)
    receipt_80mm_pdf = models.FileField(upload_to='receipts80mm/')
    table_status = models.BooleanField(default=True)

    def __str__(self):
        return f"Receipt for Transaction {self.transaction.transaction_id}"


class ContactMessage(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(null=True)
    phone = models.CharField(max_length=15)
    message = models.TextField()
    ins = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='institution', null= True)
    sent_time = models.DateTimeField(auto_now_add=True)
    table_status = models.BooleanField(default=True, null=True)

    class Meta:
        ordering = ['-sent_time']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class MessageReply(models.Model):
    message = models.ForeignKey(ContactMessage, on_delete=models.CASCADE, related_name='msg')
    reply = models.TextField()
    reply_time = models.DateTimeField(auto_now_add=True)
    table_status = models.BooleanField(default=True, null=True)

    class Meta:
        ordering = ['-reply_time']

    def __str__(self):
        return f'Reply to {self.message.first_name} {self.message.last_name} at {self.reply_time}'