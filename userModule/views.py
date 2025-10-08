from adminModule.utils import whatsapp_send_initiated, email_send_initiated, whatsapp_send_proof, email_send_proof, sms_send_initiated, sms_send_proof, get_unique_tracking_id
from userModule.models import PersonalDetails, SelectedTile, Transaction, Screenshot, ContactMessage
from django.shortcuts import render, redirect, get_object_or_404
from adminModule.models import Project, Institution
from django.db import transaction as db_transaction
from django.db import transaction, IntegrityError
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
import urllib.parse
import os


# Create your views here.
def userIndex(request, ins_id):
    ins = get_object_or_404(Institution, id=ins_id, table_status=True)

    projects = Project.objects.filter(created_by=ins,closing_date__gte=timezone.now(),
        table_status=True).order_by('-created_at')[:3]
    for p in projects:
        p.progress = round((p.current_amount / p.funding_goal) * 100,
                                 3) if p.funding_goal > 0 else 0

    if request.method == 'POST':
        try:
            with transaction.atomic():
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                email = request.POST.get('email')
                phone = request.POST.get('phone')
                message = request.POST.get('message')

                if not all([first_name, last_name, email, phone, message]):
                    messages.error(request, 'All form fields must be filled out.')
                    return redirect(f'/user/{ins.id}/contact-us/')

                ContactMessage.objects.create(first_name=first_name,last_name=last_name,email=email,phone=phone,message=message,ins=ins)

                messages.success(request, 'Your message has been sent successfully!')
                return redirect(f'/user/{ins.id}/')

        except IntegrityError:
            messages.error(request, 'An error occurred while saving your message. Please try again.')
        except Exception as e:
            messages.error(request, f'An unexpected error occurred: {e}')
    return render(request, 'index.html',{'ins':ins, 'prj':projects})


def contact_us(request, ins_id):
    ins = get_object_or_404(Institution, id=ins_id, table_status=True)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                email = request.POST.get('email')
                phone = request.POST.get('phone')
                message = request.POST.get('message')

                if not all([first_name, last_name, email, phone, message]):
                    messages.error(request, 'All form fields must be filled out.')
                    return redirect(f'/user/{ins.id}/contact-us/')

                ContactMessage.objects.create(first_name=first_name,last_name=last_name,email=email,phone=phone,message=message,ins=ins)

                messages.success(request, 'Your message has been sent successfully!')
                return redirect(f'/user/{ins.id}/contact-us/')

        except IntegrityError:
            messages.error(request, 'An error occurred while saving your message. Please try again.')
        except Exception as e:
            messages.error(request, f'An unexpected error occurred: {e}')
    return render(request, 'contact-us.html', {'ins': ins})


def about(request, ins_id):
    ins = get_object_or_404(Institution, id=ins_id, table_status=True)
    return render(request,'about.html', {'ins':ins})


def credit(request, ins_id):
    ins = get_object_or_404(Institution, id=ins_id, table_status=True)
    return render(request,'user-credit.html', {'ins':ins})


def userAllProject(request,ins_id):
    ins = get_object_or_404(Institution, id=ins_id, table_status=True)
    projects = Project.objects.filter(created_by=ins,closing_date__gte=timezone.now(),
                                      table_status=True).order_by('-created_at')
    for p in projects:
        p.progress = round((p.current_amount / p.funding_goal) * 100,
                                 3) if p.funding_goal > 0 else 0
    return render(request, 'user-projects.html',{'ins':ins, 'prj':projects})


