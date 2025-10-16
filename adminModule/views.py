from adminModule.utils import generate_receipt_pdf, whatsapp_send_approve, email_send_approve, sms_send_approve, \
    email_send_reject, sms_send_reject, whatsapp_send_reject, email_send_unverify, sms_send_unverify, \
    whatsapp_send_unverify, sms_send_response, email_send_response, whatsapp_send_response, generate_report_pdf
from adminModule.models import BankDetails, Beneficial, Project, Institution, ProjectImage, CustomUser, Reports, \
    NotificationPreference
from userModule.models import Transaction, Receipt, Screenshot, ContactMessage, MessageReply
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from django.core.files.base import ContentFile
from decimal import Decimal, InvalidOperation
from django.db import IntegrityError
from django.contrib import messages
from django.utils import timezone
from django.db.models import F, Q, Count
from io import BytesIO
import datetime
import qrcode
import urllib
import os


# Create your views here.
def adminLogin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if user.is_staff or user.is_superuser:
                return redirect('/administrator/admin-dash/')
            else:
                messages.error(request, "You do not have administrative privileges.")
                return redirect('/administrator/')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
            return redirect('/administrator/')
    return render(request, "admin-login.html")


@login_required(login_url='/administrator/')
def adminDashboard(request):
    if request.user.is_superuser:
        all_prj = Project.objects.all().count()
        closed_prj = Project.objects.filter(closed_by__lte=timezone.now()).count()
        completed_prj = Project.objects.filter(current_amount__gte=F('funding_goal')).count()
        failed_prj = Project.objects.filter(closed_by__lte=timezone.now(), current_amount__lt=F('funding_goal')).count()

        all_tra = Transaction.objects.all().count()
        ver_tra = Transaction.objects.filter(status='Verified').count()
        unver_tra = Transaction.objects.filter(status='Unverified').count()
        rej_tra = Transaction.objects.filter(status='Rejected').count()

        latest_projects = Project.objects.filter(Q(closed_by__isnull=True), table_status=True).order_by('-started_at')[:5]

    elif request.user.is_staff:
        if not request.user.table_status or not request.user.institution.table_status:
            messages.error(request, "Your account or institution has been deactivated by the superuser.")
            return redirect('/administrator/logout/')

        all_prj = Project.objects.filter(created_by=request.user.institution).count()
        closed_prj = Project.objects.filter(created_by=request.user.institution, closed_by__lte=timezone.now()).count()
        completed_prj = Project.objects.filter(created_by=request.user.institution, current_amount__gte=F('funding_goal')).count()
        failed_prj = Project.objects.filter(created_by=request.user.institution, closed_by__lte=timezone.now(),current_amount__lt=F('funding_goal')).count()

        all_tra = Transaction.objects.filter(project__created_by=request.user.institution).count()
        ver_tra = Transaction.objects.filter(project__created_by=request.user.institution, status='Verified').count()
        unver_tra = Transaction.objects.filter(project__created_by=request.user.institution, status='Unverified').count()
        rej_tra = Transaction.objects.filter(project__created_by=request.user.institution, status='Rejected').count()

        latest_projects = Project.objects.filter(Q(closed_by__isnull=True),created_by=request.user.institution, table_status=True).order_by('-started_at')[:5]

    else:
        return redirect('/administrator/')

    context = {
        'all_prj': all_prj, 'cls_prj': closed_prj, 'lst_prj': latest_projects, 'cmp_prj': completed_prj, 'fail_prj': failed_prj,
        'all_tra': all_tra, 'ver_tra': ver_tra, 'unver_tra': unver_tra, 'rej_tra': rej_tra,}

    return render(request, "admin-dashboard.html", {'admin': request.user,'context': context})


def adminLogOut(request):
    logout(request)
    messages.warning(request, "You have been logged out successfully.")
    return redirect('/administrator/')


def adminCredit(request):
    return render(request, 'admin-credit.html',{'admin':request.user})


# Profile page of the logged admin
def adminProfile(request):
    if request.user.is_superuser:
        if not request.user.table_status:
            messages.error(request, "Your account has been deactivated by another superuser.")
            return redirect('/administrator/logout/')
        preference = None
    elif request.user.is_staff:
        if not request.user.table_status or not request.user.institution.table_status:
            messages.error(request, "Your account or institution has been deactivated by a superuser.")
            return redirect('/administrator/logout/')
        preference = NotificationPreference.objects.get(institution= request.user.institution)
    else:
        messages.error(request, "Your Don't have permission to access this page.")
        return redirect('/administrator/')

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phn_no = request.POST.get('phn_no')

        try:
            with db_transaction.atomic():
                request.user.first_name = first_name
                request.user.last_name = last_name
                request.user.email = email
                request.user.phn_no = phn_no
                request.user.save()

                if request.user.is_staff and request.user.institution:
                    institution_name = request.POST.get('institution_name')
                    institution_phn = request.POST.get('institution_phn')
                    institution_address = request.POST.get('institution_address')

                    inst = request.user.institution
                    inst.institution_name = institution_name
                    inst.phn = institution_phn
                    inst.address = institution_address
                    inst.save()

            messages.success(request, "Profile updated successfully!")
            return redirect('/administrator/profile/')
        except IntegrityError:
            messages.error(request, "Failed to update profile. The provided email might already be in use.")
            return redirect('/administrator/profile/')
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {e}")
            return redirect('/administrator/profile/')
    return render(request, 'admin-profile.html', {'admin': request.user, 'preference':preference})


