from django.urls import path
from .import views

urlpatterns = [
    path('index/<int:ins_id>/',views.userIndex),
    path('all-project/',views.userAllProject),
    path('single-project/<int:prj_id>/',views.userSingleProject),
    path('checkout/', views.userCheckoutView, name='user_checkout'),
    path('about/', views.about),
    path('contact-us/', views.contact_us),
]