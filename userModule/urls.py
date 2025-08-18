from django.urls import path
from .import views

urlpatterns = [
    path('user-single-project/<int:prj_id>/',views.userSingleProject),
    path('checkout/', views.userCheckoutView, name='user_checkout'),
]