def update_account_details(request):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('/administrator/')
    if not request.user.table_status or (request.user.is_staff and not request.user.institution.table_status):
        messages.error(request, "Your account or institution has been deactivated by the superuser.")
        return redirect('/administrator/logout/')

    if request.method != 'POST':
        return redirect('/administrator/profile/')

    old_password = request.POST.get('old_password')
    new_password = request.POST.get('new_password')
    confirm_password = request.POST.get('confirm_password')

    if not request.user.check_password(old_password):
        messages.error(request, "Invalid current password. Changes were not saved.")
        return redirect('/administrator/profile/')

    try:
        with db_transaction.atomic():
            updated_something = False

            new_username = request.POST.get('new_username')
            if new_username and new_username != request.user.username:
                if CustomUser.objects.filter(username=new_username).exists():
                    messages.error(request, "This username is already taken. Please choose a different one.")
                    return redirect('/administrator/profile/')
                request.user.username = new_username
                updated_something = True

            if new_password and confirm_password:
                if new_password != confirm_password:
                    messages.error(request, "New password and confirm password do not match.")
                    return redirect('/administrator/profile/')

                request.user.set_password(new_password)
                updated_something = True

            # --- Update Institution Email Credentials (for staff users) ---
            if request.user.is_staff and request.user.institution:
                institution_email = request.POST.get('institution_email')
                institution_app_password = request.POST.get('institution_app_password')

                inst = request.user.institution

                if institution_email and institution_email != inst.email:
                    if Institution.objects.filter(email=institution_email).exclude(id=inst.id).exists():
                        messages.error(request, "This institution email is already in use by another institution.")
                        return redirect('/administrator/profile/')
                    inst.email = institution_email
                    updated_something = True

                if institution_app_password and institution_app_password != inst.email_app_password:
                    inst.email_app_password = institution_app_password
                    updated_something = True

                if updated_something:
                    inst.save()

            request.user.save()

            if updated_something:
                messages.success(request, "Account details updated successfully!")
                if new_password:
                    user = authenticate(request, username=request.user.username, password=new_password)
                    if user is not None:
                        login(request, user)
                    else:
                        messages.info(request,"Your password has been updated. Please log in again with your new password.")
                        return redirect('/administrator/logout/')
            else:
                messages.info(request, "No changes were detected. Your profile remains the same.")
            return redirect('/administrator/profile/')

    except IntegrityError as e:
        messages.error(request,f"An integrity error occurred. This is likely because the username or email is already taken. Please try again.")
        return redirect('/administrator/profile/')
    except Exception as e:
        messages.error(request, f"An unexpected error occurred during the update: {e}")
        return redirect('/administrator/profile/')


# Updating logged admin's profile picture
def adminProfilePicture(request):
    if request.user.is_superuser or request.user.is_staff:
        if request.method == 'POST':
            uploaded_img = request.FILES.get('admin_img')
            if uploaded_img:
                request.user.profile_pic = uploaded_img
                request.user.save()
                messages.success(request, "Your profile picture has been updated successfully!")
            else:
                messages.error(request, "No image was uploaded. Please select a file.")
        return redirect('/administrator/profile/')
    else:
        return redirect('/administrator/')


# Updating logged admin's institution's picture
def adminInstitutionPicture(request):
    if request.user.is_superuser or request.user.is_staff:
        if request.method == 'POST':
            uploaded_img = request.FILES.get('inst_img')
            if uploaded_img:
                request.user.institution.institution_img = uploaded_img
                request.user.institution.save()
                messages.success(request, "Institution profile picture has been updated successfully!")
            else:
                messages.error(request, "No image was uploaded. Please select a file.")
        return redirect('/administrator/profile/')
    else:
        return redirect('/administrator/')


def adminUpdateNotification(request):
    if request.user.is_staff and request.user.institution:
        if not request.user.table_status or not request.user.institution.table_status:
            messages.error(request, "Your account or institution has been deactivated.")
            return redirect('/administrator/logout/')

        prefs= NotificationPreference.objects.get(institution=request.user.institution)

        if request.method == 'POST':
            prefs.email_enabled = 'email_enabled' in request.POST
            prefs.whatsapp_enabled = 'whatsapp_enabled' in request.POST
            prefs.sms_enabled = 'sms_enabled' in request.POST
            prefs.save()

            messages.success(request, "Notification preferences have been updated.")
        return redirect('/administrator/profile/')
    messages.error(request, "You do not have the required permissions for this action.")
    return redirect('/administrator/profile/')


def adminDefaultNotification(request):
    if request.user.is_staff and request.user.institution:
        if not request.user.table_status or not request.user.institution.table_status:
            messages.error(request, "Your account or institution has been deactivated.")
            return redirect('/administrator/logout/')

        prefs, created = NotificationPreference.objects.get_or_create(institution=request.user.institution,
                                                                      defaults={'sms_enabled': True, 'whatsapp_enabled': True, 'email_enabled': True})
        if not created:
            prefs.sms_enabled = True
            prefs.whatsapp_enabled = True
            prefs.email_enabled = True
            prefs.save()

        messages.success(request, "Notification preferences have been reset to default (all services enabled).")
        return redirect('/administrator/profile/')
    messages.error(request, "You do not have the required permissions for this action.")
    return redirect('/administrator/profile/')


# Superuser listing all Institutions and adding new Institutions
def adminAllInstitution(request):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to perform this action.")
        return redirect('/administrator/')

    if not request.user.table_status:
        messages.error(request, "Your account has been deactivated by another superuser.")
        return redirect('/administrator/logout/')

    inst = Institution.objects.all()

    institution_name = request.GET.get('institution_name')
    email_filter = request.GET.get('email_filter')
    phone_filter = request.GET.get('phone_filter')
    status_filter = request.GET.get('status_filter')
    name_order = request.GET.get('name_order')

    filter_conditions = Q()

    if institution_name:
        filter_conditions &= Q(institution_name__icontains=institution_name)

    if email_filter:
        filter_conditions &= Q(email__icontains=email_filter)

    if phone_filter:
        filter_conditions &= Q(phn__icontains=phone_filter)

    if status_filter:
        if status_filter == 'active':
            filter_conditions &= Q(table_status=True)
        elif status_filter == 'inactive':
            filter_conditions &= Q(table_status=False)

    if filter_conditions:
        inst = inst.filter(filter_conditions)

    if name_order:
        if name_order == 'asc':
            inst = inst.order_by('institution_name')
        elif name_order == 'desc':
            inst = inst.order_by('-institution_name')

    if request.method == "POST":
        inst_name = request.POST.get('inst_name')
        inst_email = request.POST.get('inst_email')
        inst_app_pwd = request.POST.get('inst_app_pwd')
        inst_phn = request.POST.get('inst_phn')
        inst_address = request.POST.get('inst_address')

        try:
            with db_transaction.atomic():
                new_inst = Institution(institution_name=inst_name, address=inst_address, phn=inst_phn, email=inst_email, email_app_password=inst_app_pwd)
                new_inst.save()
            messages.success(request, f'Registered {inst_name} Successfully.')
        except IntegrityError as e:
            if 'email' in str(e).lower():
                messages.error(request, "Registration failed: An institution with this email already exists.")
            else:
                messages.error(request, f"Registration failed due to a database integrity error {e}. Please check your inputs.")
        except Exception as e:
            messages.error(request, f"Failed to register new institution due to an unknown error {e}.")
        return redirect('/administrator/all-institution/')
    return render(request, "admin-all-institution.html", {'admin': request.user, 'institutions': inst})



