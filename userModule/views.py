import urllib.parse
import uuid

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from adminModule.models import Project, Institution
from userModule.models import PersonalDetails, SelectedTile, Transaction


# Create your views here.
def userIndex(request, ins_id):
    ins = Institution.objects.get(id=ins_id)
    projects = Project.objects.filter(
        created_by__institution=ins,
        created_by__is_staff=True,
        table_status=True
    ).order_by('-created_at')[:3]
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
        table_status=True
    ).order_by('-created_at')
    return render(request, 'user-projects.html',{'ins':ins, 'prj':projects})


def userSingleProject(request,prj_id, ins_id):
    ins = Institution.objects.get(id=ins_id)
    prj = Project.objects.get(id=prj_id)
    tile_range = range(1, int(prj.funding_goal // prj.tile_value) + 1)

    # Separating bought tiles based on the transaction status for displaying with color
    verified_transactions = Transaction.objects.filter(project=prj, status='Verified',tiles_bought__table_status=True)
    processing_transactions = Transaction.objects.filter(project=prj,status='Unverified',tiles_bought__table_status=True)
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

    # For checkout
    if request.method == "POST":
        selected_tiles = request.POST.get("selected_tiles_input")
        checkout_url = reverse('user_checkout', kwargs={'ins_id': ins.id})
        query_string = urllib.parse.urlencode({
            'project_id': prj.id,
            'selected_tiles': selected_tiles
        })
        return redirect(f"{checkout_url}?{query_string}")
    return render(request, 'user-single-project.html', {'ins':ins, 'project': prj,'t_range': tile_range,
                                                            'processing_tiles_set': processing_tiles_set, 'sold_tiles_set': sold_tiles_set,})


def userCheckoutView(request,ins_id):
    ins = Institution.objects.get(id=ins_id)
    if request.method == "GET":
        project_id = request.GET.get("project_id")
        selected_tiles = request.GET.get("selected_tiles")

        project = Project.objects.get(id=project_id)
        selected_tile_count = len(selected_tiles.split('-'))
    elif  request.method == "POST":
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

        sender = PersonalDetails.objects.create(email=email, first_name= fname, last_name= lname,phone= phn,address= addr,)
        selected_tile_instance = SelectedTile.objects.create(project=project, sender=sender, tiles=selected_tiles_str)
        transaction = Transaction.objects.create(tiles_bought=selected_tile_instance, sender=sender, project=project,amount=total_amount,
                                                 currency="INR", status="Unverified", transaction_id=str(uuid.uuid4()), message=message_text)
        return redirect(f'/user/single-project/{project_id}/')
    return render(request, 'user-checkout.html', {'ins':ins,'project': project, 'selected_tiles': selected_tiles, 'count':selected_tile_count})


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