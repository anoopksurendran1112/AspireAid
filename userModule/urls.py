from django.urls import path
from .import views

urlpatterns = [
    path('user-dash/',views.userDashboard),
    path('user-avail-project/',views.userAvailbleProjects),
    path('user-single-project/<int:prj_id>/',views.userSingleProject),
]