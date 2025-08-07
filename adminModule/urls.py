from django.urls import path
from .import views

urlpatterns = [
    path('admin-dash/',views.adminDashboard),
    path('add-project/',views.adminAddProject),
]