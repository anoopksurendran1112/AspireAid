from django.contrib import admin
from .models import SelectedTile, Transaction, Screenshot, Receipt, PersonalDetails


# Register your models here.


class PersonalDetailsAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'address')


class SelectedTileAdmin(admin.ModelAdmin):
    list_display = ('project', 'sender', 'tiles', 'funded_at', 'table_status')


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('tracking_id', 'sender', 'project', 'amount', 'status', 'transaction_time', 'table_status')


class ScreenShotAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'screen_shot', 'table_status')


class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'receipt_pdf', 'table_status')


admin.site.register(PersonalDetails, PersonalDetailsAdmin)
admin.site.register(SelectedTile, SelectedTileAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Screenshot, ScreenShotAdmin)
admin.site.register(Receipt, ReceiptAdmin)
