from adminModule.utils import generate_receipt_pdf, whatsapp_send_approve, email_send_approve, sms_send_approve, \
    email_send_reject, sms_send_reject, whatsapp_send_reject, email_send_unverify, sms_send_unverify, \
    whatsapp_send_unverify
from adminModule.models import BankDetails, Beneficial, Project, Institution, ProjectImage, CustomUser
from django.shortcuts import render, redirect, get_object_or_404
from userModule.models import Transaction, Receipt, Screenshot
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from django.core.files.base import ContentFile
from decimal import Decimal, InvalidOperation
from django.db import IntegrityError
from django.contrib import messages
from django.utils import timezone
from django.db.models import F
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
        closed_prj = Project.objects.filter(closing_date__lte=timezone.now()).count()
        completed_prj = Project.objects.filter(current_amount__gte=F('funding_goal')).count()
        failed_prj = Project.objects.filter(closing_date__lte=timezone.now(), current_amount__lt=F('funding_goal')).count()

        all_tra = Transaction.objects.all().count()
        ver_tra = Transaction.objects.filter(status='Verified').count()
        unver_tra = Transaction.objects.filter(status='Unverified').count()
        rej_tra = Transaction.objects.filter(status='Rejected').count()

        latest_projects = Project.objects.filter(closing_date__gte=timezone.now(),current_amount__lt=F('funding_goal')).order_by('-created_at')[:5]

    elif request.user.is_staff:
        if not request.user.table_status or not request.user.institution.table_status:
            messages.error(request, "Your account or institution has been deactivated by the superuser.")
            return redirect('/administrator/logout/')

        all_prj = Project.objects.filter(created_by=request.user).count()
        closed_prj = Project.objects.filter(created_by=request.user, closing_date__lte=timezone.now()).count()
        completed_prj = Project.objects.filter(created_by=request.user, current_amount__gte=F('funding_goal')).count()
        failed_prj = Project.objects.filter(created_by=request.user, closing_date__lte=timezone.now(),current_amount__lt=F('funding_goal')).count()

        all_tra = Transaction.objects.filter(project__created_by=request.user).count()
        ver_tra = Transaction.objects.filter(project__created_by=request.user, status='Verified').count()
        unver_tra = Transaction.objects.filter(project__created_by=request.user, status='Unverified').count()
        rej_tra = Transaction.objects.filter(project__created_by=request.user, status='Rejected').count()

        latest_projects = Project.objects.filter(created_by=request.user, closing_date__gte=timezone.now(), current_amount__lt=F('funding_goal')).order_by('-created_at')[:5]

    else:
        return redirect('/administrator/')

    for p in latest_projects:
        if p.closing_date < timezone.now():
            p.validity = False

    context = {
        'all_prj': all_prj, 'cls_prj': closed_prj, 'lst_prj': latest_projects, 'cmp_prj': completed_prj, 'fail_prj': failed_prj,
        'all_tra': all_tra, 'ver_tra': ver_tra, 'unver_tra': unver_tra, 'rej_tra': rej_tra,}

    return render(request, "admin-dashboard.html", {'admin': request.user,'context': context})


def adminLogOut(request):
    logout(request)
    messages.warning(request, "You have been logged out successfully.")
    return redirect('/administrator/')


# Profile page of the logged admin
def adminProfile(request):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('/administrator/')
    if not request.user.table_status or (request.user.is_staff and not request.user.institution.table_status):
        messages.error(request, "Your account or institution has been deactivated by the superuser.")
        return redirect('/administrator/logout/')

    return render(request, 'admin-profile.html', {'admin': request.user})


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


# Superuser listing all Institutions and adding new Institutions
def adminAllInstitution(request):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to perform this action.")
        return redirect('/administrator/')

    if not request.user.table_status:
        messages.error(request, "Your account has been deactivated by another superuser.")
        return redirect('/administrator/logout/')

    inst = Institution.objects.all()
    if request.method == "POST":
        inst_name = request.POST.get('inst_name')
        inst_email = request.POST.get('inst_email')
        inst_app_pwd = request.POST.get('inst_app_pwd')
        inst_phn = request.POST.get('inst_phn')
        inst_address = request.POST.get('inst_address')

        try:
            with db_transaction.atomic():
                new_inst = Institution(institution_name=inst_name,address=inst_address,phn=inst_phn,email=inst_email,email_app_password=inst_app_pwd)
                new_inst.save()
            messages.success(request, f'Registered {inst_name} Successfully.')
        except IntegrityError as e:
            if 'email' in str(e).lower():
                messages.error(request, "Registration failed: An institution with this email already exists.")
            else:
                messages.error(request,f"Registration failed due to a database integrity error {e}. Please check your inputs.")
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
    if request.user.is_superuser:
        if not request.user.table_status:
            messages.error(request, "Your account has been deactivated by another superuser.")
            return redirect('/administrator/logout/')
        inst = Institution.objects.all()
        administrators = CustomUser.objects.filter(is_staff=True)
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
                CustomUser.objects.create_user(first_name=firstname, last_name=lastname, email=em, institution=ins, username=usr, is_staff = True, phn_no=phn, password=pwd)
                messages.success(request, f'Registered new admin {firstname} {lastname} for {ins.institution_name}.')
                return redirect('/administrator/all-insti-admin/')
            except IntegrityError:
                return redirect('/administrator/all-insti-admin/')
        return render(request,"admin-all-insti-admin.html", {'admin': request.user, 'inst':inst, 'administrators':administrators})
    else:
        return redirect('/administrator/')


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
        prj = Project.objects.all()
    elif request.user.is_staff:
        if not request.user.table_status:
            messages.error(request, "Your account has been deactivated by a superuser.")
            return redirect('/administrator/logout/')
        prj = Project.objects.filter(created_by = request.user)
    else:
        return redirect('/administrator/')

    for p in prj:
        if p.closing_date < timezone.now():
            p.validity = False
    return render(request, "admin-all-projects.html",{'prj':prj, 'admin': request.user})


