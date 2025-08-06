from django.shortcuts import render


# Create your views here.
def index(request):
    return render(request, "index.html")


def about(request):
    return render(request, "about.html")

  
def contactus(request):
    return render(request,"contactus.html")


def sign_in(request):
    return render(request, "sign-in.html")


def sign_up(request):
    return render(request, "sign-up.html")
