import urllib.parse
from django.shortcuts import render, redirect
from django.urls import reverse
from adminModule.models import Project


# Create your views here.
def userSingleProject(request,prj_id):
    if  request.user and (request.user.is_superuser == False and request.user.is_staff == False):
        prj = Project.objects.get(id=prj_id)
        tile_range = range(1, int(prj.funding_goal // prj.tile_value) + 1)

        if request.method == "POST":
            selected_tiles = request.POST.get("selected_tiles_input")
            query_string = urllib.parse.urlencode({
                'project_id': prj.id,
                'selected_tiles': selected_tiles
            })
            return redirect(reverse('user_checkout') + '?' + query_string)
        return render(request, 'user-single-project.html', {'user': request.user, 'project': prj,'t_range': tile_range})
    else:
        return redirect('/sign-in/')


def userCheckoutView(request,):
    if request.user and (request.user.is_superuser == False and request.user.is_staff == False):
        if request.method == "GET":
            project_id = request.GET.get("project_id")
            selected_tiles = request.GET.get("selected_tiles")

            project = Project.objects.get(id=project_id)
            selected_tile_count = len(selected_tiles.split('-'))

        elif  request.method == "POST":
            return redirect('/user/user-dash/')
        return render(request, 'user-checkout.html', {'user': request.user, 'project': project, 'selected_tiles': selected_tiles, 'count':selected_tile_count})
    else:
        return redirect('/sign-in/')
