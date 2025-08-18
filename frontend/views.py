from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.db import IntegrityError
from django.shortcuts import render, redirect

from adminModule.models import Institution
from userModule.models import CustomUser


# Create your views here.
def index(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if user.is_staff or user.is_superuser:
                return redirect('/administrator/admin-dash/')
            else:
                return redirect('/')
        else:
            return redirect('/')
    return render(request, "index.html")

