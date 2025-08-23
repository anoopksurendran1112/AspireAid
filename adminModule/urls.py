from django.urls import path
from .import views

urlpatterns = [
    path('admin-dash/',views.adminDashboard),
    path('admin-log-out/',views.adminLogOut),

    path('update-bank/',views.adminUpdateBankDetails, name='update_bank'),
    path('profile/',views.adminProfile),

    path('all-project/',views.adminAllProject),
    path('single-project/<int:pid>/',views.adminSingleProject),
    path('upload_project_image/<int:project_id>/', views.upload_project_image, name='upload_project_image'),
    path('bene_img/<int:prj_id>/', views.upload_beneficiary_image, name='upload_beneficiary_image'),
    path('del_prj_img/<int:img_id>/', views.delete_project_image, name='upload_project_image'),

    path('all-transactions/',views.adminAllTransactions),
    path('verify-transaction/<int:tid>/',views.adminVerifyTransaction),
    path('approve-transaction/<int:tid>/',views.adminApproveTransaction),
    path('reject-transaction/<int:tid>/',views.adminRejectTransaction),
    path('unverify-transaction/<int:tid>/',views.adminUnverifyTransaction),

    path('all-institution/',views.adminAllInstitution),
    path('all-insti-admin/',views.adminAllInstiAdmin),
]