from django.urls import path
from .import views

urlpatterns = [
    path('index/<int:ins_id>/',views.userIndex),
    path('single-project/<int:prj_id>/',views.userSingleProject),
    path('checkout/', views.userCheckoutView, name='user_checkout'),
]