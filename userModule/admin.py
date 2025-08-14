from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, SelectedTile, Transaction, Screenshot, Receipt


# Register your models here.
class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ('phn_no', 'institution', 'default_bank', 'profile_pic', 'table_status')
    fieldsets = UserAdmin.fieldsets + (('Custom Fields', {'fields': ('default_bank','phn_no', 'profile_pic', 'table_status', 'institution',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Custom Fields', {'fields': ('default_bank','phn_no', 'profile_pic', 'table_status', 'institution',)}),)
    list_filter = UserAdmin.list_filter + ('institution',)


class SelectedTileAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'tiles', 'funded_at', 'table_status')


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'project', 'amount', 'status', 'transaction_time', 'table_status')


class ScreenShotAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'screen_shot', 'table_status')


class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'receipt_pdf', 'table_status')


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(SelectedTile, SelectedTileAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Screenshot, ScreenShotAdmin)
admin.site.register(Receipt, ReceiptAdmin)
