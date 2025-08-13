from django.urls import path
from .import views

urlpatterns = [
    path('admin-dash/',views.adminDashboard),
    path('all-project/',views.adminAllProject),
    path('single-project/',views.adminSingleProject),
    path('all-bank/',views.adminAllBankDetails),
    path('all-institution/',views.adminAllInstitution),
    path('all-insti-admin/',views.adminAllInstiAdmin),
]