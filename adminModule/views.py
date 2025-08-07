from django.shortcuts import render

# Create your views here.

def adminpage(request):
    return render(request, "adminDashboard.html")


def adminAddProject(request):
    return render(request, "admin-add-project.html")
