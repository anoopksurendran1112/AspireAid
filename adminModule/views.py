from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect
from adminModule.models import BankDetails, Beneficial, Project, Institution
from userModule.models import CustomUser
from django.db import IntegrityError


# Create your views here.
@login_required(login_url='/sign-in/')
def adminDashboard(request):
    if request.user.is_superuser or request.user.is_staff:
        return render(request, "admin-dashboard.html", {'admin':request.user})
    else:
        return redirect('/sign-in/')


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
        return redirect('/sign-in/')


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
        return redirect('/sign-in/')


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

            acc_type = request.POST.get("acc_type")
            acc_fname = request.POST.get("account_holder_first_name")
            acc_lname = request.POST.get("account_holder_last_name")
            acc_phn= request.POST.get("account_holder_phn_no")
            acc_addr= request.POST.get("account_holder_address")
            b_name= request.POST.get("bank_name")
            br_name= request.POST.get("branch_name")
            ifsc_code = request.POST.get("ifsc")
            acc_no = request.POST.get("accno")
            upi= request.POST.get("upi")

            beneficiar, created = Beneficial.objects.get_or_create(first_name=ben_fname, last_name=ben_lname, phone_number=ben_phn,
                defaults={'address': ben_addr, 'age': ben_age,})
            if acc_type == "custom":
                bank_details, created = BankDetails.objects.get_or_create(
                    account_no=acc_no, ifsc_code= ifsc_code,
                    defaults={
                        'account_holder_first_name': acc_fname,
                        'account_holder_last_name': acc_lname,
                        'account_holder_address': acc_addr,
                        'account_holder_phn_no': acc_phn,
                        'bank_name': b_name,
                        'branch_name': br_name,
                        'upi_id': upi,
                    }
                )
            else:
                bank_details = request.user.default_bank
            new_project = Project(title=title, description=desc, beneficiary=beneficiar, created_by=request.user, funding_goal=goal, tile_value=tval, closing_date=clsdate, bank_details=bank_details)
            new_project.save()
            return redirect('/administrator/all-project/')
        return render(request, "admin-all-projects.html",{'prj':prj, 'admin': request.user})
    else:
        return redirect('/sign-in/')


def adminSingleProject(request, pid):
    if request.user.is_superuser or request.user.is_staff:
        project = Project.objects.get(id = pid)
        tile_range = range(1, int(project.funding_goal // project.tile_value) + 1)
        return render(request,"admin-single-projects.html", { 'admin':request.user, 'project': project, 't_range': tile_range})
    else:
        return redirect('/sign-in/')


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
        return redirect('/sign-in/')