def adminUpdateInstitution(request, iid):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to perform this action.")
        return redirect('/administrator/')

    institution = get_object_or_404(Institution, id=iid)
    if request.method == 'POST':
        try:
            with db_transaction.atomic():
                institution_name = request.POST.get('inst_name')
                institution_email = request.POST.get('inst_email')
                institution_phn = request.POST.get('inst_phn')
                institution_address = request.POST.get('inst_address')
                institution_app_password = request.POST.get('inst_app_pwd')

                institution.institution_name = institution_name
                institution.email = institution_email
                institution.phn = institution_phn
                institution.address = institution_address
                if institution_app_password:
                    institution.email_app_password = institution_app_password

                institution.save()

            messages.success(request, f'Institution "{institution.institution_name}" has been updated successfully.')
        except Exception as e:
            messages.error(request, f"Failed to update institution: {e}")
        return redirect('/administrator/all-institution/')
    else:
        return redirect('/administrator/all-institution/')


def AdminChangeInstitutionStatus(request, iid):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to perform this action.")
        return redirect('/administrator/')

    institution = get_object_or_404(Institution, id=iid)
    try:
        with db_transaction.atomic():
            if institution.table_status:
                institution.table_status = False
                messages.warning(request, f'Institution {institution.institution_name} has been deactivated.')
            else:
                institution.table_status = True
                messages.success(request,f'Institution {institution.institution_name} has been activated successfully.')
            institution.save()
    except Exception as e:
        messages.error(request, f"Failed to change institution status due to an error {e}.")
    return redirect('/administrator/all-institution/')


def adminDeleteInstitutionPermanent(request,iid):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to perform this action.")
        return redirect('/administrator/')
    institution = get_object_or_404(Institution, id=iid)
    institution.delete()
    messages.warning(request, f'Institution {institution.institution_name} has been permanently deleted.')
    return redirect('/administrator/all-institution/')


# Superuser listing all Institution's admins and adding new admin
def adminAllInstiAdmin(request):
    if not request.user.is_superuser:
        return redirect('/administrator/')

    if not request.user.table_status:
        messages.error(request, "Your account has been deactivated by another superuser.")
        return redirect('/administrator/logout/')

    # Start with the base queryset for administrators
    administrators = CustomUser.objects.filter(is_staff=True)
    inst = Institution.objects.all()

    # --- Advanced Filter Logic (GET request) ---
    if request.method == 'GET' and any(param in request.GET for param in
                                       ['admin_name', 'institution_filter', 'admin_username', 'admin_email',
                                        'admin_phone', 'status_filter', 'name_order', 'institution_order']):
        admin_name = request.GET.get('admin_name')
        institution_filter = request.GET.get('institution_filter')
        admin_username = request.GET.get('admin_username')
        admin_email = request.GET.get('admin_email')
        admin_phone = request.GET.get('admin_phone')
        status_filter = request.GET.get('status_filter')
        name_order = request.GET.get('name_order')
        institution_order = request.GET.get('institution_order')

        filter_conditions = Q()

        if admin_name:
            filter_conditions &= Q(first_name__icontains=admin_name) | Q(last_name__icontains=admin_name)
        if institution_filter:
            filter_conditions &= Q(institution__institution_name__icontains=institution_filter)
        if admin_username:
            filter_conditions &= Q(username__icontains=admin_username)
        if admin_email:
            filter_conditions &= Q(email__icontains=admin_email)
        if admin_phone:
            filter_conditions &= Q(phn_no__icontains=admin_phone)
        if status_filter:
            if status_filter == 'active':
                filter_conditions &= Q(table_status=True)
            elif status_filter == 'inactive':
                filter_conditions &= Q(table_status=False)

        administrators = administrators.filter(filter_conditions)

        if name_order:
            administrators = administrators.order_by(f"{'-' if name_order == 'desc' else ''}first_name")
        if institution_order:
            administrators = administrators.order_by(
                f"{'-' if institution_order == 'desc' else ''}institution__institution_name")

        # This will prevent the POST logic from running and render the filtered results
        return render(request, "admin-all-insti-admin.html",
                      {'admin': request.user, 'inst': inst, 'administrators': administrators})

    # --- Add New Admin Logic (POST request) ---
    if request.method == 'POST':
        firstname = request.POST.get('first_name')
        lastname = request.POST.get('last_name')
        em = request.POST.get('email')
        phn = request.POST.get('phn_no')
        inst = request.POST.get('inst_name')
        usr = request.POST.get('username')
        pwd = request.POST.get('password')
        try:
            ins = Institution.objects.get(id=inst)
            CustomUser.objects.create_user(
                first_name=firstname,
                last_name=lastname,
                email=em,
                institution=ins,
                username=usr,
                is_staff=True,
                phn_no=phn,
                password=pwd
            )
            messages.success(request, f'Registered new admin {firstname} {lastname} for {ins.institution_name}.')
            return redirect('/administrator/all-insti-admin/')
        except IntegrityError:
            messages.error(request,
                           'Failed to register new admin. A user with this username or email might already exist.')
            return redirect('/administrator/all-insti-admin/')
        except Exception as e:
            messages.error(request, f'An unexpected error occurred: {e}')
            return redirect('/administrator/all-insti-admin/')

    # Render the unfiltered page for the initial GET request
    return render(request, "admin-all-insti-admin.html",{'admin': request.user, 'inst': inst, 'administrators': administrators})


# Superuser Updating an Institution's admin details
def adminUpdateInstitutionAdmin(request, aid):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to perform this action.")
        return redirect('/administrator/')

    admin_to_update = get_object_or_404(CustomUser, id=aid)

    if request.method == 'POST':
        try:
            with db_transaction.atomic():
                old_password = request.POST.get('password')
                new_password = request.POST.get('confirm_password')

                if not admin_to_update.check_password(old_password):
                    messages.error(request, "Incorrect old password. Please try again.")
                    return redirect('/administrator/all-insti-admin/')
                if new_password:
                    admin_to_update.set_password(new_password)

                admin_to_update.first_name = request.POST.get('first_name')
                admin_to_update.last_name = request.POST.get('last_name')
                admin_to_update.email = request.POST.get('email')
                admin_to_update.phn_no = request.POST.get('phn_no')
                admin_to_update.username = request.POST.get('username')

                inst_id = request.POST.get('inst_name')
                admin_to_update.institution = get_object_or_404(Institution, id=inst_id)

                admin_to_update.save()

            messages.success(request, f'Admin "{admin_to_update.username}" has been updated successfully.')
        except IntegrityError:
            messages.error(request, "A user with this username or email already exists. Please use a unique value.")
        except Exception as e:
            messages.error(request, f"Failed to update admin due to an unexpected error {e}.")
        return redirect('/administrator/all-insti-admin/')
    else:
        return redirect('/administrator/all-insti-admin/')


