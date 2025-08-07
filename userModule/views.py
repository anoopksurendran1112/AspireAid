from django.shortcuts import render

# Create your views here.
def userpage(request):
    return render (request,"userpage.html")