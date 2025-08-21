from django.urls import path
from .import views

urlpatterns = [
    path('admin-dash/',views.adminDashboard),
    path('admin-log-out/',views.adminLogOut),

    path('all-project/',views.adminAllProject),
    path('single-project/<int:pid>/',views.adminSingleProject),
    path('upload_project_image/<int:project_id>/', views.upload_project_image, name='upload_project_image'),
    path('bene_img/<int:prj_id>/', views.upload_beneficiary_image, name='upload_beneficiary_image'),
    path('del_prj_img/<int:img_id>/', views.delete_project_image, name='upload_project_image'),

    path('all-bank/',views.adminAllBankDetails),
    path('all-institution/',views.adminAllInstitution),
    path('all-insti-admin/',views.adminAllInstiAdmin),
]