def AdminChangeInstitutionAdminStatus(request, aid):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to perform this action.")
        return redirect('/administrator/')

    institutionadmin = get_object_or_404(CustomUser, id=aid)
    if institutionadmin.id == request.user.id:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect('/administrator/all-insti-admin/')
    try:
        with db_transaction.atomic():
            if institutionadmin.table_status:
                institutionadmin.table_status = False
                messages.warning(request, f'Admin {institutionadmin.username} of {institutionadmin.institution} has been deactivated.')
            else:
                institutionadmin.table_status = True
                messages.success(request,f'Admin {institutionadmin.username} of {institutionadmin.institution} has been activated successfully.')
            institutionadmin.save()
    except Exception as e:
        messages.error(request, f"Failed to change admin status due to an error {e}.")
    return redirect('/administrator/all-insti-admin/')


def adminDeletePermanent(request, aid):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to perform this action.")
        return redirect('/administrator/')

    admin_to_delete = get_object_or_404(CustomUser, id=aid)

    if admin_to_delete.id == request.user.id:
        messages.error(request, "You cannot delete your own account.")
        return redirect('/administrator/all-insti-admin/')

    admin_username = admin_to_delete.username
    admin_institution = admin_to_delete.institution

    try:
        with db_transaction.atomic():
            admin_to_delete.delete()
        messages.warning(request, f'Admin {admin_username} of {admin_institution} has been permanently deleted.')
    except Exception as e:
        messages.error(request, f"Failed to delete admin due to an error {e}.")
    return redirect('/administrator/all-insti-admin/')


