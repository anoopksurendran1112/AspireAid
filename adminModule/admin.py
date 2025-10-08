from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import ( Project, BankDetails, Beneficial, ProjectImage, Institution, CustomUser)


# --- Custom Admin for CustomUser ---
class CustomUserAdmin(UserAdmin):
    # Removed 'default_bank' as it is not on the CustomUser model
    list_display = UserAdmin.list_display + (
        'phn_no',
        'institution',
        'profile_pic',
        'table_status'
    )

    # Custom fields for displaying/editing user details
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

    # Custom fields for creating a new user in the admin
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


# --- Inline for Institution (to view its default bank) ---
class BankDetailsInline(admin.TabularInline):
    model = BankDetails
    extra = 0
    # Restrict fields if necessary


# --- Standard Model Admins ---
class InstitutionAdmin(admin.ModelAdmin):
    list_display = (
        'institution_name',
        'email',
        'phn',
        'default_bank',  # Now correctly linked to BankDetails
        'table_status'
    )
    search_fields = ('institution_name', 'email')
    list_filter = ('table_status',)


class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'beneficiary',
        'funding_goal',
        'current_amount',
        'tile_value',
        'created_by',
        'closing_date',
        'table_status'
    )
    list_filter = ('created_by', 'beneficiary', 'closing_date', 'table_status')
    search_fields = ('title', 'beneficiary__first_name', 'created_by__institution_name')
    date_hierarchy = 'created_at'


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


# --- Registering Models ---
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Institution, InstitutionAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(BankDetails, BankDetailsAdmin)
admin.site.register(Beneficial, BeneficialAdmin)
admin.site.register(ProjectImage, ProjectImageAdmin)