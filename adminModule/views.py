from adminModule.models import BankDetails, Beneficial, Project, Institution, ProjectImage
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from userModule.models import CustomUser
from django.contrib.auth import logout
from django.db import IntegrityError
from django.utils import timezone
from django.db.models import Q
from io import BytesIO
import qrcode
import urllib


# Create your views here.
@login_required(login_url='/')
def adminDashboard(request):
    if request.user.is_superuser or request.user.is_staff:
        all_prj = Project.objects.filter(created_by=request.user).count()
        cls_prj = Project.objects.filter(created_by=request.user, closing_date__lte=timezone.now()).count()
        latest_projects = Project.objects.filter(created_by=request.user).order_by('-created_at')[:5]
        context = {
            'all_prj': all_prj,
            'cls_prj': cls_prj,
            'lst_prj': latest_projects,
        }
        return render(request, "admin-dashboard.html", {'admin':request.user, 'context': context})
    else:
        return redirect('/')


def adminLogOut(request):
    logout(request)
    return redirect('/')


def adminAllInstitution(request):
    if request.user.is_superuser:
        inst= Institution.objects.all()
        if request.method == "POST":
            inst_name = request.POST.get('inst_name')
            inst_email = request.POST.get('inst_email')
            inst_phn = request.POST.get('inst_phn')
            inst_address = request.POST.get('inst_address')
            new_inst = Institution(institution_name=inst_name, address=inst_address, phn=inst_phn, email=inst_email)
            new_inst.save()
            return redirect('/administrator/all-institution/')
        return render(request,"admin-all-institution.html", {'admin': request.user, 'institutions': inst})
    else:
        return redirect('/')


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
                return redirect('/administrator/all-insti-admin/')
            except IntegrityError:
                return redirect('/administrator/all-insti-admin/')
        return render(request,"admin-all-insti-admin.html", {'admin': request.user, 'inst':inst, 'administrators':administrators})
    else:
        return redirect('/')


def adminAllProject(request):
    if request.user.is_superuser or request.user.is_staff:
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

            beneficiar, created = Beneficial.objects.get_or_create(first_name=ben_fname, last_name=ben_lname, phone_number=ben_phn,
                defaults={'address': ben_addr, 'age': ben_age,})
            bank_details = request.user.default_bank

            new_project = Project(title=title, description=desc, beneficiary=beneficiar, created_by=request.user, funding_goal=goal, tile_value=tval, closing_date=clsdate, bank_details=bank_details)
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

            return redirect('/administrator/all-project/')
        return render(request, "admin-all-projects.html",{'prj':prj, 'admin': request.user})
    else:
        return redirect('/')


def adminSingleProject(request, pid):
    if request.user.is_superuser or request.user.is_staff:
        project = get_object_or_404(Project, id=pid)
        tile_range = range(1, int(project.funding_goal // project.tile_value) + 1)

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
        return render(request,"admin-single-projects.html", { 'admin':request.user, 'project': project, 't_range': tile_range})
    else:
        return redirect('/')


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
        return redirect('/')


def adminAllBankDetails(request):
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
            try:
                existing_bank_details = BankDetails.objects.filter(Q(ifsc_code=ifcs, account_no=accno) | Q(upi_id=upi)).first()
                if existing_bank_details:
                    bank_details = existing_bank_details
                    bank_details.account_holder_first_name = fname
                    bank_details.account_holder_last_name = lname
                    bank_details.account_holder_address = addr
                    bank_details.account_holder_phn_no = phn
                    bank_details.bank_name = bname
                    bank_details.branch_name = brname
                    bank_details.ifsc_code = ifcs
                    bank_details.account_no = accno
                    bank_details.upi_id = upi
                    bank_details.save()
                else:
                    bank_details = BankDetails.objects.create(account_holder_first_name=fname, account_holder_last_name=lname, account_holder_address=addr,
                        account_holder_phn_no=phn, bank_name=bname, branch_name=brname, ifsc_code=ifcs, account_no=accno, upi_id=upi,)
                request.user.default_bank = bank_details
                request.user.save()
            except Exception as e:
               print(f'An error occurred: {e}')
            return redirect('/administrator/all-bank/')
        return render(request, "admin-all-bank-details.html",{'admin': request.user})
    else:
        return redirect('/')


def delete_project_image(request, img_id):
    if request.user.is_superuser or request.user.is_staff:
        img = ProjectImage.objects.get(id=img_id)
        prj_id = img.project.id
        img.delete()
        return redirect(f'/administrator/single-project/{prj_id}/')
    else:
        return redirect('/')