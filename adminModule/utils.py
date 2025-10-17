from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from django.core.mail import EmailMessage, get_connection
from reportlab.platypus.flowables import HRFlowable, PageBreak, Image
from userModule.models import Receipt, Transaction
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from django.conf import settings
import datetime
import requests
import secrets
import string
import io
import os


SMS_INITIATE_TEMPLATE_ID = "198753"
SMS_PROOF_TEMPLATE_ID = "198750"
SMS_APPROVE_TEMPLATE_ID = "198751"
SMS_REJECT_TEMPLATE_ID = "198752"
SMS_UNVERIFY_TEMPLATE_ID = "198754"

authorization_key = "EApz1UNdI2KToYWBS5O0Fl4QDM8G6jxvi97PgaRhLqHrfwyeZuMsG2LUHqg6ZQoCKhbwXBz71pi9vANV"
header_id = "KDIGCF"

SMS_DLT_API = "https://www.fast2sms.com/dev/bulkV2"


"""Sends a regular SMS message for contact message response."""
def sms_send_response(new_reply):
    return {'status': 'success', 'message': 'SMS sent'}


"""Sends a email message for contact message response."""
def email_send_response(new_reply):
    return (True, 'Email sent')


"""Sends a Whatsapp message for contact message response."""
def whatsapp_send_response(new_reply):
    return {'status': 'success', 'message': 'WhatsApp sent'}


