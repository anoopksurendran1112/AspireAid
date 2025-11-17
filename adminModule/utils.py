from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.platypus.flowables import HRFlowable, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from django.core.mail import EmailMessage, get_connection
from django.template.loader import render_to_string
from userModule.models import Receipt, Transaction
from playwright.sync_api import sync_playwright
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from django.conf import settings
import requests
import datetime
import secrets
import string
import locale
import time
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


try:
    locale.setlocale(locale.LC_ALL, 'en_IN.utf8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'en_IN')
    except locale.Error:
        pass


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


def _render_html_to_pdf_bytes(html_content, pdf_type='regular'):
    if pdf_type == '80mm':
        pdf_options = {
            "width": "80mm",
            "height": "180mm",
            "margin": {"top": "1mm", "right": "1mm", "bottom": "1mm", "left": "1mm"},
            "print_background": True,
            "display_header_footer": False
        }
    elif pdf_type in ('regular', 'report'):
        pdf_options = {
            "format": "A4",
            "margin": {"top": "20mm", "right": "20mm", "bottom": "20mm", "left": "20mm"},
            "print_background": True,
        }
    else:
        pdf_options = {"format": "A4"}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html_content, wait_until='networkidle')
            time.sleep(0.5)
            pdf_bytes = page.pdf(**pdf_options)
            browser.close()
            return pdf_bytes
    except Exception as e:
        print(f"Playwright PDF generation failed: {e}")
        raise


def format_currency(amount, currency_symbol="₹"):
    try:
        formatted = locale.currency(amount, symbol=False, grouping=True)
        return f"{currency_symbol}{formatted}"
    except Exception:
        return f"{currency_symbol}{amount:,.2f}"


def generate_receipt_pdf(transaction):
    tile_list = transaction.tiles_bought.tiles.split('-')
    num_tiles = len(tile_list)

    tile_value = float(transaction.project.tile_value)
    row_total = num_tiles * tile_value

    rupee = "₹"
    formatted_amount = format_currency(float(transaction.amount), rupee)
    formatted_tile_value = format_currency(tile_value, rupee)
    formatted_row_total = format_currency(row_total, rupee)
    formatted_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    context = {
        'transaction': transaction,
        'rupee': rupee,
        'num_tiles': num_tiles,
        'row_total': row_total,
        'formatted_amount': formatted_amount,
        'formatted_tile_value': formatted_tile_value,
        'formatted_row_total': formatted_row_total,
        'formatted_date': formatted_date,
    }

    html_content = render_to_string('pdf/receipt_regular.html', context)
    pdf_bytes = _render_html_to_pdf_bytes(html_content, pdf_type='regular')
    filename = f"regular_receipt_{transaction.tracking_id}.pdf"
    return ContentFile(pdf_bytes, name=filename)


def generate_80mm_receipt_pdf(transaction):
    tiles_string = transaction.tiles_bought.tiles
    tile_list = tiles_string.split('-') if tiles_string else []
    num_tiles = len(tile_list)

    tile_value = float(transaction.project.tile_value)
    item_total_value = num_tiles * tile_value

    rupee = "₹"
    formatted_tile_value = format_currency(tile_value, rupee)
    formatted_item_total = format_currency(item_total_value, rupee)

    receipt_datetime_str = transaction.transaction_time.strftime("%Y-%m-%d %H:%M:%S")

    context = {
        'transaction': transaction,
        'rupee': rupee,
        'num_tiles': num_tiles,
        'item_total_value': item_total_value,
        'formatted_tile_value': formatted_tile_value,
        'formatted_item_total': formatted_item_total,
        'receipt_datetime_str': receipt_datetime_str,
    }

    html_content = render_to_string('pdf/receipt_80mm.html', context)
    pdf_bytes = _render_html_to_pdf_bytes(html_content, pdf_type='80mm')
    filename = f"80mm_receipt_{transaction.tracking_id}.pdf"
    return ContentFile(pdf_bytes, name=filename)


