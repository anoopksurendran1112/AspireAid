from django.shortcuts import render, redirect

from adminModule.models import BankDetails


# Create your views here.
def adminDashboard(request):
    return render(request, "admin-dashboard.html")


def adminAddProject(request):
    return render(request, "admin-add-project.html")


def adminAllBankDetails(request):
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
    banks = BankDetails.objects.all()
    return render(request, "admin-all-bank-details.html",{'banks':banks})


def adminEditDefaultBankDetails(request):
    return render(request,"admin-edit-default-bank-details.html")