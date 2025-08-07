from django.urls import path
from .import views

urlpatterns = [
    path('user-dash/',views.userpage),
]