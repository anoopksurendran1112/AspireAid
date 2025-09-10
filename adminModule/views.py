from adminModule.models import BankDetails, Beneficial, Project, Institution, ProjectImage, CustomUser
from adminModule.utils import generate_receipt_pdf, whatsapp_send_approve, email_send_approve
from django.shortcuts import render, redirect, get_object_or_404
from userModule.models import Transaction, Receipt, Screenshot
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from decimal import Decimal, InvalidOperation
from django.db import IntegrityError
from django.contrib import messages
from django.utils import timezone
from django.db.models import F
from io import BytesIO
import qrcode
import urllib


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
    if request.user.is_superuser or request.user.is_staff:
        return render(request, 'admin-profile.html',{'admin': request.user})
    else:
        return redirect('/administrator/')


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
    if request.user.is_superuser:
        inst= Institution.objects.all()
        if request.method == "POST":
            inst_name = request.POST.get('inst_name')
            inst_email = request.POST.get('inst_email')
            inst_app_pwd = request.POST.get('inst_app_pwd')
            inst_phn = request.POST.get('inst_phn')
            inst_address = request.POST.get('inst_address')
            new_inst = Institution(institution_name=inst_name, address=inst_address, phn=inst_phn, email=inst_email, email_app_password=inst_app_pwd)
            new_inst.save()
            messages.success(request, f'Registered {inst_name} Successfully.')
            return redirect('/administrator/all-institution/')
        return render(request,"admin-all-institution.html", {'admin': request.user, 'institutions': inst})
    else:
        return redirect('/administrator/')


# Superuser Updating existing Institutions
def adminUpdateInstitution(request,iid):
    if request.user.is_superuser:
        institution = get_object_or_404(Institution, id=iid)
        institution_name = institution.institution_name

        messages.success(request, f'Institution {institution_name} has been Updated successfully.')
        return redirect('/administrator/all-institution/')
    else:
        return redirect('/administrator/')


# Superuser Deleting existing Institutions
def adminDeleteInstitution(request,iid):
    if request.user.is_superuser:
        institution = get_object_or_404(Institution, id=iid)
        institution_name = institution.institution_name
        institution.delete()
        messages.warning(request, f'Institution {institution_name} has been deleted successfully.')
        return redirect('/administrator/all-institution/')
    else:
        return redirect('/administrator/')


# Superuser listing all Institution's admins and adding new admin
def adminAllInstiAdmin(request):
    if request.user.is_superuser:
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
def adminUpdateAdmin(request,aid):
    if request.user.is_superuser:
        admin_to_update  = get_object_or_404(CustomUser, id=aid)
        if request.method == 'POST':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            inst_id = request.POST.get('inst_name')
            phn_no = request.POST.get('phn_no')

            print(request)

            messages.success(request, f'Admin {first_name} {last_name} has been Updated successfully.')
        return redirect('/administrator/all-institution/')
    else:
        return redirect('/administrator/')


def adminAllProject(request):
    if request.user.is_superuser:
        prj = Project.objects.all()
    elif request.user.is_staff:
        prj = Project.objects.filter(created_by = request.user)
        if request.method == "POST":
            title = request.POST.get("title")
            goal = request.POST.get("goal")
            tval = request.POST.get("tvalue")
            desc = request.POST.get("desc")
            clsdate = request.POST.get("clsdate")

            ben_fname = request.POST.get("fname")
            ben_lname = request.POST.get("lname")
            ben_phn = request.POST.get("phn")
            ben_age = request.POST.get("age")
            ben_addr = request.POST.get("addr")

            try:
                funding_goal = Decimal(goal) if goal else Decimal(0)
                tile_value = Decimal(tval) if tval else Decimal(0)
            except InvalidOperation:
                messages.error(request, "Invalid number format for funding goal or tile value.")
                return redirect('/administrator/all-project/')

            beneficiar, created = Beneficial.objects.get_or_create(first_name=ben_fname, last_name=ben_lname, phone_number=ben_phn,
                defaults={'address': ben_addr, 'age': ben_age,})
            bank_details = request.user.default_bank

            new_project = Project(title=title, description=desc, beneficiary=beneficiar, created_by=request.user, funding_goal=funding_goal, tile_value=tile_value, closing_date=clsdate, bank_details=bank_details)
            new_project.save()

            upi = bank_details.upi_id if bank_details else None
            if upi:
                payee_name = f"{new_project.bank_details.account_holder_first_name} {new_project.bank_details.account_holder_first_name}"
                encoded_payee_name = urllib.parse.quote(payee_name)

                google_pay_url = f'upi://pay?pa={upi}&pn={encoded_payee_name}'

                qr_img = qrcode.make(google_pay_url)
                buffer = BytesIO()
                qr_img.save(buffer, format='PNG')
                file_name = f"project_{new_project.id}_qr.png"
                new_project.qr_code.save(file_name, ContentFile(buffer.getvalue()), save=True)

            messages.success(request, "A new project has been created successfully.")
            return redirect('/administrator/all-project/')
    else:
        return redirect('/administrator/')
    for p in prj:
        if p.closing_date < timezone.now():
            p.validity = False
    return render(request, "admin-all-projects.html",{'prj':prj, 'admin': request.user})


