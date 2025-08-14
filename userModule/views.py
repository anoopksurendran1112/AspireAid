from datetime import date
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from adminModule.models import Project
from userModule.models import CustomUser


# Create your views here.
@login_required(login_url='/sign-in/')
def userDashboard(request):
    if request.user and (request.user.is_superuser == False and request.user.is_staff == False):
        return render(request, "user-dashboard.html", {'user':request.user})
    else:
        return redirect('/sign-in/')


def userAvailbleProjects(request):
    if request.user and (request.user.is_superuser == False and request.user.is_staff == False):
        admin = CustomUser.objects.filter(is_staff = True, institution=request.user.institution)
        avail_prj = Project.objects.filter(closing_date__gte=date.today(), created_by__in=admin)
        return render(request,'user-available-project.html', {'user':request.user, 'projects':avail_prj})
    else:
        return redirect('/sign-in/')


def userSingleProject(request,prj_id):
    if  request.user and (request.user.is_superuser == False and request.user.is_staff == False):
        prj = Project.objects.get(id=prj_id)
        tile_range = range(1, int(prj.funding_goal // prj.tile_value) + 1)
        return render(request, 'user-single-project.html', {'user': request.user, 'project': prj,'t_range': tile_range})
    else:
        return redirect('/sign-in/')