def adminAddProject(request):
    if request.method != "POST":
        return redirect('/administrator/all-project/')

    title = request.POST.get("title")
    goal = request.POST.get("goal")
    tval = request.POST.get("tvalue")
    desc = request.POST.get("desc")
    clsdate_str = request.POST.get("clsdate")
    ben_fname = request.POST.get("fname")
    ben_lname = request.POST.get("lname")
    ben_phn = request.POST.get("phn")
    ben_age = request.POST.get("age")
    ben_addr = request.POST.get("addr")

    try:
        naive_clsdate = datetime.datetime.strptime(clsdate_str, '%Y-%m-%dT%H:%M')
        aware_clsdate = timezone.make_aware(naive_clsdate)
        funding_goal = Decimal(goal) if goal else Decimal(0)
        tile_value = Decimal(tval) if tval else Decimal(0)
        bank_details = request.user.default_bank

        with db_transaction.atomic():
            beneficiar, created = Beneficial.objects.get_or_create(first_name=ben_fname, last_name=ben_lname, phone_number=ben_phn,
                                                                   defaults={'address': ben_addr, 'age': ben_age, })

            new_project = Project(title=title, description=desc, beneficiary=beneficiar, created_by=request.user,
                                  funding_goal=funding_goal, tile_value=tile_value, closing_date=aware_clsdate,bank_details=bank_details)
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
    if request.user.is_superuser or request.user.is_staff:
        if not request.user.table_status:
            messages.error(request, "Your account has been deactivated by a superuser.")
            return redirect('/administrator/logout/')

        project = get_object_or_404(Project.objects.select_related('beneficiary'), id=pid)

        if project.closing_date < timezone.now():
            project.validity = False

        total_tiles_count = int(project.funding_goal // project.tile_value)
        tile_range = range(1, total_tiles_count + 1)

        verified_transactions = Transaction.objects.filter(project=project, status='Verified').select_related('tiles_bought')
        processing_transactions = Transaction.objects.filter(project=project, status='Unverified').select_related('tiles_bought')

        sold_tiles_set = set()
        for t in verified_transactions:
            if t.tiles_bought and t.tiles_bought.tiles:
                sold_tiles_set.update([int(n) for n in t.tiles_bought.tiles.split('-') if n.isdigit()])

        processing_tiles_set = set()
        for t in processing_transactions:
            if t.tiles_bought and t.tiles_bought.tiles:
                processing_tiles_set.update([int(n) for n in t.tiles_bought.tiles.split('-') if n.isdigit()])

        unavailable_tiles_count = len(sold_tiles_set) + len(processing_tiles_set)
        available_tiles_count = total_tiles_count - unavailable_tiles_count

        return render(request, "admin-single-projects.html", {'admin': request.user,'project': project,'t_range': tile_range,
                                                              'total_tiles_count': total_tiles_count,'available_tiles_count': available_tiles_count,
                                                              'processing_tiles_set': processing_tiles_set,'sold_tiles_set': sold_tiles_set,'transaction': verified_transactions})
    else:
        return redirect('/administrator/')


def adminUpdateProject(request, pid):
    if request.method == "POST":
        project = get_object_or_404(Project, id=pid)
        try:
            project.title = request.POST.get("title")
            project.funding_goal = request.POST.get("goal")
            project.tile_value = request.POST.get("tvalue")
            project.description = request.POST.get("desc")
            project.closing_date = request.POST.get("clsdate")

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
    if request.user.is_superuser or request.user.is_staff:
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
            if request.user.default_bank:
                request.user.default_bank.account_holder_first_name = fname
                request.user.default_bank.account_holder_last_name = lname
                request.user.default_bank.account_holder_address = addr
                request.user.default_bank.account_holder_phn_no = phn
                request.user.default_bank.bank_name = bname
                request.user.default_bank.branch_name = brname
                request.user.default_bank.ifsc_code = ifcs
                request.user.default_bank.account_no = accno
                request.user.default_bank.upi_id = upi
                request.user.default_bank.save()
            else:
                bank_details = BankDetails.objects.create(account_holder_first_name=fname, account_holder_last_name=lname, account_holder_address=addr,
                    account_holder_phn_no=phn, bank_name=bname, branch_name=brname, ifsc_code=ifcs, account_no=accno, upi_id=upi,)
                request.user.default_bank = bank_details
                request.user.save()
            return redirect(request.META.get('HTTP_REFERER', '/'))
    else:
        return redirect('/administrator/')


def adminAllTransactions(request):
    if request.user.is_superuser:
        if not request.user.table_status:
            messages.error(request, "Your account has been deactivated by another superuser.")
            return redirect('/administrator/logout/')
        transaction_filtered = Transaction.objects.all().order_by('-transaction_time')
    elif request.user.is_staff:
        if not request.user.table_status:
            messages.error(request, "Your account has been deactivated by a superuser.")
            return redirect('/administrator/logout/')
        transaction_filtered = Transaction.objects.filter(project__created_by=request.user).order_by('-transaction_time')
    else:
        return redirect('/administrator/')

    for t in transaction_filtered:
        if t.tiles_bought:
            t.num_tiles = len(t.tiles_bought.tiles.split('-'))
        else:
            t.num_tiles = 0
    return render(request, 'admin-all-transactions.html', {'admin':request.user, 'transaction':transaction_filtered})


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
                project_instance.table_status = False

            transaction.save()
            transaction.tiles_bought.save()
            project_instance.save()

        email_success, email_message = email_send_approve(transaction)
        # sms_result = sms_send_approve(transaction)
        whatsapp_result = whatsapp_send_approve(transaction)

        all_notifications_sent = True
        notification_errors = []

        # if sms_result['status'] == 'error':
        #     all_notifications_sent = False
        #     notification_errors.append(f"SMS sending failed: {sms_result['message']}")

        if whatsapp_result['status'] == 'error':
            all_notifications_sent = False
            notification_errors.append(f"WhatsApp message failed to send: {whatsapp_result['message']}")

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

        email_success, email_message = email_send_reject(transaction_instance)
        # sms_result = sms_send_reject(transaction_instance)
        whatsapp_result = whatsapp_send_reject(transaction_instance)

        all_notifications_sent = True
        notification_errors = []

        # if sms_result['status'] == 'error':
        #     all_notifications_sent = False
        #     notification_errors.append(f"SMS sending failed: {sms_result['message']}")

        if whatsapp_result['status'] == 'error':
            all_notifications_sent = False
            notification_errors.append(f"WhatsApp message failed to send: {whatsapp_result['message']}")

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

        email_success, email_message = email_send_unverify(transaction_instance)
        # sms_result = sms_send_unverify(transaction_instance)
        whatsapp_result = whatsapp_send_unverify(transaction_instance)

        all_notifications_sent = True
        notification_errors = []

        # if sms_result['status'] == 'error':
        #     all_notifications_sent = False
        #     notification_errors.append(f"SMS sending failed: {sms_result['message']}")

        if whatsapp_result['status'] == 'error':
            all_notifications_sent = False
            notification_errors.append(f"WhatsApp message failed to send: {whatsapp_result['message']}")

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
        if not request.user.table_status:
            messages.error(request, "Your account has been deactivated by a superuser.")
            return redirect('/administrator/logout/')
        receipts = Receipt.objects.filter(transaction__project__created_by=request.user)
    else:
        return redirect('/administrator/')

    for r in receipts:
        if r.transaction.tiles_bought and r.transaction.tiles_bought.tiles:
            r.tile_count = len(r.transaction.tiles_bought.tiles.split('-'))
        else:
            r.tile_count = 0
    return render(request, 'admin-all-receipts.html', {'admin': request.user,'rec': receipts})


def adminSendReciept(request, r_id):
    try:
        receipt = get_object_or_404(Receipt, id=r_id)

        # sms_result = sms_send_approve(receipt.transaction)
        email_success, email_message = email_send_approve(receipt.transaction)
        whatsapp_result = whatsapp_send_approve(receipt.transaction)

        all_notifications_sent = True
        notification_errors = []

        # if sms_result['status'] == 'error':
        #     all_notifications_sent = False
        #     notification_errors.append(f"SMS sending failed: {sms_result['message']}")

        if whatsapp_result['status'] == 'error':
            all_notifications_sent = False
            notification_errors.append(f"WhatsApp message failed to send: {whatsapp_result['message']}")

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