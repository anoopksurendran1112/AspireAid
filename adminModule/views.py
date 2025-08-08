from django.shortcuts import render

# Create your views here.

def adminDashboard(request):
    return render(request, "admin-dashboard.html")


def adminAddProject(request):
    return render(request, "admin-add-project.html")


def adminAllBankDetails(request):
    return render(request, "admin-all-bank-details.html")


def adminEditDefaultBankDetails(request):
    return render(request,"admin-edit-default-bank-details.html")