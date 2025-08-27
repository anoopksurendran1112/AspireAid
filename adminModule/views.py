from django.db.models import F

from adminModule.models import BankDetails, Beneficial, Project, Institution, ProjectImage, CustomUser
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.shortcuts import render, redirect, get_object_or_404
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from reportlab.platypus.flowables import HRFlowable
from userModule.models import Transaction, Receipt
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from django.db import IntegrityError
from reportlab.lib.units import inch
from django.utils import timezone
from reportlab.lib import colors
from io import BytesIO
import qrcode
import urllib
import io


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
                return redirect('/administrator/')
        else:
            return redirect('/administrator/')
    return render(request, "admin-login.html")


@login_required(login_url='/administrator/')
def adminDashboard(request):
    if request.user.is_superuser or request.user.is_staff:
        all_prj = Project.objects.filter(created_by=request.user).count()
        closed_prj = Project.objects.filter(created_by=request.user, closing_date__lte=timezone.now()).count()
        completed_prj = Project.objects.filter(created_by=request.user, current_amount__gte=F('funding_goal')).count()
        failed_prj = Project.objects.filter(created_by=request.user, closing_date__lte=timezone.now(), current_amount__lt=F('funding_goal')).count()
        all_tra = Transaction.objects.filter(project__created_by=request.user).count()
        ver_tra = Transaction.objects.filter(project__created_by=request.user, status='Verified').count()
        unver_tra = Transaction.objects.filter(project__created_by=request.user, status='Unverified').count()
        rej_tra = Transaction.objects.filter(project__created_by=request.user, status='Rejected').count()

        latest_projects = Project.objects.filter(created_by=request.user, closing_date__gte=timezone.now(), current_amount__lt=F('funding_goal')).order_by('-created_at')[:5]
        for p in latest_projects:
            if p.closing_date < timezone.now():
                p.validity = False
        context = {
            'all_prj': all_prj,
            'cls_prj': closed_prj,
            'lst_prj': latest_projects,
            'cmp_prj': completed_prj,
            'fail_prj': failed_prj,
            'all_tra': all_tra,
            'ver_tra': ver_tra,
            'unver_tra': unver_tra,
            'rej_tra': rej_tra,
        }
        return render(request, "admin-dashboard.html", {'admin':request.user, 'context': context})
    else:
        return redirect('/')


def adminLogOut(request):
    logout(request)
    return redirect('/')


def adminProfile(request):
    if request.user.is_superuser or request.user.is_staff:
        return render(request, 'admin-profile.html',{'admin': request.user})
    else:
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
        for p in prj:
            if p.closing_date < timezone.now():
                p.validity = False
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
        return redirect('/')


def delete_project_image(request, img_id):
    if request.user.is_superuser or request.user.is_staff:
        img = ProjectImage.objects.get(id=img_id)
        prj_id = img.project.id
        img.delete()
        return redirect(f'/administrator/single-project/{prj_id}/')
    else:
        return redirect('/')


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
        return redirect('/')


def adminAllTransactions(request):
    if request.user.is_superuser or request.user.is_staff:
        prj = Project.objects.filter(created_by = request.user)
        transaction_filtered = Transaction.objects.filter(project__in=prj).order_by('-transaction_time')
        for t in transaction_filtered:
            if t.tiles_bought:
                t.num_tiles = len(t.tiles_bought.tiles.split('-'))
            else:
                t.num_tiles = 0
        return render(request, 'admin-all-transactions.html', {'transaction':transaction_filtered})
    else:
        return redirect('/')


def adminVerifyTransaction(request, tid):
    if request.user.is_superuser or request.user.is_staff:
        transaction = Transaction.objects.get(id=tid)
        if transaction.tiles_bought:
            transaction.num_tiles = len(transaction.tiles_bought.tiles.split('-'))
        else:
            transaction.num_tiles = 0
        return render(request, "admin-verify-transaction.html", {'admin': request.user, 'transaction': transaction})
    else:
        return redirect('/')


