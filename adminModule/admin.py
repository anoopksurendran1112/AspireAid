from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Project, BankDetails, Beneficial, ProjectImage, Institution,
    CustomUser, NotificationPreference, ProjectUpdates  # 1. Import ProjectUpdates
)


# =========================================================================
# --- INLINES ---
# =========================================================================

# Inline for ProjectUpdates (to be used in ProjectAdmin)
class ProjectUpdatesInline(admin.TabularInline):
    model = ProjectUpdates
    extra = 1  # Show one empty form for adding a new update
    fields = ('update_title', 'update', 'table_status')
    readonly_fields = ('update_date',)
    verbose_name_plural = 'Project Updates'


# Inline for NotificationPreference (for InstitutionAdmin)
class NotificationPreferenceInline(admin.StackedInline):
    model = NotificationPreference
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


# Inline for Institution (to view its default bank) ---
class BankDetailsInline(admin.TabularInline):
    model = BankDetails
    extra = 0


# =========================================================================
# --- CUSTOM ADMINS ---
# =========================================================================

# --- Custom Admin for CustomUser ---
class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + (
        'phn_no',
        'institution',
        'profile_pic',
        'table_status'
    )
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('phn_no', 'profile_pic', 'institution', 'table_status')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('phn_no', 'profile_pic', 'institution', 'table_status')}),
    )
    list_filter = UserAdmin.list_filter + ('institution', 'table_status')
    search_fields = ('email', 'phn_no', 'institution__institution_name')


# --- Standard Model Admins ---
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('institution_name', 'email', 'phn', 'default_bank', 'table_status')
    search_fields = ('institution_name', 'email')
    list_filter = ('table_status',)
    inlines = [NotificationPreferenceInline]
    fieldsets = (
        (None, {'fields': ('institution_name', 'address', 'phn', 'email', 'default_bank', 'institution_img',
                           'table_status')}),
    )


class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'beneficiary',
        'funding_goal',
        'current_amount',
        'created_by',
        'table_status'
    )
    list_filter = ('created_by', 'beneficiary', 'table_status')
    search_fields = ('title', 'beneficiary__first_name', 'created_by__institution_name')
    date_hierarchy = 'started_at'

    # 2. Add the ProjectUpdatesInline here
    inlines = [ProjectUpdatesInline]


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

# 3. ProjectUpdates is managed through the ProjectAdmin inline, so it does not need to be registered separately.
# If you wanted a standalone page for updates, you would uncomment the line below:
# admin.site.register(ProjectUpdates)