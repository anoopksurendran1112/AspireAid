import os

from adminModule.utils import whatsapp_send_initiated, email_send_initiated, whatsapp_send_proof, email_send_proof, sms_send_initiated, sms_send_proof, get_unique_tracking_id
from userModule.models import PersonalDetails, SelectedTile, Transaction, Screenshot
from django.shortcuts import render, redirect, get_object_or_404
from adminModule.models import Project, Institution
from django.db import transaction as db_transaction
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
import urllib.parse



# Create your views here.
def userIndex(request, ins_id):
    ins = Institution.objects.get(id=ins_id)
    projects = Project.objects.filter(created_by__institution=ins, created_by__is_staff=True,closing_date__gte=timezone.now(),
        table_status=True).order_by('-created_at')[:3]
    return render(request, 'index.html',{'ins':ins, 'prj':projects})
      
      
def contact_us(request,ins_id):
    ins = Institution.objects.get(id=ins_id)
    return render(request,'contact-us.html', {'ins':ins})


def about(request, ins_id):
    ins = Institution.objects.get(id=ins_id)
    return render(request,'about.html', {'ins':ins})


def userAllProject(request,ins_id):
    ins = Institution.objects.get(id=ins_id)
    projects = Project.objects.filter(
        created_by__institution=ins,
        created_by__is_staff=True,
        closing_date__gte=timezone.now(),
        table_status=True
    ).order_by('-created_at')
    return render(request, 'user-projects.html',{'ins':ins, 'prj':projects})


def userSingleProject(request, prj_id, ins_id):
    ins = get_object_or_404(Institution, id=ins_id)
    prj = get_object_or_404(Project, id=prj_id)

    if request.method == "POST":
        selected_tiles = request.POST.get("selected_tiles_input")
        checkout_url = reverse('user_checkout', kwargs={'ins_id': ins.id})
        query_string = urllib.parse.urlencode({'project_id': prj.id,'selected_tiles': selected_tiles})
        return redirect(f"{checkout_url}?{query_string}")

    else:
        prj.status =''
        if prj.funding_goal == prj.current_amount:
            prj.status = 'Completed'
            prj.save()
        elif prj.closing_date < timezone.now():
            prj.status = 'Expired'
            prj.save()
        elif prj.table_status is False:
            prj.status = 'Closed'
            prj.save()

        if prj.status not in ['Completed', 'Expired', 'Closed']:
            tile_range = range(1, int(prj.funding_goal // prj.tile_value) + 1)

            verified_transactions = Transaction.objects.filter(project=prj, status='Verified',
                                                               tiles_bought__table_status=True)
            processing_transactions = Transaction.objects.filter(project=prj, status='Unverified',
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

            return render(request, 'user-single-project.html',
                          { 'ins': ins, 'project': prj, 't_range': tile_range, 'processing_tiles_set': processing_tiles_set,
                            'sold_tiles_set': sold_tiles_set, 'now': timezone.now()})
        else:
            return render(request, 'user-single-project.html',
                          { 'ins': ins,'project': prj,'now': timezone.now()})


def userCheckoutView(request, ins_id):
    institution = get_object_or_404(Institution, id=ins_id)

    if request.method == "GET":
        project_id = request.GET.get("project_id")
        selected_tiles = request.GET.get("selected_tiles")
        project = get_object_or_404(Project, id=project_id)
        selected_tile_count = len(selected_tiles.split('-'))
        return render(request, 'user-checkout.html', {'ins': institution,'project': project,
                                                      'selected_tiles': selected_tiles,'count': selected_tile_count})

    elif request.method == "POST":
        project_id = request.POST.get("project_id")
        selected_tiles_str = request.POST.get("selected_tiles")
        fname = request.POST.get("fname")
        lname = request.POST.get("lname")
        email = request.POST.get("email")
        phn = request.POST.get("phn")
        addr = request.POST.get("addr")
        message_text = request.POST.get("message")

        project = get_object_or_404(Project, id=project_id)
        total_amount = len(selected_tiles_str.split('-')) * project.tile_value

        try:
            with db_transaction.atomic():

                if project.closing_date <= timezone.now():
                    messages.error(request, "This project is closed for contributions.")
                    return redirect(f'/user/{ins_id}/single-project/{project_id}/')
                if not project.table_status:
                    messages.error(request, "This project is no longer active for contributions.")
                    return redirect(f'/user/{ins_id}/single-project/{project_id}/')
                if SelectedTile.objects.filter(project=project, tiles=selected_tiles_str).exists():
                    messages.error(request, "These tiles have already been selected.")
                    return redirect(f'/user/{ins_id}/single-project/{project_id}/')

                sender = PersonalDetails.objects.create(email=email,first_name=fname,last_name=lname,phone=phn,address=addr)
                selected_tile_instance = SelectedTile.objects.create(project=project,sender=sender,tiles=selected_tiles_str)
                transaction = Transaction.objects.create(tiles_bought=selected_tile_instance,sender=sender,project=project,amount=total_amount,currency="INR",status="Unverified",tracking_id=get_unique_tracking_id(),message=message_text)

            proof_upload_url = f'{ins_id}/proof/{transaction.id}'

            sms_send_initiated(transaction,proof_upload_url)
            whatsapp_send_initiated(transaction,proof_upload_url)
            email_send_initiated(transaction,proof_upload_url)

            messages.success(request, f'Payment for the tiles {selected_tiles_str} has been initiated.')
        except Exception as e:
            print(f"An error occurred: {e}")
            messages.error(request, f"Failed to perform checkout: {e}")
        return redirect(f'/user/{ins_id}/single-project/{project_id}/')


def userProofUpload(request, ins_id, trans_id):
    ins = get_object_or_404(Institution, id=ins_id)
    tra = get_object_or_404(Transaction, id=trans_id)

    tiles_string = tra.tiles_bought.tiles if tra.tiles_bought else ''
    count = len(tiles_string.split('-')) if tiles_string else 0

    if request.method == 'POST':
        proof = request.FILES.get('proof_of_payment')
        if not proof:
            messages.error(request, "Please select a file to upload.")
            return redirect(f'/user/{ins_id}/proof/{tra.id}/')

        try:
            with db_transaction.atomic():

                try:
                    old_screenshot = Screenshot.objects.get(transaction=tra)
                    old_file_path = old_screenshot.screen_shot.path
                    old_screenshot.screen_shot = proof
                    old_screenshot.save()

                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)

                except Screenshot.DoesNotExist:
                    new_screenshot = Screenshot.objects.create(transaction=tra, screen_shot=proof)

            sms_send_proof(tra)
            whatsapp_send_proof(tra)
            email_send_proof(tra)

            messages.success(request, "Proof of payment uploaded successfully!")
        except Exception as e:
            print(f"An error occurred: {e}")
            messages.error(request, f"An error occurred during proof upload: {e}")
        return redirect(f'/user/{ins_id}/single-project/{tra.project.id}/')

    return render(request, "user-proof-upload.html", {'ins': ins,'tra': tra,'count': count})


def userTrackStatus(request, ins_id):
    ins = Institution.objects.get(id=ins_id)
    transactions = Transaction.objects.none()
    if request.method == 'POST':
        phn = request.POST.get('phn')
        transactions = Transaction.objects.filter(sender__phone = phn).order_by('-transaction_time')
        for t in transactions:
            if t.tiles_bought:
                t.num_tiles = len(t.tiles_bought.tiles.split('-'))
            else:
                t.num_tiles = 0
    return render(request, "user-track-status.html", {'ins': ins, 'tra':transactions})