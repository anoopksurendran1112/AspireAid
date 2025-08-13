from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, SelectedTile


# Register your models here.
class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ('email', 'phn_no', 'profile_pic', 'table_status')
    fieldsets = UserAdmin.fieldsets + ((None, {'fields': ('phn_no', 'profile_pic', 'table_status',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + ((None, {'fields': ('phn_no', 'profile_pic', 'table_status',)}),)


class SelectedTileAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'tiles', 'funded_at', 'table_status')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(SelectedTile, SelectedTileAdmin)
