from django.urls import path
from .import views

urlpatterns = [
    path('',views.adminLogin),
    path('admin-dash/',views.adminDashboard),
    path('admin-log-out/',views.adminLogOut),

    path('profile/',views.adminProfile),
    path('admin_profile_img/',views.adminProfilePicture),
    path('admin_inst_img/',views.adminInstitutionPicture),

    path('all-institution/',views.adminAllInstitution),
    path('change-institution-status/<int:iid>/',views.AdminChangeInstitutionStatus),
    path('delete-institution/<int:iid>/',views.adminDeleteInstitutionPermanent),
    path('update-institution/<int:iid>/',views.adminUpdateInstitution),

    path('all-insti-admin/',views.adminAllInstiAdmin),
    path('change-admin-status/<int:aid>/',views.AdminChangeInstitutionAdminStatus),
    path('delete-insti-admin/<int:aid>/',views.adminDeletePermanent),
    path('update-institution-admin/<int:aid>/',views.adminUpdateInstitutionAdmin),

    path('update-bank/',views.adminUpdateBankDetails, name='update_bank'),

    path('all-project/',views.adminAllProject),
    path('add-project/', views.adminAddProject, name='admin_add_project'),
    path('single-project/<int:pid>/',views.adminSingleProject),
    path('update-project/<int:pid>/', views.adminUpdateProject, name='admin_update_project'),
    path('change-project-status/<int:pid>/',views.adminChangeProjectStatus),
    path('delete-project/<int:pid>/',views.adminDeleteProject),
    path('upload_project_image/<int:project_id>/', views.upload_project_image, name='upload_project_image'),
    path('bene_img/<int:prj_id>/', views.upload_beneficiary_image, name='upload_beneficiary_image'),
    path('del_prj_img/<int:img_id>/', views.delete_project_image, name='upload_project_image'),

    path('all-transactions/',views.adminAllTransactions),
    path('verify-transaction/<int:tid>/',views.adminVerifyTransaction),
    path('approve-transaction/<int:tid>/',views.adminApproveTransaction),
    path('reject-transaction/<int:tid>/',views.adminRejectTransaction),
    path('unverify-transaction/<int:tid>/',views.adminUnverifyTransaction),

    path('generate-receipt/<int:t_id>/', views.adminGenerateReceipts),
    path('all-receipts/',views.adminAllReceipts),
    path('send-receipt/<int:r_id>/',views.adminSendReciept),
]