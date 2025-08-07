from django.contrib import admin
from .models import Project, BankDetails, Beneficial, ProjectImage

# Register your models here.
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title','description','beneficiary','funding_goal','tile_value','created_at','closing_date','table_status')


class BankDetailsAdmin(admin.ModelAdmin):
    list_display = ('project','account_holder_name','account_holder_address','account_holder_phn_no','bank_name','branch_name','ifsc_code','account_no','upi_id','table_status')


class BeneficialAdmin(admin.ModelAdmin):
    list_display = ('first_name','last_name','phone_number','address','age','profile_pic','table_status')


class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ('project','project_img','table_status')

admin.site.register(Project, ProjectAdmin)
admin.site.register(BankDetails, BankDetailsAdmin)
admin.site.register(Beneficial, BeneficialAdmin)
admin.site.register(ProjectImage, ProjectImageAdmin)