def adminAllProject(request):
    if request.user.is_superuser:
        if not request.user.table_status:
            messages.error(request, "Your account has been deactivated by another superuser.")
            return redirect('/administrator/logout/')
        projects = Project.objects.all()
    elif request.user.is_staff:
        if not request.user.table_status or not request.user.institution.table_status:
            messages.error(request, "Your account or institution has been deactivated by a superuser.")
            return redirect('/administrator/logout/')
        projects = Project.objects.filter(created_by=request.user.institution)
    else:
        messages.error(request, "Your Don't have permission to acces this page.")
        return redirect('/administrator/')

    project_title = request.GET.get('project_title')
    project_status = request.GET.get('project_status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    amount_order = request.GET.get('amount_order')
    date_order = request.GET.get('date_order')
    target_order = request.GET.get('target_order')

    if project_title:
        projects = projects.filter(title__icontains=project_title)

    if project_status:
        if project_status == 'active':
            projects = projects.filter(table_status=True)
        elif project_status == 'closed':
            projects = projects.filter(table_status=False)
        elif project_status == 'success':
            projects = projects.filter(current_amount__gte=F('funding_goal'))

    if start_date:
        projects = projects.filter(started_at__date__gte=start_date)
    if end_date:
        projects = projects.filter(started_at__date__lte=end_date)

    if amount_order == 'asc':
        projects = projects.order_by('current_amount')
    elif amount_order == 'desc':
        projects = projects.order_by('-current_amount')
    elif target_order == 'asc':
        projects = projects.order_by('funding_goal')
    elif target_order == 'desc':
        projects = projects.order_by('-funding_goal')
    elif date_order == 'asc':
        projects = projects.order_by('closed_by')
    elif date_order == 'desc':
        projects = projects.order_by('-closed_by')
    else:
        projects = projects.order_by('-started_at')

    for p in projects:
        if p.current_amount >= p.funding_goal:
            p.validity = 'Completed'
    return render(request, "admin-all-projects.html", {'prj': projects, 'admin': request.user})


def adminAddProject(request):
    if request.method != "POST":
        return redirect('/administrator/all-project/')

    title = request.POST.get("title")
    goal = request.POST.get("goal")
    tval = request.POST.get("tvalue")
    desc = request.POST.get("desc")
    ben_fname = request.POST.get("fname")
    ben_lname = request.POST.get("lname")
    ben_phn = request.POST.get("phn")
    ben_age = request.POST.get("age")
    ben_addr = request.POST.get("addr")

    try:
        funding_goal = Decimal(goal) if goal else Decimal(0)
        tile_value = Decimal(tval) if tval else Decimal(0)
        bank_details = request.user.institution.default_bank

        with db_transaction.atomic():
            beneficiar, created = Beneficial.objects.get_or_create(first_name=ben_fname, last_name=ben_lname, phone_number=ben_phn,
                                                                   defaults={'address': ben_addr, 'age': ben_age, })

            new_project = Project(title=title, description=desc, beneficiary=beneficiar, created_by=request.user.institution,
                                  funding_goal=funding_goal, tile_value=tile_value)
            new_project.save()

            if bank_details and bank_details.upi_id:
                payee_name = f"{bank_details.account_holder_first_name} {bank_details.account_holder_last_name}"
                encoded_payee_name = urllib.parse.quote(payee_name)
                google_pay_url = f'upi://pay?pa={bank_details.upi_id}&pn={encoded_payee_name}'
                qr_img = qrcode.make(google_pay_url)
                buffer = BytesIO()
                qr_img.save(buffer, format='PNG')
                file_name = f"project_{new_project.id}_qr.png"
                new_project.qr_code.save(file_name, ContentFile(buffer.getvalue()), save=True)

        messages.success(request, "A new project has been created successfully.")
    except InvalidOperation:
        messages.error(request, "Invalid number format for funding goal or tile value.")
    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {e}")
    return redirect('/administrator/all-project/')


def adminSingleProject(request, pid):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('/administrator/')

    if not request.user.table_status:
        messages.error(request, "Your account has been deactivated by a superuser.")
        return redirect('/administrator/logout/')

    project = get_object_or_404(Project, id=pid)

    project.progress = round((project.current_amount / project.funding_goal) * 100,
                             3) if project.funding_goal > 0 else 0
    # project.validity = project.closed_by >= timezone.now()

    total_tiles_count = int(project.funding_goal // project.tile_value)

    # Retrieve all transactions for the project
    transactions = Transaction.objects.filter(project=project).select_related('tiles_bought', 'sender').order_by(
        '-transaction_time')

    # Calculate tiles and available tiles in a single pass
    sold_tiles_set = set()
    processing_tiles_set = set()

    for t in transactions:
        t.num_tiles = 0
        if t.tiles_bought and t.tiles_bought.tiles:
            tile_numbers = [int(n) for n in t.tiles_bought.tiles.split('-') if n.isdigit()]
            t.num_tiles = len(tile_numbers)
            if t.status == 'Verified':
                sold_tiles_set.update(tile_numbers)
            elif t.status == 'Unverified':
                processing_tiles_set.update(tile_numbers)

    unavailable_tiles_count = len(sold_tiles_set) + len(processing_tiles_set)
    available_tiles_count = total_tiles_count - unavailable_tiles_count

    # Re-fetch specific transactions for the template, if needed
    verified_transactions = [t for t in transactions if t.status == 'Verified']

    context = {
        'admin': request.user,
        'project': project,
        'transactions': transactions,  # This now includes all transactions with num_tiles
        'total_tiles_count': total_tiles_count,
        'available_tiles_count': available_tiles_count,
        'sold_tiles_set': sold_tiles_set,
        'processing_tiles_set': processing_tiles_set,
        'verified_transactions': verified_transactions,  # Keep this for compatibility if needed
    }

    return render(request, "admin-single-projects.html", context)


def adminUpdateProject(request, pid):
    if request.method == "POST":
        project = get_object_or_404(Project, id=pid)
        try:
            project.title = request.POST.get("title")
            project.funding_goal = request.POST.get("goal")
            project.tile_value = request.POST.get("tvalue")
            project.description = request.POST.get("desc")

            beneficiary_instance = project.beneficiary
            beneficiary_instance.first_name = request.POST.get("fname")
            beneficiary_instance.last_name = request.POST.get("lname")
            beneficiary_instance.phone_number = request.POST.get("phn")
            beneficiary_instance.age = request.POST.get("age")
            beneficiary_instance.address = request.POST.get("addr")

            beneficiary_instance.save()
            project.save()

            messages.success(request, "Project updated successfully.")
            return redirect(f'/administrator/single-project/{pid}/')
        except Exception as e:
            messages.error(request, f"An error occurred while updating the project: {e}")
            return redirect(f'/administrator/single-project/{pid}/')
    return redirect(f'/administrator/single-project/{pid}/')


def adminChangeProjectStatus(request, pid):
    if request.user.is_superuser or request.user.is_staff:
        project_instance = get_object_or_404(Project, id=pid)

        new_status = not project_instance.table_status
        project_instance.table_status = new_status
        project_instance.save()
        if new_status:
            messages.success(request, f'The project {project_instance.title} has been enabled.')
        else:
            messages.warning(request, f'The project {project_instance.title} has been disabled.')
        return redirect(f'/administrator/single-project/{pid}/')
    else:
        return redirect('/administrator/')


def adminDeleteProject(request,pid):
    if request.user.is_superuser or request.user.is_staff:
        project_instance = get_object_or_404(Project, id=pid)
        project_instance.delete()
        messages.warning(request, "A project has been deleted.")
        return redirect('/administrator/all-project/')
    else:
        return redirect('/administrator/')


def upload_project_image(request, project_id):
    if request.user.is_superuser or request.user.is_staff:
        if request.method == 'POST':
            project_instance = get_object_or_404(Project, id=project_id)
            if 'img' in request.FILES:
                uploaded_file = request.FILES['img']
                new_image = ProjectImage(
                    project=project_instance,
                    project_img=uploaded_file
                )
                new_image.save()
        return redirect(f'/administrator/single-project/{project_id}/')
    else:
        return redirect('/administrator/')


def delete_project_image(request, img_id):
    if request.user.is_superuser or request.user.is_staff:
        img = ProjectImage.objects.get(id=img_id)
        prj_id = img.project.id
        img.delete()
        return redirect(f'/administrator/single-project/{prj_id}/')
    else:
        return redirect('/administrator/')


def upload_beneficiary_image(request, prj_id):
    if request.user.is_superuser or request.user.is_staff:
        if request.method == 'POST':
            project_instance = get_object_or_404(Project, id=prj_id)
            if 'bene_img' in request.FILES:
                uploaded_img = request.FILES['bene_img']
                project_instance.beneficiary.profile_pic = uploaded_img
                project_instance.beneficiary.save()
        return redirect(f'/administrator/single-project/{prj_id}/')
    else:
        return redirect('/administrator/')


def adminUpdateBankDetails(request):
    if request.user.is_staff:
        if request.method == "POST":
            fname = request.POST.get('account_holder_first_name')
            lname = request.POST.get('account_holder_last_name')
            phn = request.POST.get('account_holder_phn_no')
            addr = request.POST.get('account_holder_address')
            bname = request.POST.get('bank_name')
            brname = request.POST.get('branch_name')
            ifcs = request.POST.get('ifsc_code')
            accno = request.POST.get('account_no')
            upi = request.POST.get('upi_id')
            if request.user.institution.default_bank:
                request.user.institution.default_bank.account_holder_first_name = fname
                request.user.institution.default_bank.account_holder_last_name = lname
                request.user.institution.default_bank.account_holder_address = addr
                request.user.institution.default_bank.account_holder_phn_no = phn
                request.user.institution.default_bank.bank_name = bname
                request.user.institution.default_bank.branch_name = brname
                request.user.institution.default_bank.ifsc_code = ifcs
                request.user.institution.default_bank.account_no = accno
                request.user.institution.default_bank.upi_id = upi
                request.user.institution.default_bank.save()
            else:
                bank_details = BankDetails.objects.create(account_holder_first_name=fname, account_holder_last_name=lname, account_holder_address=addr,
                    account_holder_phn_no=phn, bank_name=bname, branch_name=brname, ifsc_code=ifcs, account_no=accno, upi_id=upi,)
                request.user.institution.default_bank = bank_details
                request.user.institution.save()
            return redirect(request.META.get('HTTP_REFERER', '/'))
    else:
        return redirect('/administrator/')


def adminAllTransactions(request):
    if request.user.is_superuser:
        if not request.user.table_status:
            messages.error(request, "Your account has been deactivated by another superuser.")
            return redirect('/administrator/logout/')
        transactions = Transaction.objects.all()
    elif request.user.is_staff:
        if not request.user.table_status or not request.user.institution.table_status:
            messages.error(request, "Your account or institution has been deactivated by a superuser.")
            return redirect('/administrator/logout/')
        transactions = Transaction.objects.filter(project__created_by=request.user.institution)
    else:
        messages.error(request, "Your Don't have permission to access this page.")
        return redirect('/administrator/')

    tracking_id = request.GET.get('tracking_id')
    project_title = request.GET.get('project_title')
    sender_name = request.GET.get('sender_name')
    status = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    amount_order = request.GET.get('amount_order')
    tiles_order = request.GET.get('tiles_order')

    if tracking_id:
        transactions = transactions.filter(tracking_id__icontains=tracking_id)
    if project_title:
        transactions = transactions.filter(project__title__icontains=project_title)
    if sender_name:
        transactions = transactions.filter(
            Q(sender__first_name__icontains=sender_name) | Q(sender__last_name__icontains=sender_name))
    if status:
        transactions = transactions.filter(status=status)
    if start_date:
        transactions = transactions.filter(transaction_time__date__gte=start_date)
    if end_date:
        transactions = transactions.filter(transaction_time__date__lte=end_date)

    transactions = transactions.order_by('-transaction_time')

    if amount_order == 'asc':
        transactions = sorted(transactions, key=lambda t: t.amount)
    elif amount_order == 'desc':
        transactions = sorted(transactions, key=lambda t: t.amount, reverse=True)


    if tiles_order == 'asc':
        for t in transactions:
            if t.tiles_bought and t.tiles_bought.tiles:
                t.num_tiles = len(t.tiles_bought.tiles.split('-'))
            else:
                t.num_tiles = 0
        transactions = sorted(transactions, key=lambda t: t.num_tiles)
    elif tiles_order == 'desc':
        for t in transactions:
            if t.tiles_bought and t.tiles_bought.tiles:
                t.num_tiles = len(t.tiles_bought.tiles.split('-'))
            else:
                t.num_tiles = 0
        transactions = sorted(transactions, key=lambda t: t.num_tiles, reverse=True)

    for t in transactions:
        if not hasattr(t, 'num_tiles'):
            if t.tiles_bought and t.tiles_bought.tiles:
                t.num_tiles = len(t.tiles_bought.tiles.split('-'))
            else:
                t.num_tiles = 0
    return render(request, 'admin-all-transactions.html', {'admin': request.user, 'transaction': transactions})


def adminVerifyTransaction(request, tid):
    if request.user.is_superuser or request.user.is_staff:
        if not request.user.table_status:
            messages.error(request, "Your account has been deactivated by a superuser.")
            return redirect('/administrator/logout/')

        transaction = Transaction.objects.get(id=tid)
        if transaction.tiles_bought:
            transaction.num_tiles = len(transaction.tiles_bought.tiles.split('-'))
        else:
            transaction.num_tiles = 0
        screenshot = Screenshot.objects.filter(transaction=transaction).order_by('-id').first()
        return render(request, "admin-verify-transaction.html", {'admin': request.user, 'transaction': transaction, 'screenshot': screenshot})
    else:
        return redirect('/administrator/')


def adminApproveTransaction(request, tid):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('/administrator/')

    transaction = get_object_or_404(Transaction, id=tid)

    if transaction.status == "Verified":
        messages.info(request, "This transaction has already been verified.")
        return redirect('/administrator/all-transactions/')

    try:
        with db_transaction.atomic():
            new_pdf_data = generate_receipt_pdf(transaction)
            receipt, created = Receipt.objects.update_or_create(transaction=transaction,defaults={'receipt_pdf': new_pdf_data})

            transaction.status = "Verified"
            transaction.table_status = True
            transaction.tiles_bought.table_status = True

            project_instance = transaction.project
            project_instance.current_amount += transaction.amount
            if project_instance.funding_goal <= project_instance.current_amount:
                project_instance.closed_by = datetime.datetime.now()
                project_instance.table_status = False

            transaction.save()
            transaction.tiles_bought.save()
            project_instance.save()

        all_notifications_sent = True
        notification_errors = []

        noti_pref = NotificationPreference.objects.get(institution=request.user.institution)

        if noti_pref.sms_enabled:
            sms_result = sms_send_approve(transaction)
            if sms_result['status'] == 'error':
                all_notifications_sent = False
                notification_errors.append(f"SMS sending failed: {sms_result['message']}")

        if noti_pref.whatsapp_enabled:
            whatsapp_result = whatsapp_send_approve(transaction)
            if whatsapp_result['status'] == 'error':
                all_notifications_sent = False
                notification_errors.append(f"WhatsApp message failed to send: {whatsapp_result['message']}")

        if noti_pref.email_enabled:
            email_success, email_message = email_send_approve(transaction)
            if not email_success:
                all_notifications_sent = False
                notification_errors.append(f"Email sending failed: {email_message}")

        if all_notifications_sent:
            messages.success(request,f'The transaction: {transaction.tracking_id} has been approved and a receipt has been generated.')
        else:
            base_msg = "The transaction has been approved, but there were issues with some notifications."
            details_msg = " ".join(notification_errors)
            messages.warning(request, f"{base_msg} Details: {details_msg}")
    except Exception as e:
        messages.error(request, f"Failed to approve transaction: {e}")
    return redirect('/administrator/all-transactions/')


def adminRejectTransaction(request, tid):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('/administrator/')
    transaction_instance = get_object_or_404(Transaction, id=tid)
    if transaction_instance.status == "Rejected":
        messages.info(request, f'The transaction: {transaction_instance.tracking_id} is already rejected.')
        return redirect('/administrator/all-transactions/')
    try:
        with db_transaction.atomic():
            if transaction_instance.status == "Verified":
                transaction_instance.project.current_amount -= transaction_instance.amount
                transaction_instance.project.closed_by = None

            transaction_instance.status = "Rejected"
            transaction_instance.table_status = False
            transaction_instance.tiles_bought.table_status = False
            transaction_instance.project.table_status = True

            try:
                receipt_to_delete = Receipt.objects.get(transaction=transaction_instance)
                receipt_to_delete.delete()
            except Receipt.DoesNotExist:
                pass

            transaction_instance.project.save()
            transaction_instance.tiles_bought.save()
            transaction_instance.save()

        all_notifications_sent = True
        notification_errors = []
        noti_pref = NotificationPreference.objects.get(institution=request.user.institution)

        if noti_pref.sms_enabled:
            sms_result = sms_send_reject(transaction_instance)
            if sms_result['status'] == 'error':
                all_notifications_sent = False
                notification_errors.append(f"SMS sending failed: {sms_result['message']}")

        if noti_pref.whatsapp_enabled:
            whatsapp_result = whatsapp_send_reject(transaction_instance)
            if whatsapp_result['status'] == 'error':
                all_notifications_sent = False
                notification_errors.append(f"WhatsApp message failed to send: {whatsapp_result['message']}")

        if noti_pref.email_enabled:
            email_success, email_message = email_send_reject(transaction_instance)
            if not email_success:
                all_notifications_sent = False
                notification_errors.append(f"Email sending failed: {email_message}")

        if all_notifications_sent:
            messages.success(request, f'The transaction: {transaction_instance.tracking_id} has been rejected and a notification has been sent to the user.')
        else:
            base_msg = "The transaction has been rejected, but there were issues with some notifications."
            details_msg = " ".join(notification_errors)
            messages.warning(request, f"{base_msg} Details: {details_msg}")
    except Exception as e:
        messages.error(request, f"Failed to reject transaction: {e}")
    return redirect('/administrator/all-transactions/')


def adminUnverifyTransaction(request, tid):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('/administrator/')
    transaction_instance = get_object_or_404(Transaction, id=tid)
    if transaction_instance.status == "Unverified":
        messages.info(request, f'The transaction: {transaction_instance.tracking_id} is already unverified.')
        return redirect('/administrator/all-transactions/')
    try:
        with db_transaction.atomic():
            if transaction_instance.status == "Verified":
                transaction_instance.project.current_amount -= transaction_instance.amount

            transaction_instance.status = "Unverified"
            transaction_instance.table_status = True
            transaction_instance.tiles_bought.table_status = True
            transaction_instance.project.table_status = True

            try:
                receipt_to_delete = Receipt.objects.get(transaction=transaction_instance)
                receipt_to_delete.delete()
            except Receipt.DoesNotExist:
                pass

            transaction_instance.project.save()
            transaction_instance.tiles_bought.save()
            transaction_instance.save()

        all_notifications_sent = True
        notification_errors = []
        noti_pref = NotificationPreference.objects.get(institution=request.user.institution)

        if noti_pref.sms_enabled:
            sms_result = sms_send_unverify(transaction_instance)
            if sms_result['status'] == 'error':
                all_notifications_sent = False
                notification_errors.append(f"SMS sending failed: {sms_result['message']}")

        if noti_pref.whatsapp_enabled:
            whatsapp_result = whatsapp_send_unverify(transaction_instance)
            if whatsapp_result['status'] == 'error':
                all_notifications_sent = False
                notification_errors.append(f"WhatsApp message failed to send: {whatsapp_result['message']}")

        if noti_pref.whatsapp_enabled:
            email_success, email_message = email_send_unverify(transaction_instance)
            if not email_success:
                all_notifications_sent = False
                notification_errors.append(f"Email sending failed: {email_message}")

        if all_notifications_sent:
            messages.success(request, f'The transaction: {transaction_instance.tracking_id} has been unverified and a notification has been sent to the user.')
        else:
            base_msg = "The transaction has been unverified, but there were issues with some notifications."
            details_msg = " ".join(notification_errors)
            messages.warning(request, f"{base_msg} Details: {details_msg}")
    except Exception as e:
        messages.error(request, f"Failed to unverify transaction: {e}")
    return redirect('/administrator/all-transactions/')


def adminGenerateReceipts(request, t_id):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('/administrator/')
    transaction_instance = get_object_or_404(Transaction, id=t_id)
    try:
        with db_transaction.atomic():
            old_receipt = None
            try:
                old_receipt = Receipt.objects.get(transaction=transaction_instance)
            except Receipt.DoesNotExist:
                pass

            new_pdf_data = generate_receipt_pdf(transaction_instance)
            receipt, created = Receipt.objects.update_or_create(transaction=transaction_instance,defaults={'receipt_pdf': new_pdf_data})

            if not created and old_receipt and old_receipt.receipt_pdf:
                old_file_path = old_receipt.receipt_pdf.path
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)

        messages.success(request,f'A receipt for the transaction: {transaction_instance.tracking_id} has been created.')
    except Exception as e:
        messages.error(request, f"Failed to generate receipt: {e}")
    return redirect('/administrator/all-transactions/')


def adminAllReceipts(request):
    if request.user.is_superuser:
        if not request.user.table_status:
            messages.error(request, "Your account has been deactivated by another superuser.")
            return redirect('/administrator/logout/')
        receipts = Receipt.objects.all()
    elif request.user.is_staff:
        if not request.user.table_status or not request.user.institution.table_status:
            messages.error(request, "Your account or institution has been deactivated by a superuser.")
            return redirect('/administrator/logout/')
        receipts = Receipt.objects.filter(transaction__project__created_by=request.user.institution)
    else:
        messages.error(request, "Your Don't have permission to access this page.")
        return redirect('/administrator/')

    tracking_id = request.GET.get('tracking_id')
    project_title = request.GET.get('project_title')
    sender_name = request.GET.get('sender_name')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    amount_order = request.GET.get('amount_order')
    tiles_order = request.GET.get('tiles_order')

    if tracking_id:
        receipts = receipts.filter(transaction__tracking_id__icontains=tracking_id)
    if project_title:
        receipts = receipts.filter(transaction__project__title__icontains=project_title)
    if sender_name:
        receipts = receipts.filter(Q(transaction__sender__first_name__icontains=sender_name) | Q(
                transaction__sender__last_name__icontains=sender_name))
    if start_date:
        receipts = receipts.filter(transaction__transaction_time__date__gte=start_date)
    if end_date:
        receipts = receipts.filter(transaction__transaction_time__date__lte=end_date)

    if amount_order or tiles_order:
        if tiles_order:
            for r in receipts:
                if r.transaction.tiles_bought and r.transaction.tiles_bought.tiles:
                    r.tile_count = len(r.transaction.tiles_bought.tiles.split('-'))
                else:
                    r.tile_count = 0

            if tiles_order == 'asc':
                receipts = sorted(receipts, key=lambda r: r.tile_count)
            elif tiles_order == 'desc':
                receipts = sorted(receipts, key=lambda r: r.tile_count, reverse=True)

        elif amount_order == 'asc':
            receipts = receipts.order_by('transaction__amount')
        elif amount_order == 'desc':
            receipts = receipts.order_by('-transaction__amount')
    else:
        receipts = receipts.order_by('-transaction__transaction_time')

    for r in receipts:
        if not hasattr(r, 'tile_count'):
            if r.transaction.tiles_bought and r.transaction.tiles_bought.tiles:
                r.tile_count = len(r.transaction.tiles_bought.tiles.split('-'))
            else:
                r.tile_count = 0
    return render(request, 'admin-all-receipts.html', {'admin': request.user, 'rec': receipts})


def adminSendReciept(request, r_id):
    try:
        receipt = get_object_or_404(Receipt, id=r_id)

        all_notifications_sent = True
        notification_errors = []
        noti_pref = NotificationPreference.objects.get(institution=request.user.institution)

        if noti_pref.sms_enabled:
            sms_result = sms_send_approve(receipt.transaction)
            if sms_result['status'] == 'error':
                all_notifications_sent = False
                notification_errors.append(f"SMS sending failed: {sms_result['message']}")

        if noti_pref.whatsapp_enabled:
            whatsapp_result = whatsapp_send_approve(receipt.transaction)
            if whatsapp_result['status'] == 'error':
                all_notifications_sent = False
                notification_errors.append(f"WhatsApp message failed to send: {whatsapp_result['message']}")

        if noti_pref.email_enabled:
            email_success, email_message = email_send_approve(receipt.transaction)
            if not email_success:
                all_notifications_sent = False
                notification_errors.append(f"Email sending failed: {email_message}")

        if all_notifications_sent:
            messages.success(request,f'A receipt has been successfully sent to {receipt.transaction.sender.first_name} {receipt.transaction.sender.last_name}.')
        else:
            base_msg = f"Failed to send all confirmation messages for the receipt to {receipt.transaction.sender.first_name} {receipt.transaction.sender.last_name}."
            details_msg = " ".join(notification_errors)
            messages.warning(request, f"{base_msg} Details: {details_msg}")
    except Exception as e:
        messages.error(request, f"An unexpected error occurred while sending the receipt: {e}.")
    return redirect('/administrator/all-receipts/')


def adminAllReports(request):
    completion_conditions = Q(closed_by__isnull=False) & Q(current_amount__gte=F('funding_goal'))

    if request.user.is_superuser:
        if not request.user.table_status:
            messages.error(request, "Your account has been deactivated by another superuser.")
            return redirect('/administrator/logout/')
        project = (Project.objects.filter(completion_conditions)
                   .annotate(tra=Count('transaction', distinct=True)).order_by('-closed_by'))
        reports = Reports.objects.all().select_related('project')

    elif request.user.is_staff:
        if not request.user.table_status or not request.user.institution.table_status:
            messages.error(request, "Your account or institution has been deactivated by a superuser.")
            return redirect('/administrator/logout/')
        project = (Project.objects.filter(completion_conditions, created_by=request.user.institution,)
                   .annotate(tra=Count('transaction', distinct=True)).order_by('-closed_by'))
        reports = Reports.objects.filter(project__created_by=request.user.institution).select_related('project')

    else:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('/administrator/')

    for p in project:
        p.tiles = (p.funding_goal / p.tile_value)
        p.tra = Transaction.objects.filter(project = p).count()
    return render(request, 'admin-all-reports.html', {'admin': request.user, 'project': project, 'reports': reports})


def adminGenerateReports(request, p_id):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('/administrator/')
    project_instance = get_object_or_404(Project, id=p_id)
    try:
        with db_transaction.atomic():
            old_report = None
            try:
                old_report = Reports.objects.get(project=project_instance)
            except Reports.DoesNotExist:
                pass

            new_pdf_data = generate_report_pdf(project_instance)
            report, created = Reports.objects.update_or_create(project=project_instance,defaults={'report_pdf': new_pdf_data})

            if not created and old_report and old_report.report_pdf:
                old_file_path = old_report.report_pdf.path
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)

        messages.success(request,f'A report for the project: {project_instance.title} has been created.')
    except Exception as e:
        messages.error(request, f"Failed to generate report: {e}")
    return redirect('/administrator/all-reports/')


