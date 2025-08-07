from django.urls import path
from .import views

urlpatterns = [
    path('admin-dash/',views.adminpage),
]