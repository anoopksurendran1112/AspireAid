from django.urls import path
from .import views

urlpatterns = [
    path('admin-dash/',views.adminDashboard),
    path('all-project/',views.adminAllProject),
    path('all-bank/',views.adminAllBankDetails),
]