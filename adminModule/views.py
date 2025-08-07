from django.shortcuts import render

# Create your views here.

def adminDashboard(request):
    return render(request, "admin-dashboard.html")


def adminAddProject(request):
    return render(request, "admin-add-project.html")