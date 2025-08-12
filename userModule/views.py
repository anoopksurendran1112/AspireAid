from datetime import date
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from adminModule.models import Project
from userModule.models import CustomUser


# Create your views here.
@login_required(login_url='/sign-in/')
def userDashboard(request):
    if request.user.is_superuser == False and request.user.is_staff == False:
        return render(request, "user-dashboard.html", {'user':request.user})
    else:
        return redirect('/sign-in/')


def userAvailbleProjects(request):
    if request.user.is_superuser == False and request.user.is_staff == False:
        avail_prj = Project.objects.filter(closing_date__gte=date.today())
        return render(request,'user-available-project.html', {'user':request.user, 'projects':avail_prj})
    else:
        return redirect('/sign-in/')


def userSingleProject(request):
    if request.user.is_superuser == False and request.user.is_staff == False:
        avail_prj = Project.objects.filter(closing_date__gte=date.today())
        return render(request, 'user-single-project.html', {'user': request.user, 'projects': avail_prj})
    else:
        return redirect('/sign-in/')