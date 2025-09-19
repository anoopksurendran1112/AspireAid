from django.urls import path
from .import views

urlpatterns = [
    path('<int:ins_id>/',views.userIndex),
    path('<int:ins_id>/about/', views.about),
    path('<int:ins_id>/contact-us/', views.contact_us),
    path('<int:ins_id>/track-status/', views.userTrackStatus),
    path('<int:ins_id>/all-project/',views.userAllProject),

    path('<int:ins_id>/single-project/<int:prj_id>/',views.userSingleProject),
    path('<int:ins_id>/checkout/', views.userCheckoutView, name='user_checkout'),
    path('<int:ins_id>/proof/<int:trans_id>/', views.userProofUpload),
]