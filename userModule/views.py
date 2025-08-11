from django.shortcuts import render, redirect
from userModule.models import CustomUser


# Create your views here.
def userpage(request):
    if request.user.is_authenticated:
        logged_user_id = request.session.get('logged_user_id')
        logged_user = CustomUser.objects.get(id=logged_user_id)
        return render (request,"user-dashboard.html",{'user':logged_user})
    else:
        return redirect('/sign-in/')