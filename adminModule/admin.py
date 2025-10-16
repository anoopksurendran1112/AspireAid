from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Project, BankDetails, Beneficial, ProjectImage, Institution,
    CustomUser, NotificationPreference  # Import the new model
)


# =========================================================================
# --- INLINES ---
# =========================================================================

# 1. Inline for NotificationPreference (for InstitutionAdmin)
class NotificationPreferenceInline(admin.StackedInline):
    model = NotificationPreference
    # Ensure there's only one instance to edit (due to OneToOneField)
    max_num = 1
    can_delete = False
    verbose_name_plural = 'Notification Channel Settings'
    fieldsets = (
        (None, {
            'fields': (
                ('sms_enabled', 'whatsapp_enabled', 'email_enabled'),
            ),
        }),
    )


# --- Inline for Institution (to view its default bank) ---
class BankDetailsInline(admin.TabularInline):
    model = BankDetails
    extra = 0
    # Note: If BankDetails is only linked via ForeignKey to Institution, this inline won't work
    # unless you are viewing the BankDetails object itself. Assuming this inline is for a related purpose.


# =========================================================================
# --- CUSTOM ADMINS ---
# =========================================================================

# --- Custom Admin for CustomUser ---
class CustomUserAdmin(UserAdmin):
    # Removed 'default_bank' as it is not on the CustomUser model
    list_display = UserAdmin.list_display + (
        'phn_no',
        'institution',
        'profile_pic',
        'table_status'
    )

    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': (
                'phn_no',
                'profile_pic',
                'institution',
                'table_status',
            )
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {
            'fields': (
                'phn_no',
                'profile_pic',
                'institution',
                'table_status',
            )
        }),
    )

    list_filter = UserAdmin.list_filter + ('institution', 'table_status')
    search_fields = ('email', 'phn_no', 'institution__institution_name')


# --- Standard Model Admins ---
class InstitutionAdmin(admin.ModelAdmin):
    list_display = (
        'institution_name',
        'email',
        'phn',
        'default_bank',
        'table_status'
    )
    search_fields = ('institution_name', 'email')
    list_filter = ('table_status',)

    # 2. Add the NotificationPreferenceInline here
    inlines = [NotificationPreferenceInline]

    # Optional: Group the fields for better layout
    fieldsets = (
        (None, {
            'fields': ('institution_name', 'address', 'phn', 'email', 'default_bank', 'institution_img', 'table_status')
        }),
    )


class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'beneficiary',
        'funding_goal',
        'current_amount',
        'tile_value',
        'created_by',
        'closed_by',
        'table_status'
    )
    list_filter = ('created_by', 'beneficiary', 'closed_by', 'table_status')
    search_fields = ('title', 'beneficiary__first_name', 'created_by__institution_name')
    date_hierarchy = 'started_at'


class BankDetailsAdmin(admin.ModelAdmin):
    list_display = (
        'account_holder_first_name',
        'account_holder_last_name',
        'bank_name',
        'account_no',
        'upi_id',
        'table_status'
    )
    list_filter = ('bank_name', 'table_status')
    search_fields = ('account_no', 'upi_id', 'account_holder_first_name')


class BeneficialAdmin(admin.ModelAdmin):
    list_display = (
        'first_name',
        'last_name',
        'age',
        'phone_number',
        'table_status'
    )
    list_filter = ('age', 'table_status')
    search_fields = ('first_name', 'last_name', 'phone_number')


class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ('project', 'project_img', 'table_status')
    list_filter = ('project__title', 'table_status')


# =========================================================================
# --- REGISTERING MODELS ---
# =========================================================================

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Institution, InstitutionAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(BankDetails, BankDetailsAdmin)
admin.site.register(Beneficial, BeneficialAdmin)
admin.site.register(ProjectImage, ProjectImageAdmin)