def adminContactMessage(request):
    if request.user.is_superuser:
        if not request.user.table_status:
            messages.error(request, "Your account has been deactivated by another superuser.")
            return redirect('/administrator/logout/')
        msg = ContactMessage.objects.all().order_by('-sent_time')
    elif request.user.is_staff:
        if not request.user.table_status or not request.user.institution.table_status:
            messages.error(request, "Your account or institution has been deactivated by a superuser.")
            return redirect('/administrator/logout/')
        msg = ContactMessage.objects.filter(ins=request.user.institution).order_by('-sent_time')
    else:
        messages.error(request, "Your Don't have permission to access this page.")
        return redirect('/administrator/')

    for m in msg:
        m.has_replied = MessageReply.objects.filter(message=m).exists()
    return render(request, 'admin-all-contact-message.html', {'admin':request.user,'contact_messages': msg})


def adminMessageReply(request, msg_id):
    if request.method == 'POST':
        reply = request.POST.get('reply_message')
        try:
            with db_transaction.atomic():
                original_message = ContactMessage.objects.get(pk=msg_id)
                new_reply = MessageReply.objects.create(message=original_message, reply=reply)

                all_notifications_sent = True
                notification_errors = []
                noti_pref = NotificationPreference.objects.get(institution=request.user.institution)

                if noti_pref.sms_enabled:
                    sms_result = sms_send_response(new_reply)
                    if sms_result['status'] == 'error':
                        all_notifications_sent = False
                        notification_errors.append(f"SMS sending failed: {sms_result['message']}")

                if noti_pref.sms_enabled:
                    whatsapp_result = whatsapp_send_response(new_reply)
                    if whatsapp_result['status'] == 'error':
                        all_notifications_sent = False
                        notification_errors.append(f"WhatsApp message failed to send: {whatsapp_result['message']}")

                email_success, email_message = email_send_response(new_reply)
                if not email_success:
                    all_notifications_sent = False
                    notification_errors.append(f"Email sending failed: {email_message}")

                if all_notifications_sent:
                    messages.success(request,f'Reply successfully sent to {original_message.first_name} {original_message.last_name}.')
                else:
                    base_msg = f"Reply was saved, but failed to send all notifications to {original_message.first_name} {original_message.last_name}."
                    details_msg = " ".join(notification_errors)
                    messages.warning(request, f"{base_msg} Details: {details_msg}")
        except ContactMessage.DoesNotExist:
            messages.error(request, "The original message could not be found.")
        except IntegrityError as e:
            messages.error(request, f"A database error occurred: {e}.")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred while sending the reply: {e}.")
    return redirect('/administrator/contact-message/')