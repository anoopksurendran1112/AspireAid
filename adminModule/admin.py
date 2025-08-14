from django.contrib import admin
from .models import Project, BankDetails, Beneficial, ProjectImage, Institution

# Register your models here.
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


admin.site.register(Institution, InstitutionAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(BankDetails, BankDetailsAdmin)
admin.site.register(Beneficial, BeneficialAdmin)
admin.site.register(ProjectImage, ProjectImageAdmin)