def userSingleProject(request, prj_id, ins_id):
    ins = get_object_or_404(Institution, id=ins_id, table_status=True)
    prj = get_object_or_404(Project, id=prj_id)

    prj.progress = round((prj.current_amount / prj.funding_goal) * 100,
                             3) if prj.funding_goal > 0 else 0
    total_tiles = int(prj.funding_goal // prj.tile_value)

    if request.method == "POST":
        selected_tiles = request.POST.get("selected_tiles_input")
        if not selected_tiles:
            return redirect(reverse('user_single_project', kwargs={'ins_id': ins_id, 'prj_id': prj_id}))

        checkout_url = reverse('user_checkout', kwargs={'ins_id': ins.id})
        query_string = urllib.parse.urlencode({'project_id': prj.id, 'selected_tiles': selected_tiles})
        return redirect(f"{checkout_url}?{query_string}")

    else:
        project_status = 'Active'
        if prj.funding_goal <= prj.current_amount:
            project_status = 'Completed'
        elif prj.closing_date < timezone.now():
            project_status = 'Expired'
        if not prj.table_status:
            project_status = 'Closed'

        if project_status in ['Completed', 'Expired', 'Closed']:
            return render(request, 'user-single-project.html',{'ins': ins, 'project': prj, 'project_status': project_status,})
        else:
            tile_range = range(1, total_tiles + 1)
            all_tiles_str_list = SelectedTile.objects.filter(project=prj,table_status=True).values_list('tiles', flat=True)

            all_tiles_list = []
            for tiles_str in all_tiles_str_list:
                if tiles_str:
                    all_tiles_list.extend([int(t) for t in tiles_str.split('-') if t.isdigit()])

            sold_tiles_set = set(Transaction.objects.filter(project=prj,status='Verified').values_list('tiles_bought__tiles', flat=True))
            sold_tiles = set([int(t) for s in sold_tiles_set for t in s.split('-') if t.isdigit()])

            processing_tiles_set = set(Transaction.objects.filter(project=prj,status='Unverified').values_list('tiles_bought__tiles', flat=True))
            processing_tiles = set([int(t) for s in processing_tiles_set for t in s.split('-') if t.isdigit()])

            unavailable_tiles_count = len(sold_tiles) + len(processing_tiles)
            available_tiles_count = total_tiles - unavailable_tiles_count

            return render(request, 'user-single-project.html',{'ins': ins, 'project': prj, 'total_tiles': total_tiles,
                           'available_tiles_count': available_tiles_count, 't_range': tile_range,'sold_tiles_set': sold_tiles, 'processing_tiles_set': processing_tiles,})

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

        if project.closing_date <= timezone.now():
            messages.error(request, "This project is closed for contributions.")
            return redirect(f'/user/{ins_id}/single-project/{project_id}/')
        if not project.table_status:
            messages.error(request, "This project is no longer active for contributions.")
            return redirect(f'/user/{ins_id}/single-project/{project_id}/')
        if SelectedTile.objects.filter(project=project, tiles=selected_tiles_str, table_status=True).exists():
            messages.error(request, "These tiles have already been selected.")
            return redirect(f'/user/{ins_id}/single-project/{project_id}/')

        try:
            with db_transaction.atomic():
                sender = PersonalDetails.objects.create(email=email,first_name=fname,last_name=lname,phone=phn,address=addr)
                selected_tile_instance = SelectedTile.objects.create(project=project,sender=sender,tiles=selected_tiles_str)
                transaction = Transaction.objects.create(tiles_bought=selected_tile_instance,sender=sender,project=project,amount=total_amount,currency="INR",status="Unverified",tracking_id=get_unique_tracking_id(),message=message_text)

            proof_upload_url = f'{ins_id}/proof/{transaction.id}'

            sms_result = sms_send_initiated(transaction, proof_upload_url)
            whatsapp_result = whatsapp_send_initiated(transaction, proof_upload_url)
            email_success, email_message = email_send_initiated(transaction, request.build_absolute_uri(f'/user/{proof_upload_url}/'))

            all_notifications_sent = True
            notification_errors = []

            if sms_result['status'] == 'error':
                all_notifications_sent = False
                notification_errors.append(f"SMS sending failed: {sms_result['message']}")

            if whatsapp_result['status'] == 'error':
                all_notifications_sent = False
                notification_errors.append(f"WhatsApp message failed to send: {whatsapp_result['message']}")

            if not email_success:
                all_notifications_sent = False
                notification_errors.append(f"Email sending failed: {email_message}")

            if all_notifications_sent:
                messages.success(request,f'Payment for the tiles {selected_tiles_str} has been initiated and a confirmation has been sent via SMS, WhatsApp, and Email.')
            else:
                base_message = "Your payment has been successfully initiated, but we encountered issues with some of the notification services."
                detailed_errors = " ".join(notification_errors)
                messages.warning(request, f"{base_message} Details: {detailed_errors}")

        except Exception as e:
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

            sms_result = sms_send_proof(tra)
            whatsapp_result = whatsapp_send_proof(tra)
            email_success, email_message = email_send_proof(tra)

            all_notifications_sent = True
            notification_errors = []

            if sms_result['status'] == 'error':
                all_notifications_sent = False
                notification_errors.append(f"SMS sending failed: {sms_result['message']}")

            if whatsapp_result['status'] == 'error':
                all_notifications_sent = False
                notification_errors.append(f"WhatsApp message failed to send: {whatsapp_result['message']}")

            if not email_success:
                all_notifications_sent = False
                notification_errors.append(f"Email sending failed: {email_message}")

            if all_notifications_sent:
                messages.success(request,"Proof of payment uploaded successfully and a confirmation has been sent via email, SMS, and WhatsApp.")
            else:
                base_message = "Proof of payment uploaded successfully, but we encountered issues with some of the notification services."
                detailed_errors = " ".join(notification_errors)
                messages.warning(request, f"{base_message} Details: {detailed_errors}")
        except Exception as e:
            messages.error(request, f"An error occurred during proof upload: {e}")
        return redirect(f'/user/{ins_id}/single-project/{tra.project.id}/')

    return render(request, "user-proof-upload.html", {'ins': ins,'tra': tra,'count': count})


def userTrackStatus(request, ins_id):
    ins = Institution.objects.get(id=ins_id)
    transactions = Transaction.objects.none()
    search_content = ''

    if request.method == 'POST':
        track_query = request.POST.get('track', '').strip()
        search_content = track_query

        if track_query:
            if '@' in track_query:
                transactions = Transaction.objects.filter(sender__email=track_query).order_by('-transaction_time')
            elif track_query.isdigit():
                transactions = Transaction.objects.filter(sender__phone=track_query).order_by('-transaction_time')
            else:
                transactions = Transaction.objects.filter(tracking_id=track_query).order_by('-transaction_time')

            for t in transactions:
                if t.tiles_bought:
                    t.num_tiles = len(t.tiles_bought.tiles.split('-'))
                else:
                    t.num_tiles = 0

    return render(request, "user-track-status.html", {'ins': ins, 'tra': transactions, 'search': search_content})