"""Sends a regular SMS message for payment initiated."""
def sms_send_initiated(transaction, url):
    try:
        user_full_name = f"{transaction.sender.full_name}"
        project_title = transaction.project.title
        phone_number = transaction.sender.phone

        variables_values = f"{user_full_name}|{project_title}|{url}|"
        params = {
            "authorization": authorization_key, "route": "dlt", "sender_id": header_id,
            "message": SMS_INITIATE_TEMPLATE_ID, "variables_values": variables_values,
            "flash": "0", "numbers": phone_number}

        response = requests.get(SMS_DLT_API, params=params)

        if response.status_code == 200:
            return {"status": "success", "response": response.text}
        else:
            return {"status": "error", "response": response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


"""Sends a regular SMS message for proof upload."""
def sms_send_proof(transaction):
    try:
        user_full_name = f"{transaction.sender.full_name}"
        tracking_id = transaction.tracking_id
        project_title = transaction.project.title
        phone_number = transaction.sender.phone

        variables_values = f"{user_full_name}|{project_title}|{tracking_id}|"
        params = {
            "authorization": authorization_key, "route": "dlt", "sender_id": header_id,
            "message": SMS_PROOF_TEMPLATE_ID, "variables_values": variables_values,
            "flash": "0", "numbers": phone_number,}
        response = requests.get(SMS_DLT_API, params=params)

        if response.status_code == 200:
            return {"status": "success", "response": response.text}
        else:
            return {"status": "error", "response": response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


"""Sends a regular SMS message for successful verification."""
def sms_send_approve(transaction):
    try:
        receipt = get_object_or_404(Receipt, transaction=transaction)

        user_full_name = f"{transaction.sender.full_name}"
        project_title = transaction.project.title

        if receipt.receipt_pdf:
            receipt.filename = os.path.basename(receipt.receipt_pdf.name)

        phone_number = transaction.sender.phone

        variables_values = f"{user_full_name}|{project_title}|{receipt.filename}|"
        params = {
            "authorization": authorization_key,"route": "dlt","sender_id": header_id,
            "message": SMS_APPROVE_TEMPLATE_ID,"variables_values": variables_values,
            "flash": "0","numbers": phone_number,}

        response = requests.get(SMS_DLT_API, params=params)

        if response.status_code == 200:
            return {"status": "success", "response": response.text}
        else:
            return {"status": "error", "response": response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


"""Sends a regular SMS message for rejected verification."""
def sms_send_reject(transaction):
    try:
        user_full_name = f"{transaction.sender.full_name}"
        project_title = transaction.project.title
        phone_number = transaction.sender.phone

        variables_values = f"{user_full_name}|{project_title}|"
        params = {
            "authorization": authorization_key,"route": "dlt","sender_id": header_id,
            "message": SMS_REJECT_TEMPLATE_ID,"variables_values": variables_values,
            "flash": "0","numbers": phone_number,}

        response = requests.get(SMS_DLT_API, params=params)

        if response.status_code == 200:
            return {"status": "success", "response": response.text}
        else:
            return {"status": "error", "response": response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


"""Sends a regular SMS message for unverified verification."""
def sms_send_unverify(transaction):
    try:
        user_full_name = f"{transaction.sender.full_name}"
        project_title = transaction.project.title
        phone_number = transaction.sender.phone

        variables_values = f"{user_full_name}|{project_title}|"
        params = {
            "authorization": authorization_key,"route": "dlt","sender_id": header_id,
            "message": SMS_UNVERIFY_TEMPLATE_ID,"variables_values": variables_values,
            "flash": "0","numbers": phone_number,}

        response = requests.get(SMS_DLT_API, params=params)

        if response.status_code == 200:
            return {"status": "success", "response": response.text}
        else:
            return {"status": "error", "response": response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


"""Sends a Whatsapp message for payment initiated."""
def whatsapp_send_initiated(transaction, url):
    try:
        params_string = f"{transaction.sender.full_name},{transaction.project.title},{transaction.tracking_id},{url}"
        api_params = {
            'user': settings.WHATSAPP_BHASHSMS_API_USER,'pass': settings.WHATSAPP_BHASHSMS_API_PASS,'sender': settings.WHATSAPP_BHASHSMS_API_SENDER,
            'phone': transaction.sender.phone,'text': 'cf_payment_initiated_v2','priority': settings.WHATSAPP_BHASHSMS_API_PRIORITY,
            'stype': settings.WHATSAPP_BHASHSMS_API_STYPE,'Params': params_string}

        response = requests.get(settings.WHATSAPP_BHASHSMS_API, params=api_params)
        if response.status_code == 200:
            return {"status": "success", "response": response.text}
        else:
            error_message = f"API returned non-200 status code: {response.status_code}. Response: {response.text}"
            return {"status": "error", "message": error_message}
    except Exception as e:
        error_message = f"An exception occurred during WhatsApp send: {str(e)}"
        return {"status": "error", "message": error_message}


"""Sends a WhatsApp message for proof upload."""
def whatsapp_send_proof(transaction):
    try:
        params_string = f"{transaction.sender.full_name}, {transaction.tracking_id},{transaction.project.title}"
        api_params = {
            'user': settings.WHATSAPP_BHASHSMS_API_USER,
            'pass': settings.WHATSAPP_BHASHSMS_API_PASS,
            'sender': settings.WHATSAPP_BHASHSMS_API_SENDER,
            'phone': transaction.sender.phone,
            'text': 'cf_successful_proof',
            'priority': settings.WHATSAPP_BHASHSMS_API_PRIORITY,
            'stype': settings.WHATSAPP_BHASHSMS_API_STYPE,
            'Params': params_string,}

        response = requests.get(settings.WHATSAPP_BHASHSMS_API, params=api_params)
        if response.status_code == 200:
            return {"status": "success", "response": response.text}
        else:
            error_message = f"API returned non-200 status code: {response.status_code}. Response: {response.text}"
            return {"status": "error", "message": error_message}
    except Exception as e:
        error_message = f"An exception occurred during WhatsApp send: {str(e)}"
        return {"status": "error", "message": error_message}


"""Sends a WhatsApp message for successful verification."""
def whatsapp_send_approve(transaction):
    try:
        receipt = get_object_or_404(Receipt, transaction=transaction)
        if receipt.receipt_pdf:
            receipt.filename = os.path.basename(receipt.receipt_pdf.name)

        params_string = f"{transaction.sender.full_name}, {transaction.project.title}, {receipt.filename}"
        api_params = {
            'user': settings.WHATSAPP_BHASHSMS_API_USER,
            'pass': settings.WHATSAPP_BHASHSMS_API_PASS,
            'sender': settings.WHATSAPP_BHASHSMS_API_SENDER,
            'phone': transaction.sender.phone,
            'text': 'cf_transaction_approved',
            'priority': settings.WHATSAPP_BHASHSMS_API_PRIORITY,
            'stype': settings.WHATSAPP_BHASHSMS_API_STYPE,
            'Params': params_string}

        response = requests.get(settings.WHATSAPP_BHASHSMS_API, params=api_params)
        if response.status_code == 200:
            return {"status": "success", "response": response.text}
        else:
            error_message = f"API returned non-200 status code: {response.status_code}. Response: {response.text}"
            return {"status": "error", "message": error_message}
    except Exception as e:
        error_message = f"An exception occurred during WhatsApp send: {str(e)}"
        return {"status": "error", "message": error_message}


"""Sends a WhatsApp message for rejected verification."""
def whatsapp_send_reject(transaction):
    try:
        params_string = f"{transaction.sender.full_name}, {transaction.project.title}"
        api_params = {
            'user': settings.WHATSAPP_BHASHSMS_API_USER,
            'pass': settings.WHATSAPP_BHASHSMS_API_PASS,
            'sender': settings.WHATSAPP_BHASHSMS_API_SENDER,
            'phone': transaction.sender.phone,
            'text': 'cf_transaction_rejected',
            'priority': settings.WHATSAPP_BHASHSMS_API_PRIORITY,
            'stype': settings.WHATSAPP_BHASHSMS_API_STYPE,
            'Params': params_string}

        response = requests.get(settings.WHATSAPP_BHASHSMS_API, params=api_params)
        if response.status_code == 200:
            return {"status": "success", "response": response.text}
        else:
            error_message = f"API returned non-200 status code: {response.status_code}. Response: {response.text}"
            return {"status": "error", "message": error_message}
    except Exception as e:
        error_message = f"An exception occurred during WhatsApp send: {str(e)}"
        return {"status": "error", "message": error_message}


"""Sends a WhatsApp message for unverified verification."""
def whatsapp_send_unverify(transaction):
    try:
        params_string = f"{transaction.sender.full_name}, {transaction.project.title}"
        api_params = {
            'user': settings.WHATSAPP_BHASHSMS_API_USER,
            'pass': settings.WHATSAPP_BHASHSMS_API_PASS,
            'sender': settings.WHATSAPP_BHASHSMS_API_SENDER,
            'phone': transaction.sender.phone,
            'text': 'cf_transaction_unverified',
            'priority': settings.WHATSAPP_BHASHSMS_API_PRIORITY,
            'stype': settings.WHATSAPP_BHASHSMS_API_STYPE,
            'Params': params_string}

        response = requests.get(settings.WHATSAPP_BHASHSMS_API, params=api_params)
        if response.status_code == 200:
            return {"status": "success", "response": response.text}
        else:
            error_message = f"API returned non-200 status code: {response.status_code}. Response: {response.text}"
            return {"status": "error", "message": error_message}
    except Exception as e:
        error_message = f"An exception occurred during WhatsApp send: {str(e)}"
        return {"status": "error", "message": error_message}


"""Start connecting SMTP server"""
def get_email_connection(institution):
    try:
        connection = get_connection(host='smtp.gmail.com',port=587,username=institution.email,
                                    password=institution.email_app_password,use_tls=True,use_ssl=False)
        return True, connection
    except Exception as e:
        error_message = f"Could not establish email connection. Please check the SMTP credentials. Error: {e}"
        return False, error_message


"""Sends an email for payment initiated."""
def email_send_initiated(transaction, url):
    try:
        institution = transaction.project.created_by

        success, connection = get_email_connection(institution)
        if not success:
            return False, connection

        subject = f'Payment Initiated for "{transaction.project.title}"'
        plain_text_message = (
            f'Dear {transaction.sender.full_name},\n\n'
            f'Your donation for the project "{transaction.project.title}" has been successfully recorded with tracking id: {transaction.tracking_id}. You can track the status using your mobile number.\n'
            f'You can upload proof or track the status here: {url}\n\n'
            f'- Team {institution.institution_name}')

        sender_email = transaction.project.created_by.email
        receiver_email = transaction.sender.email

        email_message = EmailMessage(subject=subject, body=plain_text_message, from_email=sender_email,
                                     to=[receiver_email], connection=connection)

        email_message.send(fail_silently=False)
        return True, "Email sent successfully."
    except Exception as e:
        error_message = f'An error occurred while sending the email. Error: {e}'
        return False, error_message


"""Sends an email for proof upload."""
def email_send_proof(transaction):
    try:
        institution = transaction.project.created_by

        success, connection = get_email_connection(institution)
        if not success:
            return False, connection

        subject = f'Proof upload for "{transaction.project.title}"'
        plain_text_message = (
            f'Dear {transaction.sender.full_name},\n'
            f'Thank you for submitting your donation proof for the project "{transaction.project.title}. Your tracking ID is {transaction.tracking_id}.\n'
            f'Verification is in progress, and you will be notified once it is completed.\n\n'
            f'- Team {institution.institution_name}')

        sender_email = transaction.project.created_by.email
        receiver_email = transaction.sender.email

        email_message = EmailMessage(subject=subject, body=plain_text_message, from_email=sender_email,
                                     to=[receiver_email], connection=connection)

        email_message.send(fail_silently=False)

        return True, "Email sent successfully."
    except Exception as e:
        error_message = f"An error occurred while sending the email. Error: {str(e)}"
        return False, error_message


"""Sends an email for successful verification with receipt."""
def email_send_approve(transaction):
    try:
        institution = transaction.project.created_by

        success, connection = get_email_connection(institution)
        if not success:
            return False, connection

        subject = f'Payment successfully verified for "{transaction.project.title}"'
        plain_text_message = (
            f'Dear {transaction.sender.full_name},\n\n'
            f'Your donation for the project "{transaction.project.title}" has been successfully verified, and the transaction is now complete.\n'
            f'Your receipt is attached below.\n\n'
            f'- Team {institution.institution_name}')

        sender_email = transaction.project.created_by.email
        receiver_email = transaction.sender.email

        email_message = EmailMessage(subject=subject,body=plain_text_message,from_email=sender_email,
            to=[receiver_email],connection=connection)

        try:
            receipt = Receipt.objects.get(transaction=transaction)
            pdf_path = receipt.receipt_pdf.path
            email_message.attach_file(pdf_path)
        except Exception as e:
            pass

        email_message.send(fail_silently=False)
        return True, "Email sent successfully."
    except Exception as e:
        error_message = f'An error occurred while sending the email. Error: {e}'
        return False, error_message


"""Sends an email for rejected verification."""
def email_send_reject(transaction):
    try:
        institution = transaction.project.created_by

        success, connection = get_email_connection(institution)
        if not success:
            return False, connection

        subject = f'Payment Verification Rejected for "{transaction.project.title}"'
        plain_text_message = (
            f'Dear {transaction.sender.full_name},\n\n'
            f'We regret to inform you that, your donation proof for the project "{transaction.project.title}" has been rejected.\n'
            f'Please contact the admin to resolve the issue and submit a valid proof to complete the transaction.\n\n'
            f'- Team {institution.institution_name}')

        sender_email = transaction.project.created_by.email
        receiver_email = transaction.sender.email

        email_message = EmailMessage(subject=subject,body=plain_text_message,from_email=sender_email,
            to=[receiver_email],connection=connection)

        email_message.send(fail_silently=False)
        return True, "Email sent successfully."
    except Exception as e:
        error_message = f'An error occurred while sending the email. Error: {e}'
        return False, error_message


"""Sends an email for unverified verification."""
def email_send_unverify(transaction):
    try:
        institution = transaction.project.created_by

        success, connection = get_email_connection(institution)
        if not success:
            return False, connection

        subject = f'Payment Status Unverified for "{transaction.project.title}"'
        plain_text_message = (
            f'Dear {transaction.sender.full_name},\n\n'
            f'Your donation for the project "{transaction.project.title}" remains unverified. Use your registered number to track the current status.\n'
            f'Our team is reviewing it and will verify soon.\n\n'
            f'- Team {institution.institution_name}')

        sender_email = transaction.project.created_by.email
        receiver_email = transaction.sender.email

        email_message = EmailMessage(subject=subject,body=plain_text_message,from_email=sender_email,
            to=[receiver_email],connection=connection)

        email_message.send(fail_silently=False)
        return True, "Email sent successfully."
    except Exception as e:
        error_message = f'An error occurred while sending the email. Error: {e}'
        return False, error_message


def get_unique_tracking_id():
    characters = string.ascii_letters + string.digits
    while True:
        tracking_id = ''.join(secrets.choice(characters) for _ in range(12))
        if not Transaction.objects.filter(tracking_id=tracking_id).exists():
            return tracking_id


"""generate receipt pdf."""
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
        [Paragraph(transaction.project.created_by.institution_name, styles['TitleStyle']), ""],
        '',
        [Paragraph(f"NO: {transaction.tracking_id}", styles['BoldStyle']),  # Fixed hardcoded invoice number
         Paragraph(f"DATE: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['RightAlignNormal'])]
        # Formatted the date
    ]
    header_table = Table(header_data, colWidths=[available_width / 2, available_width / 2])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1, spaceAfter=15, spaceBefore=0))

    # --- Details Section (Project, Beneficiary, Tiles, Buyer) ---
    project_beneficiary_data = [
        [
            Paragraph("Project Details", styles['SubtitleStyle']),
            Paragraph("Beneficiary Details", styles['SubtitleStyle']),
        ],
        [
            Paragraph(f"<b>Title:</b> {transaction.project.title}<br/>"
                      f"<b>Starting date:</b> {transaction.project.started_at.strftime('%Y-%m-%d %H:%M:%S')}<br/>"  # Formatted the date
                      f"<b>Created by:</b> {transaction.project.created_by.institution_name}<br/>",
                      # Fixed this bug
                      styles['NormalStyle']),
            Paragraph(
                f"<b>Name:</b> {transaction.project.beneficiary.first_name} {transaction.project.beneficiary.last_name}<br/>"
                f"<b>Phone:</b> {transaction.project.beneficiary.phone_number}<br/>"
                f"<b>Address:</b> {transaction.project.beneficiary.address}<br/>",  # Fixed this bug
                styles['NormalStyle']),
        ]
    ]

    project_beneficiary_table = Table(project_beneficiary_data, colWidths=[available_width / 2, available_width / 2])
    project_beneficiary_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(project_beneficiary_table)
    elements.append(Spacer(1, 10))

    tiles_buyer_data = [
        [
            Paragraph("Tiles Details", styles['SubtitleStyle']),
            Paragraph("Buyer Details", styles['SubtitleStyle']),
        ],
        [
            Paragraph(f"<b>Selected Tiles:</b> {transaction.tiles_bought.tiles}<br/>"
                      f"<b>Quantity:</b> {transaction.num_tiles}<br/>"
                      f"<b>Amount:</b> {transaction.amount}<br/>", styles['NormalStyle']),
            Paragraph(f"<b>Name:</b> {transaction.sender.full_name}<br/>"
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
    elements.append(Paragraph(f'<b>Tracking ID:</b> {transaction.tracking_id}', styles['NormalStyle']))
    elements.append(Paragraph(f'<b>Transaction Date:</b> {transaction.transaction_time.strftime("%Y-%m-%d %H:%M:%S")}',
                              styles['NormalStyle']))  # Formatted the date
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1, spaceAfter=15, spaceBefore=0))

    # --- Notes/Message Section ---
    elements.append(Paragraph("Message", styles['SubtitleStyle']))
    elements.append(Paragraph(transaction.message, styles['NormalStyle']))

    # Build PDF
    doc.build(elements)

    # Reset buffer position to the beginning before returning
    buffer.seek(0)

    return ContentFile(buffer.getvalue(), name=f'{transaction.tracking_id}.pdf')


"""generate report pdf."""
def generate_report_pdf(project, request):
    # A4 page dimensions and margins
    page_width, page_height = A4
    left_margin = 0.75 * inch
    right_margin = 0.75 * inch
    available_width = page_width - left_margin - right_margin


    # Use an in-memory buffer to build the PDF
    buffer = io.BytesIO()

    # Create the PDF document
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=left_margin, rightMargin=right_margin,
                            topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    elements = []

    # --- STYLE DEFINITIONS (Refined) ---
    report_header_style = ParagraphStyle(name='ReportHeader', fontName='Helvetica-Bold', fontSize=16,
                                         textColor=colors.black, alignment=0, spaceAfter=20)
    project_title_style = ParagraphStyle(name='ProjectTitle', fontName='Helvetica-Bold', fontSize=20,
                                         textColor=colors.black, alignment=1, spaceAfter=20)
    section_heading_style = ParagraphStyle(name='SectionHeading', fontName='Helvetica-Bold', fontSize=12,
                                           textColor=colors.HexColor("#444444"), spaceAfter=8, alignment=0,)

    # Text styles
    normal_style = ParagraphStyle(name='Normal', fontName='Helvetica', fontSize=10, leading=14, spaceAfter=8,
                                  alignment=0)
    centered_normal = ParagraphStyle(name='CenteredNormal', fontName='Helvetica', fontSize=10, leading=14,
                                     spaceAfter=12, alignment=1)

    # Metric styles
    metric_label_row_height = 20
    metric_value_row_height = 30
    key_metric_label_style = ParagraphStyle(name='KeyMetricLabel', fontName='Helvetica-Bold', fontSize=11,
                                            textColor=colors.HexColor("#666666"), alignment=1)
    key_metric_value_style = ParagraphStyle(name='KeyMetricValue', fontName='Helvetica-Bold', fontSize=22,
                                            textColor=colors.black, alignment=1,leading=metric_value_row_height)



    # --- PAGE 1: PROJECT DETAILS (Improved Spacing) ---

    # Header and Title Block
    elements.append(Paragraph(project.created_by.institution_name, report_header_style))
    elements.append(Paragraph(project.title, project_title_style))
    elements.append(Spacer(1, 10))

    # Project Description
    elements.append(Paragraph("Project Description", section_heading_style))
    elements.append(Paragraph(project.description, normal_style))
    elements.append(Spacer(1, 18))

    # --- KEY METRICS TABLE ---
    # Retrieve dynamic data (using placeholders for demo)
    funding_goal_formatted = f"Rs.{project.funding_goal}"
    current_amount_formatted = f"Rs.{project.current_amount}"

    funding_metrics_data = [
        [
            Paragraph("Funding Goal", key_metric_label_style),
            Paragraph("Total Raised", key_metric_label_style),
        ],
        [
            Paragraph(funding_goal_formatted, key_metric_value_style),
            Paragraph(current_amount_formatted, key_metric_value_style),
        ]
    ]

    funding_metrics_table = Table(funding_metrics_data, colWidths=[available_width / 2] * 2, rowHeights = [metric_label_row_height, metric_value_row_height])
    funding_metrics_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.7, colors.HexColor("#cccccc")),
    ]))
    elements.append(funding_metrics_table)
    elements.append(Spacer(1, 20))

    # --- TIMELINE & SUMMARY ---
    elements.append(Paragraph("Project Timeline & Funding Summary", section_heading_style))

    # Calculate tiles (approximate for goal, since current tiles are tracked in SelectedTile)
    total_required_tiles = int(project.funding_goal / project.tile_value)

    summary_data = [
        ["Funding Started:", project.started_at.strftime("%Y-%m-%d")],
        ["Funding Closed:", project.closed_by.strftime("%Y-%m-%d") if project.closed_by else "N/A"],
        ["Tile Value:", f"Rs.{project.tile_value:,.2f}"],
        ["Required Tiles to Goal:", f"{total_required_tiles} tiles"],
        ["Funding Status:",
         f"Closed - {'Exceeded Goal' if project.current_amount >= project.funding_goal else 'Goal Not Met'}"],
    ]

    # Create the summary table
    summary_table = Table(summary_data, colWidths=[available_width * 0.5, available_width * 0.5])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # --- ASSOCIATED DETAILS (Institution & Beneficiary) ---
    elements.append(Paragraph("Associated Details", section_heading_style))

    inst_bank = project.created_by.default_bank
    beneficiary = project.beneficiary

    details_data = [
        [
            Paragraph('<b>Beneficiary Details:</b>', normal_style),
            Paragraph('<b>Institution Bank Details:</b>', normal_style),
        ],
        [
            Paragraph(
                f'Name: {beneficiary.first_name} {beneficiary.last_name}<br/>'
                f'Age: {beneficiary.age}<br/>'
                f'Phone: {beneficiary.phone_number or "N/A"}<br/>'
                f'Address: {beneficiary.address}', normal_style),
            Paragraph(
                f'Acc Holder: {inst_bank.account_holder_first_name} {inst_bank.account_holder_last_name}'
                f'Bank Name: {inst_bank.bank_name}<br/>'
                f'IFSC: {inst_bank.ifsc_code or "N/A"}<br/>'
                f'Acc No: {inst_bank.account_no}<br/>',
                normal_style),
        ]
    ]

    details_table = Table(details_data, colWidths=[available_width / 2] * 2, rowHeights=[20, 70])
    details_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#666666")),  # Light green header
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(details_table)
    elements.append(Spacer(1, 20))

    # Footer
    elements.append(Paragraph(
        f'<b>Report Approved by:</b> {request.user.first_name} {request.user.last_name}',
        normal_style
    ))
    elements.append(Paragraph(
        f'<b>Report Generated:</b> {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        normal_style
    ))

    # ------------------------------------------------------------------------------------------------
    elements.append(PageBreak())
    # ------------------------------------------------------------------------------------------------

    # --- PAGE 2: PROJECT IMAGES ---

    elements.append(Paragraph("Project Image Documentation", report_header_style))
    elements.append(Paragraph(f"Visual Documentation for: {project.title}", section_heading_style))
    elements.append(Spacer(1, 10))

    image_paths = []
    for project_image in project.images.filter(table_status=True).all():
        try:
            if project_image.project_img:
                image_paths.append(project_image.project_img.path)
        except Exception as e:
            print(f"Error accessing file path for image {project_image.pk}: {e}")
            continue

    if image_paths:
        image_elements = []
        # Calculate image width to fit two images side-by-side with padding
        img_width = (available_width / 2) - (0.1 * inch)
        img_height = img_width * (3 / 4)  # Assume 4:3 aspect ratio

        for path in image_paths:
            try:
                img = Image(path, width=img_width, height=img_height)
                image_elements.append(img)
            except Exception as e:
                image_elements.append(Paragraph(f"[Image failed to load: {path}]", normal_style))

        # Organize images into a table for grid layout (2 columns)
        image_data = []
        for i in range(0, len(image_elements), 2):
            row = image_elements[i:i + 2]
            # Ensure the row has two elements (add spacer if needed for alignment)
            if len(row) == 1:
                row.append(Spacer(1, 1))
            image_data.append(row)

        image_table = Table(image_data, colWidths=[available_width / 2] * 2)
        image_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        elements.append(image_table)

    else:
        elements.append(Paragraph(
            "**No Project Images Available.**",
            centered_normal
        ))

    # ------------------------------------------------------------------------------------------------
    elements.append(PageBreak())
    # ------------------------------------------------------------------------------------------------

    # --- PAGE 3 ONWARDS: TRANSACTION DETAILS ---

    elements.append(Paragraph("Detailed Transaction Log", report_header_style))
    elements.append(Paragraph(f"Verified Transactions for: {project.title}", section_heading_style))
    elements.append(Spacer(1, 10))

    # Get data
    transactions = Transaction.objects.filter(project=project)

    # 1. Prepare Transaction Table Data
    transaction_table_data = []

    # Header Row
    table_header_style = ParagraphStyle(name='TableHeader', fontName='Helvetica-Bold',
                                        textColor=colors.HexColor("#FFFFFF"), fontSize=9, alignment=1, spaceBefore=0,
                                        spaceAfter=0)

    header = [
        Paragraph("Sl.No", table_header_style),
        Paragraph("Donor Name", table_header_style),
        Paragraph("Tracking ID", table_header_style),
        Paragraph("Date/Time", table_header_style),
        Paragraph("Tiles Qty", table_header_style),
        Paragraph("Amount (Rs.)", table_header_style)
    ]
    transaction_table_data.append(header)

    # Body Rows
    for txn in transactions:
        # Transaction amount (assuming verified)
        amount_val = txn.amount

        row = [
            Paragraph('1', centered_normal),
            Paragraph(txn.sender.full_name, normal_style),
            Paragraph(txn.tracking_id, normal_style),
            Paragraph(txn.transaction_time.strftime("%Y-%m-%d %H:%M"), centered_normal),
            Paragraph(str(len(txn.tiles_bought.tiles.split('-'))), centered_normal),
            Paragraph(f"Rs.{amount_val:,.2f}", normal_style),
        ]
        transaction_table_data.append(row)

    # 2. Define Table Column Widths
    # Total available width is 515 points (A4 - margins)
    col_widths = [
        30,  # S.No
        150,  # Donor Name
        100,  # Tracking ID
        85,  # Date/Time
        60,  # Tiles Qty
        90  # Amount (Rs.)
    ]

    # 3. Create Table Object
    txn_table = Table(transaction_table_data, colWidths=col_widths, repeatRows=1)

    # 4. Define Table Style
    txn_table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#333333")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),

        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),  # Donor Name left aligned
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),  # Tracking ID left aligned
        ('ALIGN', (5, 1), (5, -1), 'RIGHT'),  # Amount right aligned
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f0f0f0')]),

        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
    ])

    txn_table.setStyle(txn_table_style)

    # 5. Add Table to Story
    elements.append(txn_table)

    # 6. Build PDF
    doc.build(elements)

    # Return the file as a ContentFile for Django response
    return ContentFile(buffer.getvalue(), name=f'{project.title}_Report.pdf')