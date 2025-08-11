from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.db import IntegrityError
from django.shortcuts import render, redirect
from userModule.models import CustomUser


# Create your views here.
def index(request):
    return render(request, "index.html")


def about(request):
    return render(request, "about.html")

  
def contactus(request):
    return render(request,"contact-us.html")


def sign_in(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            request.session['logged_user_id'] = user.id
            login(request, user)
            if user.is_staff or user.is_superuser:
                messages.success(request, 'Welcome to the Admin Dashboard!')
                return redirect('/administrator/admin-dash/')
            else:
                print({user.first_name})
                messages.success(request, f'Welcome, {user.first_name}!')
                return redirect('/user/user-dash/')
        else:
            messages.error(request, 'Invalid email or password.')
            return render(request, "sign-in.html")
    return render(request, 'sign-in.html')


def sign_up(request):
    if request.method == 'POST':
        firstname = request.POST.get('fname')
        lastname = request.POST.get('lname')
        em = request.POST.get('email')
        phn = request.POST.get('phn')
        pwd = request.POST.get('password')
        try:
            CustomUser.objects.create_user(
                first_name = firstname,
                last_name = lastname,
                email = em,
                username = em,
                phn_no = phn,
                password = pwd
            )
            messages.success(request, 'Registration successful! You can now sign in.')
            return redirect('/sign-in/')
        except IntegrityError:
            messages.error(request, 'A user with that username or email already exists.')
            return render(request, "sign-up.html")
    return render(request, "sign-up.html")