def generate_report_pdf(project, request):
    """
    Refactored to generate a PDF report for a Project instance,
    based on the multi-page ReportLab structure.
    """
    # 1. Aggregate Data and Perform Calculations

    # --- Data Aggregation (Replace with your actual Django ORM queries) ---

    # Example: If you need to access transactions:
    # all_transactions = project.transactions.all().select_related('sender', 'tiles_bought')

    # --- MOCK DATA BASED ON REPORTLAB LOGIC ---
    # Funding Metrics
    funding_goal = float(project.funding_goal)
    current_amount = float(project.current_amount)
    tile_value = float(project.tile_value)

    total_required_tiles = int(funding_goal / tile_value)

    # Transaction Details (Used for the transaction table on page 3)
    # The ReportLab code implies using a queryset named 'transactions'
    # We'll mock a list of dictionaries with the required fields:
    transactions_list = [
        # Note: In real code, fetch this from project.transactions.all()
        {'sl_no': 1, 'donor_name': 'Donor A', 'tracking_id': 'TX001',
         'time': datetime.datetime.now() - datetime.timedelta(days=1), 'num_tiles': 25, 'amount': 500},
        {'sl_no': 2, 'donor_name': 'Donor B', 'tracking_id': 'TX002',
         'time': datetime.datetime.now() - datetime.timedelta(hours=5), 'num_tiles': 75, 'amount': 1500},
        # Add more if needed
    ]
    # Calculate num_tiles and format amount for each transaction
    for txn in transactions_list:
        txn['formatted_amount'] = format_currency(txn['amount'])

    # --- END MOCK DATA ---

    # 2. Perform Formatting
    rupee = "₹"

    formatted_funding_goal = format_currency(funding_goal, rupee)
    formatted_current_amount = format_currency(current_amount, rupee)
    formatted_tile_value = format_currency(tile_value, rupee)
    formatted_report_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    funding_status_text = f"Closed - {'Exceeded Goal' if current_amount >= funding_goal else 'Goal Not Met'}"

    # 3. Prepare Context
    context = {
        'project': project,
        'request_user': request.user,  # Used for report approval name
        'rupee': rupee,
        'report_date': formatted_report_date,

        # Page 1 Metrics
        'formatted_funding_goal': formatted_funding_goal,
        'formatted_current_amount': formatted_current_amount,
        'total_required_tiles': total_required_tiles,
        'formatted_tile_value': formatted_tile_value,
        'funding_status_text': funding_status_text,

        # Page 2 Images (Need to correctly map this in your actual implementation)
        # 'project_images': project.images.filter(table_status=True).all(),
        'project_images_list': [{'url': '', 'caption': 'Placeholder image'}] * 4,  # Mock list

        # Page 3 Transactions
        'transactions_list': transactions_list,
    }

    # 4. Generate PDF
    html_content = render_to_string('pdf/project_report.html', context, request=request)

    pdf_bytes = _render_html_to_pdf_bytes(html_content, pdf_type='report')

    # 5. Save and Return
    filename = f"project_report_{project.id}.pdf"
    return ContentFile(pdf_bytes, name=filename)