def adminApproveTransaction(request, tid):
    if request.user.is_superuser or request.user.is_staff:
        transaction = Transaction.objects.get(id=tid)
        if transaction.status != "Verified":
            transaction.status = "Verified"
            transaction.table_status = True
            transaction.tiles_bought.table_status = True
            transaction.project.current_amount += transaction.amount
            if transaction.project.funding_goal == transaction.project.current_amount:
                transaction.project.table_status = False
            transaction.project.save()
            transaction.save()
        return redirect('/administrator/all-transactions/')
    else:
        return redirect('/')


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
        return redirect('/administrator/all-transactions/')
    else:
        return redirect('/')


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
        return redirect('/administrator/all-transactions/')
    else:
        return redirect('/')


def generate_receipt_pdf(transaction):

    # A4 page dimensions and margins
    page_width = A4[0]
    left_margin = 0.5 * inch
    right_margin = 0.5 * inch
    available_width = page_width - left_margin - right_margin

    # Use an in-memory buffer to build the PDF
    buffer = io.BytesIO()

    # Create the PDF document
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=left_margin, rightMargin=right_margin,
                            topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    elements = []
    transaction.num_tiles = len(transaction.tiles_bought.tiles.split('-'))

    # --- Define Styles ---
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('TitleStyle', fontName='Helvetica-Bold', fontSize=18, spaceAfter=50, alignment=TA_LEFT))
    styles.add(ParagraphStyle('SubtitleStyle', fontName='Helvetica-Bold', fontSize=12, spaceAfter=6, alignment=TA_LEFT))
    styles.add(ParagraphStyle('NormalStyle', fontName='Helvetica', fontSize=10, spaceAfter=6, alignment=TA_LEFT))
    styles.add(ParagraphStyle('BoldStyle', fontName='Helvetica-Bold', fontSize=10, spaceAfter=6, alignment=TA_LEFT))
    styles.add(ParagraphStyle('RightAlignNormal', fontName='Helvetica', fontSize=10, spaceAfter=6, alignment=TA_RIGHT))
    styles.add(
        ParagraphStyle('AmountDueStyle', fontName='Helvetica-Bold', fontSize=16, spaceAfter=12, alignment=TA_CENTER))

    # --- Header Section (Logo, Invoice Number, Date) ---
    header_data = [
        [Paragraph(transaction.project.created_by.institution.institution_name, styles['TitleStyle']), ""],
        '',
        [Paragraph(f"NO: invoice 1", styles['BoldStyle']),
         Paragraph(f"DATE: {timezone.now()}", styles['RightAlignNormal'])]
    ]
    header_table = Table(header_data, colWidths=[available_width / 2, available_width / 2])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1, spaceAfter=15, spaceBefore=0))

    # --- Details Section (Project, Beneficiary, Tiles, Buyer) ---
    # Create the first row table for Project and Beneficiary details
    project_beneficiary_data = [
        [
            Paragraph("Project Details", styles['SubtitleStyle']),
            Paragraph("Beneficiary Details", styles['SubtitleStyle']),
        ],
        [
            Paragraph(f"<b>Title:</b> {transaction.project.title}<br/>"
                      f"<b>Starting date:</b> {transaction.project.created_at}<br/>"
                      f"<b>Closing date:</b> {transaction.project.closing_date}<br/>"
                      f"<b>Created by:</b> {transaction.project.closing_date}<br/>", styles['NormalStyle']),
            Paragraph(f"<b>Name:</b> {transaction.project.beneficiary.first_name} {transaction.project.beneficiary.last_name}<br/>"
                      f"<b>Phone:</b> {transaction.project.beneficiary.phone_number}<br/>"
                      f"<b>Address:</b> {transaction.project.beneficiary.phone_number}<br/>", styles['NormalStyle']),
        ]
    ]

    project_beneficiary_table = Table(project_beneficiary_data, colWidths=[available_width / 2, available_width / 2])
    project_beneficiary_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(project_beneficiary_table)

    # Add a Spacer to create a gap between the two detail rows
    elements.append(Spacer(1, 10))

    # Create the second row table for Tiles and Buyer details
    tiles_buyer_data = [
        [
            Paragraph("Tiles Details", styles['SubtitleStyle']),
            Paragraph("Buyer Details", styles['SubtitleStyle']),
        ],
        [
            Paragraph(f"<b>Selected Tiles:</b> {transaction.tiles_bought.tiles}<br/>"
                      f"<b>Quantity:</b> {transaction.num_tiles}<br/>"
                      f"<b>Amount:</b> {transaction.amount}<br/>", styles['NormalStyle']),
            Paragraph(f"<b>Name:</b> {transaction.sender.first_name} {transaction.sender.last_name}<br/>"
                      f"<b>Phone:</b> {transaction.sender.phone}<br/>"
                      f"<b>Email:</b> {transaction.sender.email}<br/>"
                      f"<b>Address:</b> {transaction.sender.address}<br/>", styles['NormalStyle'])
        ]
    ]

    tiles_buyer_table = Table(tiles_buyer_data, colWidths=[available_width / 2, available_width / 2])
    tiles_buyer_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(tiles_buyer_table)
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1, spaceAfter=15, spaceBefore=0))

    # --- Items Table ---
    item_rows = [["Project Title", "Tiles Bought", "Quantity", "Tile Value", "Total"]]
    total_value = 0
    row_total = transaction.num_tiles * transaction.project.tile_value
    item_rows.append([
        transaction.project.title,
        transaction.tiles_bought.tiles,
        transaction.num_tiles,
        transaction.project.tile_value,
        row_total
    ])

    item_rows.append(["", "", "", "Total:", row_total])

    col_widths = [available_width * 0.40, available_width * 0.20, available_width * 0.10, available_width * 0.10,
                  available_width * 0.20]

    items_table = Table(item_rows, colWidths=col_widths)
    items_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, -1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(items_table)
    elements.append(Spacer(1, 10))

    # --- Amount Due Section ---
    elements.append(Paragraph(f"Total: {row_total}Rs", styles['AmountDueStyle']))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1, spaceAfter=15, spaceBefore=0))

    # --- Payment Details Section ---
    elements.append(Paragraph("Payment Details", styles['SubtitleStyle']))
    elements.append(Paragraph(f'<b>Transaction ID:</b> {transaction.transaction_id}', styles['NormalStyle']))
    elements.append(Paragraph(f'<b>Transaction Date:</b> {transaction.transaction_time}', styles['NormalStyle']))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1, spaceAfter=15, spaceBefore=0))

    # --- Notes/Message Section ---
    elements.append(Paragraph("Message", styles['SubtitleStyle']))
    elements.append(Paragraph(transaction.message, styles['NormalStyle']))

    # Build PDF
    doc.build(elements)

    # Reset buffer position to the beginning before returning
    buffer.seek(0)

    return ContentFile(buffer.getvalue(), name=f'{transaction.transaction_id}.pdf')


def adminGenerateReceipts(request, t_id):
    if request.user.is_superuser or request.user.is_staff:
        transaction_instance = get_object_or_404(Transaction, id=t_id)

        receipt, created = Receipt.objects.update_or_create(
            transaction=transaction_instance,
            defaults={'receipt_pdf': generate_receipt_pdf(transaction_instance)}
        )
        return redirect('/administrator/all-transactions/')
    else:
        return redirect('/administrator/')



def adminAllReceipts(request):
    if request.user.is_superuser or request.user.is_staff:
        receipts = Receipt.objects.all()
        for r in receipts:
            r.tile_count = len(r.transaction.tiles_bought.tiles.split('-'))
        return render(request, 'admin-all-receipts.html',{'rec':receipts})
    else:
        return redirect('/administrator/')