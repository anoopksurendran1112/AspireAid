from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Project, BankDetails, Beneficial, ProjectImage, Institution, CustomUser


# Register your models here.
class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ('phn_no', 'institution', 'default_bank', 'profile_pic', 'table_status')
    fieldsets = UserAdmin.fieldsets + (('Custom Fields', {'fields': ('default_bank','phn_no', 'profile_pic', 'table_status', 'institution',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Custom Fields', {'fields': ('default_bank','phn_no', 'profile_pic', 'table_status', 'institution',)}),)
    list_filter = UserAdmin.list_filter + ('institution',)


class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('institution_name','address','phn', 'email', 'institution_img', 'table_status')


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title','description','beneficiary','funding_goal','tile_value','bank_details', 'created_by','created_at','closing_date','table_status')


class BankDetailsAdmin(admin.ModelAdmin):
    list_display = ('account_holder_first_name','account_holder_last_name','account_holder_address','account_holder_phn_no','bank_name','branch_name','ifsc_code','account_no','upi_id','table_status')


class BeneficialAdmin(admin.ModelAdmin):
    list_display = ('first_name','last_name','phone_number','address','age','profile_pic','table_status')


class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ('project','project_img','table_status')


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Institution, InstitutionAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(BankDetails, BankDetailsAdmin)
admin.site.register(Beneficial, BeneficialAdmin)
admin.site.register(ProjectImage, ProjectImageAdmin)