def adminSingleProject(request, pid):
    if request.user.is_superuser or request.user.is_staff:
        project = get_object_or_404(Project, id=pid)
        if project.closing_date < timezone.now():
            project.validity = False
        tile_range = range(1, int(project.funding_goal // project.tile_value) + 1)

        # Separating bought tiles based on the transaction status for displaying with color
        verified_transactions = Transaction.objects.filter(project=project, status='Verified',
                                                           tiles_bought__table_status=True)
        processing_transactions = Transaction.objects.filter(project=project, status='Unverified',
                                                             tiles_bought__table_status=True)
        sold_tiles_list = []
        processing_tiles_list = []

        sold_tiles_list_of_strings = verified_transactions.values_list('tiles_bought__tiles', flat=True)
        processing_tiles_list_of_strings = processing_transactions.values_list('tiles_bought__tiles', flat=True)

        for tiles_str in sold_tiles_list_of_strings:
            if tiles_str:
                sold_tiles_list.extend([int(t) for t in tiles_str.split('-') if t.isdigit()])

        for tiles_str in processing_tiles_list_of_strings:
            if tiles_str:
                processing_tiles_list.extend([int(t) for t in tiles_str.split('-') if t.isdigit()])

        processing_tiles_set = set(processing_tiles_list)
        sold_tiles_set = set(sold_tiles_list)

        transaction_filtered = Transaction.objects.filter(project=project)
        for t in transaction_filtered:
            if t.tiles_bought:
                t.num_tiles = len(t.tiles_bought.tiles.split('-'))
            else:
                t.num_tiles = 0

        if request.method == "POST":
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

            return redirect(f'/administrator/single-project/{pid}/')
        return render(request,"admin-single-projects.html", { 'admin':request.user, 'project': project, 't_range': tile_range,
                                                              'processing_tiles_set': processing_tiles_set, 'sold_tiles_set': sold_tiles_set, 'transaction':transaction_filtered})
    else:
        return redirect('/administrator/')


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
        transaction_filtered = Transaction.objects.all().order_by('-transaction_time')
    elif request.user.is_staff:
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
    if request.user.is_superuser or request.user.is_staff:
        transaction = Transaction.objects.get(id=tid)
        try:
            if transaction.status != "Verified":

                # Update transaction status
                transaction.status = "Verified"
                transaction.table_status = True
                transaction.tiles_bought.table_status = True

                # Update project amount and status
                project_instance = transaction.project
                project_instance.current_amount += transaction.amount
                if project_instance.funding_goal <= project_instance.current_amount:
                    project_instance.table_status = False

                # Save all changes inside the atomic block
                transaction.save()
                project_instance.save()

                email_send_approve(transaction)
                whatsapp_send_approve(request,transaction)

                messages.success(request, f'The transaction: {transaction.tracking_id} has been approved.')
            else:
                messages.info(request, "This transaction has already been verified.")
        except Exception as e:
            print(f"An error occurred: {e}")
            messages.error(request, f"Failed to approve transaction: {e}")
            return redirect('/administrator/all-transactions/')

        return redirect('/administrator/all-transactions/')
    else:
        return redirect('/administrator/')


def adminRejectTransaction(request, tid):
    if request.user.is_superuser or request.user.is_staff:
        transaction = Transaction.objects.get(id=tid)
        if transaction.status != "Rejected":
            if transaction.status == "Verified":
                transaction.project.current_amount -= transaction.amount
            transaction.status = "Rejected"
            transaction.table_status = False
            transaction.tiles_bought.table_status = False
            transaction.project.table_status = True
            transaction.project.save()
            transaction.save()
            messages.error(request, f'The transaction: {transaction.tracking_id} has been rejected.')
        return redirect('/administrator/all-transactions/')
    else:
        return redirect('/administrator/')


def adminUnverifyTransaction(request, tid):
    if request.user.is_superuser or request.user.is_staff:
        transaction = Transaction.objects.get(id=tid)
        if transaction.status != "Unverified":
            if transaction.status == "Verified":
                transaction.project.current_amount -= transaction.amount
            transaction.status = "Unverified"
            transaction.table_status = True
            transaction.tiles_bought.table_status = True
            transaction.project.table_status = True
            transaction.project.save()
            transaction.save()
            messages.warning(request, f'The transaction: {transaction.tracking_id} has been unverified.')
        return redirect('/administrator/all-transactions/')
    else:
        return redirect('/administrator/')


def adminGenerateReceipts(request, t_id):
    if request.user.is_superuser or request.user.is_staff:
        transaction_instance = get_object_or_404(Transaction, id=t_id)

        receipt, created = Receipt.objects.update_or_create(
            transaction=transaction_instance,
            defaults={'receipt_pdf': generate_receipt_pdf(transaction_instance)}
        )
        messages.success(request, f'A receipt for the transaction: {transaction_instance.tracking_id} has been created.')
        return redirect('/administrator/all-transactions/')
    else:
        return redirect('/administrator/')


def adminAllReceipts(request):
    if request.user.is_superuser:
        receipts = Receipt.objects.all()
    elif request.user.is_staff:
        receipts = Receipt.objects.filter(transaction__project__created_by=request.user)
    else:
        return redirect('/administrator/')
    for r in receipts:
        if r.transaction.tiles_bought and r.transaction.tiles_bought.tiles:
            r.tile_count = len(r.transaction.tiles_bought.tiles.split('-'))
        else:
            r.tile_count = 0
    return render(request, 'admin-all-receipts.html', {'admin': request.user,'rec': receipts})