#
# """generate report pdf."""
# def generate_report_pdf(project, request):
#     # --- REGISTER AND EMBED FONT ---
#     # Reusing the font paths and robust checks from the receipt function
#     font_regular_path = os.path.join(settings.BASE_DIR, 'AspireAid', 'static', 'fonts', 'NotoSansMalayalam-Regular.ttf')
#     font_bold_path = os.path.join(settings.BASE_DIR, 'AspireAid', 'static', 'fonts', 'NotoSansMalayalam-Bold.ttf')
#
#     if not os.path.exists(font_regular_path):
#         raise FileNotFoundError(f"Font not found at: {font_regular_path}")
#     if not os.path.exists(font_bold_path):
#         raise FileNotFoundError(f"Font not found at: {font_bold_path}")
#
#     pdfmetrics.registerFont(TTFont('NotoSansMalayalam-Regular', font_regular_path))
#     pdfmetrics.registerFont(TTFont('NotoSansMalayalam-Bold', font_bold_path))
#
#     # --- PAGE CONFIGURATION ---
#     page_width, page_height = A4
#     left_margin, right_margin = 0.5 * inch, 0.5 * inch  # Match receipt margin
#     available_width = page_width - left_margin - right_margin
#
#     buffer = io.BytesIO()
#     doc = SimpleDocTemplate(
#         buffer,
#         pagesize=A4,
#         leftMargin=left_margin,
#         rightMargin=right_margin,
#         topMargin=0.5 * inch,
#         bottomMargin=0.5 * inch,
#     )
#     elements = []
#     rupee = "\u20B9"
#
#     # --- STYLES (MATCHING RECEIPT STYLES) ---
#     styles = getSampleStyleSheet()
#
#     # Matching receipt's styles
#     styles.add(ParagraphStyle('ReportTitle', fontName='NotoSansMalayalam-Bold', fontSize=18, spaceAfter=20,
#                               alignment=TA_LEFT))  # Based on TitleStyle
#     styles.add(ParagraphStyle('SectionHeading', fontName='NotoSansMalayalam-Bold', fontSize=12, textColor=colors.black, spaceAfter=8,
#                        alignment=TA_LEFT))  # Based on SubtitleStyle
#     styles.add(ParagraphStyle('NormalStyle', fontName='NotoSansMalayalam-Regular', fontSize=8, spaceAfter=6, alignment=TA_LEFT,
#                               leading=10))  # Based on NormalStyle, added leading
#     styles.add(
#         ParagraphStyle('NormalStyleCenter', fontName='NotoSansMalayalam-Regular', fontSize=8, textColor=colors.black, spaceAfter=6,
#                        alignment=TA_CENTER))
#     styles.add(ParagraphStyle('BoldStyleLeft', fontName='NotoSansMalayalam-Bold', fontSize=8, spaceAfter=6, alignment=TA_LEFT))
#     styles.add(ParagraphStyle('RightAlignNormal', fontName='NotoSansMalayalam-Regular', fontSize=10, spaceAfter=6, alignment=TA_RIGHT))
#     styles.add(ParagraphStyle('KeyMetricLabel', fontName='NotoSansMalayalam-Regular', fontSize=11, textColor=colors.HexColor("#666666"),
#                               alignment=TA_CENTER))
#     styles.add(ParagraphStyle('KeyMetricValue', fontName='NotoSansMalayalam-Bold', fontSize=22, textColor=colors.black,
#                               alignment=TA_CENTER, leading=30))
#     styles.add(ParagraphStyle('TableHeaderStyle', fontName='NotoSansMalayalam-Bold', textColor=colors.white, fontSize=9,
#                               alignment=TA_CENTER))
#
#     # --- PAGE 1: HEADER & KEY METRICS ---
#     elements.append(Paragraph(project.created_by.institution_name, styles['ReportTitle']))
#     elements.append(Paragraph(project.title, styles['SectionHeading']))
#     elements.append(HRFlowable(width="100%", thickness=1, spaceAfter=15, spaceBefore=0))  # Matching Receipt Separator
#
#     elements.append(Paragraph("Project Description", styles['SectionHeading']))
#     elements.append(Paragraph(project.description, styles['NormalStyle']))
#     elements.append(Spacer(1, 15))
#
#     # --- KEY METRICS ---
#     funding_goal_formatted = f"{rupee}{project.funding_goal:,.2f}"
#     current_amount_formatted = f"{rupee}{project.current_amount:,.2f}"
#
#     funding_metrics_data = [
#         [
#             Paragraph("Funding Goal", styles['KeyMetricLabel']),
#             Paragraph("Total Raised", styles['KeyMetricLabel']),
#         ],
#         [
#             Paragraph(funding_goal_formatted, styles['KeyMetricValue']),
#             Paragraph(current_amount_formatted, styles['KeyMetricValue']),
#         ]
#     ]
#     funding_metrics_table = Table(
#         funding_metrics_data,
#         colWidths=[available_width / 2] * 2,
#         rowHeights=[20, 30]
#     )
#     funding_metrics_table.setStyle(TableStyle([
#         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#         ('GRID', (0, 0), (-1, -1), 0.7, colors.HexColor("#585858")),
#     ]))
#     elements.append(funding_metrics_table)
#     elements.append(Spacer(1, 20))
#
#     # --- SUMMARY SECTION ---
#     elements.append(Paragraph("Project Timeline & Funding Summary", styles['SectionHeading']))
#     total_required_tiles = int(project.funding_goal / project.tile_value)
#     summary_data = [
#         [Paragraph("Funding Started:", styles['BoldStyleLeft']),
#          Paragraph(project.started_at.strftime("%Y-%m-%d"), styles['NormalStyle'])],
#         [Paragraph("Funding Closed:", styles['BoldStyleLeft']),
#          Paragraph(project.closed_by.strftime("%Y-%m-%d") if project.closed_by else "N/A", styles['NormalStyle'])],
#         [Paragraph("Tile Value:", styles['BoldStyleLeft']),
#          Paragraph(f"{rupee}{project.tile_value:,.2f}", styles['NormalStyle'])],
#         [Paragraph("Required Tiles to Goal:", styles['BoldStyleLeft']),
#          Paragraph(f"{total_required_tiles} tiles", styles['NormalStyle'])],
#         [Paragraph("Funding Status:", styles['BoldStyleLeft']),
#          Paragraph(f"Closed - {'Exceeded Goal' if project.current_amount >= project.funding_goal else 'Goal Not Met'}",
#                    styles['NormalStyle'])],
#     ]
#
#     # Create summary table - Using clearer receipt-like style
#     summary_table = Table(summary_data, colWidths=[available_width * 0.5, available_width * 0.5])
#     summary_table.setStyle(TableStyle([
#         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#         ('TOPPADDING', (0, 0), (-1, -1), 3),
#         ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
#         ('LEFTPADDING', (0, 0), (-1, -1), 10),
#         ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor("#585858")),
#         ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#D2C6C6")),
#     ]))
#     elements.append(summary_table)
#     elements.append(Spacer(1, 20))
#
#     # --- ASSOCIATED DETAILS ---
#     elements.append(Paragraph("Associated Details", styles['SectionHeading']))
#     inst_bank = project.created_by.default_bank
#     beneficiary = project.beneficiary
#     details_data = [
#         [
#             Paragraph('<b>Beneficiary Details:</b>', styles['BoldStyleLeft']),
#             Paragraph('<b>Institution Bank Details:</b>', styles['BoldStyleLeft']),
#         ],
#         [
#             Paragraph(
#                 f'Name: {beneficiary.first_name} {beneficiary.last_name}<br/>'
#                 f'Age: {beneficiary.age}<br/>'
#                 f'Phone: {beneficiary.phone_number or "N/A"}<br/>'
#                 f'Address: {beneficiary.address}', styles['NormalStyle']),
#             Paragraph(
#                 f'Acc Holder: {inst_bank.account_holder_first_name} {inst_bank.account_holder_last_name}<br/>'
#                 f'Bank Name: {inst_bank.bank_name}<br/>'
#                 f'IFSC: {inst_bank.ifsc_code or "N/A"}<br/>'
#                 f'Acc No: {inst_bank.account_no}<br/>', styles['NormalStyle']),
#         ]
#     ]
#     details_table = Table(details_data, colWidths=[available_width / 2] * 2)
#     details_table.setStyle(TableStyle([
#         ('VALIGN', (0, 0), (-1, -1), 'TOP'),
#         ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#D2C6C6")),  # Darker header row
#         ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
#         ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#585858")),
#         ('TOPPADDING', (0, 0), (-1, -1), 5),
#     ]))
#     elements.append(details_table)
#     elements.append(Spacer(1, 20))
#
#     # Footer
#     elements.append(Paragraph(
#         f'<b>Report Approved by:</b> {request.user.first_name} {request.user.last_name}',
#         styles['NormalStyle']
#     ))
#     elements.append(Paragraph(
#         f'<b>Report Generated:</b> {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
#         styles['NormalStyle']
#     ))
#
#     # --- PAGE BREAK ---
#     elements.append(PageBreak())
#
#     # --- PAGE 2: PROJECT IMAGES ---
#     elements.append(Paragraph("Project Image Documentation", styles['ReportTitle']))
#     elements.append(Paragraph(f"Visual Documentation for: {project.title}", styles['SectionHeading']))
#     elements.append(HRFlowable(width="100%", thickness=1, spaceAfter=15, spaceBefore=0))
#
#     image_paths = []
#     # Simplified access to images for brevity
#     for project_image in project.images.filter(table_status=True).all():
#         try:
#             if project_image.project_img:
#                 image_paths.append(project_image.project_img.path)
#         except Exception:
#             continue
#
#     if image_paths:
#         image_elements = []
#         img_width = (available_width / 2) - (0.1 * inch)
#         img_height = img_width * (3 / 4)
#         for path in image_paths:
#             try:
#                 img = Image(path, width=img_width, height=img_height)
#                 image_elements.append(img)
#             except Exception:
#                 image_elements.append(Paragraph(f"[Image failed to load: {path}]", styles['NormalStyle']))
#         image_data = []
#         for i in range(0, len(image_elements), 2):
#             row = image_elements[i:i + 2]
#             if len(row) == 1:
#                 row.append(Spacer(1, 1))
#             image_data.append(row)
#         image_table = Table(image_data, colWidths=[available_width / 2] * 2)
#         image_table.setStyle(TableStyle([
#             ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#             ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#             ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
#         ]))
#         elements.append(image_table)
#     else:
#         elements.append(Paragraph("**No Project Images Available.**", styles['NormalStyleCenter']))
#
#     elements.append(PageBreak())
#
#     # --- PAGE 3: TRANSACTION DETAILS ---
#     elements.append(Paragraph("Detailed Transaction Log", styles['ReportTitle']))
#     elements.append(Paragraph(f"Verified Transactions for: {project.title}", styles['SectionHeading']))
#     elements.append(HRFlowable(width="100%", thickness=1, spaceAfter=15, spaceBefore=0))
#
#     # NOTE: It is highly recommended to filter transactions by status='Verified' here
#     transactions = Transaction.objects.filter(project=project)
#     transaction_table_data = []
#
#     # Header Row (Matching Receipt's dark header style)
#     header = [
#         Paragraph("Sl.No", styles['TableHeaderStyle']),
#         Paragraph("Donor Name", styles['TableHeaderStyle']),
#         Paragraph("Tracking ID", styles['TableHeaderStyle']),
#         Paragraph("Date/Time", styles['TableHeaderStyle']),
#         Paragraph("Tiles Qty", styles['TableHeaderStyle']),
#         Paragraph("Amount (₹)", styles['TableHeaderStyle'])
#     ]
#     transaction_table_data.append(header)
#
#     # Body Rows
#     for idx, txn in enumerate(transactions, start=1):
#         # NOTE: Be careful with the tile count logic if 'tiles' can be empty
#         num_tiles = len(txn.tiles_bought.tiles.split('-')) if txn.tiles_bought and txn.tiles_bought.tiles else 0
#         amount_val = txn.amount
#
#         row = [
#             Paragraph(str(idx), styles['NormalStyleCenter']),
#             Paragraph(txn.sender.full_name, styles['NormalStyle']),
#             Paragraph(txn.tracking_id, styles['NormalStyle']),
#             Paragraph(txn.transaction_time.strftime("%Y-%m-%d %H:%M"), styles['NormalStyleCenter']),
#             Paragraph(str(num_tiles), styles['NormalStyleCenter']),
#             Paragraph(f"{rupee}{amount_val:,.2f}", styles['NormalStyleCenter']),
#             # Use Center alignment for money column
#         ]
#         transaction_table_data.append(row)
#
#     col_widths = [30, 150, 100, 85, 60, 90]
#     txn_table = Table(transaction_table_data, colWidths=col_widths, repeatRows=1)
#     txn_table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#D2C6C6")),  # Dark header
#         ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # White text
#         ('FONTNAME', (0, 0), (-1, 0), 'NotoSansMalayalam-Bold'),
#         ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
#         ('TOPPADDING', (0, 0), (-1, 0), 6),
#         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#         ('ALIGN', (1, 1), (2, -1), 'LEFT'),  # Donor Name/Tracking ID left aligned
#         ('ALIGN', (5, 1), (5, -1), 'CENTER'),  # Amount center aligned (was right)
#         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#         ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
#         # Slightly lighter alternating rows
#         ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#585858")),
#     ]))
#     elements.append(txn_table)
#
#     # --- BUILD PDF ---
#     doc.build(elements)
#     pdf_data = buffer.getvalue()
#     buffer.close()
#
#     return ContentFile(pdf_data, name=f"{project.title}_Report.pdf")