from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from adminModule.models import BankDetails, Beneficial, Project, Institution


# Create your views here.
@login_required(login_url='/sign-in/')
def adminDashboard(request):
    if request.user.is_superuser or request.user.is_staff:
        return render(request, "admin-dashboard.html", {'admin':request.user})
    else:
        return redirect('/sign-in/')


def adminAllProject(request):
    if request.user.is_superuser or request.user.is_staff:
        prj = Project.objects.all()
        default_bank = BankDetails.objects.get(account_type = "default")
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
            bank_details, created = BankDetails.objects.get_or_create(ifsc_code=ifsc_code, account_no=acc_no,
                defaults={'account_holder_first_name': acc_fname, 'account_holder_last_name': acc_lname, 'account_holder_address': acc_addr,
                          'account_holder_phn_no': acc_phn, 'bank_name': b_name, 'branch_name': br_name, 'upi_id': upi,})
            new_project = Project(title=title, description=desc, beneficiary=beneficiar, funding_goal=goal, tile_value=tval, closing_date=clsdate, bank_details=bank_details)
            new_project.save()
            return redirect('/administrator/all-project/')
        return render(request, "admin-all-projects.html",{'prj':prj, 'bank':default_bank, 'admin': request.user})
    else:
        return redirect('/sign-in/')


def adminSingleProject(request):
    if request.user.is_superuser or request.user.is_staff:
        return render(request,"admin-single-projects.html", { 'admin':request.user})
    else:
        return redirect('/sign-in/')


def adminAllBankDetails(request):
    if request.user.is_superuser or request.user.is_staff:
        banks = BankDetails.objects.all()
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
            BankDetails.objects.filter(account_type='default').update(account_holder_first_name=fname, account_holder_last_name=lname,account_holder_address=addr, account_holder_phn_no=phn, account_type="default",bank_name=bname,branch_name=brname,ifsc_code=ifcs,account_no=accno,upi_id=upi)
            return redirect('/administrator/all-bank/')
        return render(request, "admin-all-bank-details.html",{'banks':banks, 'admin': request.user})
    else:
        return redirect('/sign-in/')


def adminAllInstitution(request):
    if request.user.is_superuser or request.user.is_staff:
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
    if request.user.is_superuser or request.user.is_staff:
        return render(request,"admin-all-insti-admin.html", {'admin': request.user})
    else:
        return redirect('/sign-in/')