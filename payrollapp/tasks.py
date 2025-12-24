from datetime import *
from django.utils import timezone
from celery import shared_task
from datetime import timedelta
from .models import *
import logging
from django.conf import settings
import random
from .serializers import *
import os
import calendar
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from collections import defaultdict
logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
from django.core.mail import send_mail, EmailMessage
from .models import DocumentVerification, Employee, Document


def sendemail(subject, message, recipient_list):
    email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
    email.send()
    return True


def sendemailTemplate(subject, template_name, context, recipient_list):
    html_content = render_to_string(template_name, context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, recipient_list)
    email.attach_alternative(html_content, "text/html")
    email.send()
    return True

@shared_task(bind=True)
def GenerateQuote(request):
    quotes=len(Quotes.objects.all())
    quote=random.randint(0,quotes-1)
    for parent in Organization.objects.all():
        parent.quote=QuoteSerializer(Quotes.objects.get(id=quote)).data['quote']
        parent.save()

@shared_task(bind=True)
def checkpending(request):
    pendingrequests=leaves.objects.filter(status='pending')
    for leave_request in pendingrequests:
        hours = (datetime.now(timezone.utc) - leave_request.timeStamp).total_seconds() / 3600
        from_date_as_datetime = datetime.combine(leave_request.fromDate, time.min)
        timeleft = (from_date_as_datetime - datetime.now(timezone.utc)).total_seconds() / 3600

        try:
            leaveforwardingpolicy = LeaveApprovalFlow.objects.get(parent=leave_request.parent,child=leave_request.child)
            leavepolicy = LeavePolicy.objects.get(parent=leave_request.parent,child=leave_request.child)
            auto_approval = leavepolicy.autoApproval
            if auto_approval == True:
                autoApprovalBefore = leavepolicy.autoApprovalBefore
                if timeleft < autoApprovalBefore and hours >= autoApprovalBefore:
                    leave_request.status = 'approved'
                    leave_request.save()
                    notification_message = f"The leave request for the employee {leave_request.employee} from {leave_request.fromDate} to {leave_request.toDate} has been approved automatically by the system as the status has not beed modified till date."
                    sendemail("Leave Request Auto Approved", notification_message, [leave_request.approvingPerson.email,leave_request.child.HrHead.email])
                    leave_request.save()
                    subject = f'Leave Status'
                    message = f'Your leave request from {leave_request.fromDate} to {leave_request.toDate}. \nThis leave request has beed auto approved by the system.'
                    sendemail(subject, message,  [leave_request.employee.email])
                    return

            is_forwarded = leaveforwardingpolicy.leaveForwarding
            leave_upto = leaveforwardingpolicy.leaveForwardingUpto
            for_hours = leaveforwardingpolicy.leaveForwarAfer
        except:
            is_forwarded = False
            leaveforwardingpolicy = None
            for_hours = 0
            return

        if leave_upto == 'HR':
            if leave_request.approvingPerson == leave_request.child.HrHead:
                return
        if leave_upto == 'BO':
            if leave_request.approvingPerson == leave_request.child.bussinessOwner:
                return

        if is_forwarded and hours >= for_hours:
            existing_app = leave_request.approvingPerson
            if 'SUPER_USER' not in existing_app.get_roles():
                existing_app_emp = Employee.objects.get(user = existing_app)
                newApp = existing_app_emp.reported_to
                if newApp:
                    leave_request.approvingPerson = newApp
                    notification_message = f"You have a new leave request from {leave_request.employee} from {leave_request.fromDate} to {leave_request.toDate}. This has been forwared to you since {existing_app.email} has not updated the leave status."
                    notification = Notification.objects.create(sender = leave_request.employee.user,receiver = newApp,message = notification_message)   
                    sendemail("Leave Request", notification_message, [newApp.email])
                    leave_request.save()
                    subject = f'Leave Status'
                    message = f'Your leave request from {leave_request.fromDate} to {leave_request.toDate} is {leave_request.status}. \nThis leave request will be handled by {newApp.email} '
                    sendemail(subject, message,  [leave_request.employee.email])

@shared_task(bind=True)
def checksubstatus(request):
    accounts = Accounts.objects.all()
    for account in accounts:
        today =  datetime.now().date()
        if account.subscriptionEndDate < today:
            account.subscriptionStatus = "inactive"
            account.save()

@shared_task(bind=True)
def update_leaves(request):
    childs = ChildAccount.objects.filter(attendanceType='punch')
    current_date = datetime.today()
    previous_day = current_date - timedelta(days=1)
    previous_day_of_week = previous_day.strftime('%A')

    for child in childs:
        employees = Employee.objects.filter(parent=child.parent, main_child=child)
        year = previous_day.year
        month = previous_day.month

        try:
            attendance_policy = AttendancePolicy.objects.get(parent=child.parent, child=child)
            working_days = attendance_policy.get_workingDays()
        except AttendancePolicy.DoesNotExist:
            working_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

        holidays_in_month = Holidays.objects.filter(
            parent=child.parent,
            child=child,
            date__year=year,
            date__month=month
        ).values_list('date', flat=True)

        for employee in employees:
            leave_days = set()
            optional_holidays = EmployeeOptHoliday.objects.filter(
                holiday__date__month=month,
                holiday__date__year=year,
                employee=employee
            ).values_list('holiday__date', flat=True)
            attobj = Attendance.objects.filter(employee=employee, date=previous_day)
            leaves_queryset = leaves.objects.filter(
                employee=employee,
                parent=employee.parent,
                child=child,
                fromDate__lte=previous_day.replace(day=calendar.monthrange(year, month)[1]).date(),
                toDate__gte=previous_day.replace(day=1).date(),
                status = "approved"
            )

            for leave in leaves_queryset:
                leave_start = max(leave.fromDate, previous_day.date().replace(day=1))
                leave_end = min(leave.toDate, previous_day.replace(day=calendar.monthrange(year, month)[1]).date())
                leave_range = set(range(leave_start.day, leave_end.day + 1))
                leave_days.update(leave_range)
            stat = "absent"
            if previous_day.day in leave_days:
                stat = "leave"
            if previous_day.date() in optional_holidays or previous_day.date() in holidays_in_month or previous_day_of_week not in working_days:
                stat = "holiday"
            if not attobj.exists():
                Attendance.objects.create(
                    employee=employee,
                    parent=employee.parent,
                    child=employee.main_child,
                    logged_in=False,
                    status=stat,
                    date=previous_day
                )
                if stat == "absent":
                    subject = "Attendance Alert !!!"
                    message = f"Dear {employee.userName},\n\nI hope this message finds you well. We noticed that you did not mark your attendance yesterday, and no leave request has been submitted. As a result, your absence has been recorded.\n\nPlease review this at your earliest convenience.\n\nWarm regards,\n{employee.parent.orgName}"
                    sendemail(subject, message,  [employee.email])
                if stat != "holiday":
                    try:
                        empleave, created = EmployeeLeaves.objects.get_or_create(
                            employee=employee,
                            year=year,
                            month=month,
                            child=child,
                            parent=child.parent,
                            defaults={'leaves': 1}
                        )
                        if not created:
                            empleave.leaves += 1
                            empleave.save()
                    except Exception as e:
                        print(f"Error updating leaves for employee {employee.id}: {e}")



@shared_task(bind=True)
def send_greeting(self):
    print("✅ SEND GREETING TASK STARTED")

    today = datetime.today()
    current_month = today.month
    current_day = today.day

    employees = Employee.objects.filter(status="onroll")
    all_employees = Employee.objects.filter(status="onroll")


    for employee in employees:

        print("Checking :", employee.userName, employee.dateOfBirth)

        # ========== BIRTHDAY ==========
        if employee.dateOfBirth and employee.dateOfBirth.month == current_month and employee.dateOfBirth.day == current_day:

                print("🎂 BIRTHDAY MATCH FOUND :", employee.userName)

                # Email
                subject = "Happy Birthday 🎂"
                message = f"Dear {employee.userName},\nHappy Birthday! 🎉\nOn behalf of everyone at {employee.parent.orgName}, we want to extend our warmest wishes to you on your special day. May this day be filled with joy, laughter, and unforgettable moments.\nWe appreciate all your hard work and dedication, and we're grateful to have you as part of our team.\nEnjoy your day to the fullest!\nBest regards,\n{employee.parent.orgName}"

                sendemail(subject, message, [employee.email])

                # Notification to ALL
                for emp in Employee.objects.all():
                    if emp.user:
                        Notification.objects.create(
                            sender=employee.user,
                            receiver=emp.user,
                            message=f"🎂 Today is {employee.userName}'s Birthday! Wish them 🎉"
                        )

        # ========== WORK ANNIVERSARY ==========
        if employee.dateOfJoining:
            if employee.dateOfJoining.month == current_month and employee.dateOfJoining.day == current_day:

                years = today.year - employee.dateOfJoining.year

                print("🎉 WORK ANNIVERSARY FOUND :", employee.userName)

                # Email
                subject = "Happy Work Anniversary 🎉"
                message = f"Dear {employee.userName},\n\nCongratulations on completing {years} years in {employee.parent.orgName} 🎉"
                sendemail(subject, message, [employee.email])

                # Notification to ALL
                for emp in Employee.objects.all():
                    if emp.user:
                        Notification.objects.create(
                            sender=employee.user,
                            receiver=emp.user,
                            message=f"🎉 {employee.userName} completed {years} year(s) today!"
                        )

        # ========== MARRIAGE ANNIVERSARY (Email only) ==========
        employeeGreetings = EmployeeOccasions.objects.filter(
            employee=employee,
            date__month=current_month,
            date__day=current_day,
            type="marriageday"
        )

        if employeeGreetings.exists():

            print("💍 MARRIAGE ANNIVERSARY FOUND :", employee.userName)

            subject = "Happy Marriage Anniversary 💍"
            message = f"Dear {employee.userName},\n\nHappy Marriage Anniversary 💍"
            sendemail(subject, message, [employee.email])



@shared_task(bind=True)
def TriggerEmail(request):
    employees=Employee.objects.all()
    for employee in employees:
        pendinglist=f"Hello {employee.userName}.These Details in your Profile section arePending\n"
        length=len(EmployeeOccasions.objects.filter(employee=employee))
        if length==0:
            pendinglist+=(" your Occassion Details  are Pending\n")
        length=len(EmployeeEducationDetails.objects.filter(employee=employee))

        if length==0:
            pendinglist+=(" your Education Details  are Pending\n")
        length=len(EmployeeRelation.objects.filter(employee=employee))
        if length==0:
            pendinglist+=(" your Relation Details  are Pending\n")
        length=len(EmployeeReference.objects.filter(employee=employee))
        if length==0:
            pendinglist+=(" your Reference Details  are Pending\n")
        length=len(Document.objects.filter(employee=employee))
        if length<3:
            pendinglist+=(" your Document Uploads  are Pending\n")
        pendinglist+="Please Make sure that these details are updated as soon as possible\n"

@shared_task(bind=True)
def TriggerDailyLogin(request):
    for parent in Organization.objects.all():
        for child in ChildAccount.objects.filter(parent=parent,attendanceType='punch'):
            employees=Employee.objects.filter(parent=parent,main_child=child)
            day=datetime.now().strftime("%A")
            date=datetime.today().date()
            try:
                days=AttendancePolicy.objects.get(parent=parent,child=child).get_workingDays()
            except:
                days=[]
            if day in days:
                if date not in Holidays.objects.filter(
                        parent=parent,
                        child=child,
                        date=date
                    ).values_list('date', flat=True):
                    for employee in employees:
                        try:
                            todayatt=Attendance.objects.filter(date=date,employee=employee)
                            if len(todayatt)==0:
                                context = {
                                    'employee': employee,
                                    'login_link': os.environ.get('apiurl')
                                }
                                sendemailTemplate(
                                    'Regarding Login',
                                    'emails/NotLoggedIn.html',
                                    context,
                                    [employee.email]
                                )
                        except:
                            pass

@shared_task(bind=True)
def notifyleave(self):
    pending_requests = leaves.objects.filter(status='pending')
    requests_by_manager = defaultdict(list)
    for leave_request in pending_requests:
        if leave_request.approvingPerson:
            manager = leave_request.approvingPerson
            requests_by_manager[manager].append(leave_request)

    for manager, requests in requests_by_manager.items():
        context = {
            'reported_to': manager.username,  
            'user_data': requests,    
        }

        sendemailTemplate(
            'Pending Leave Requests',
            'emails/PendingLeaveReq.html',
            context,
            [manager.email]
            )


@shared_task
def send_document_verification_email(employee_id):
    """
    Sends an email to the employee summarizing rejected documents and comments.
    Called after verification submit for that employee (or by a view).
    """
    try:
        emp = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return {"error": "employee_not_found"}

    rejected = DocumentVerification.objects.filter(employee=emp, status='REJECTED').order_by('-verified_at')

    if not rejected.exists():
        # send "all accepted" email or skip
        subject = "Document Verification - All documents accepted"
        body = "All your documents have been verified and accepted."
        recipient = [emp.email] if emp.email else []
        if recipient:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipient)
        return {"status": "no_rejected"}

    subject = "Document Verification - Action required"
    # Build a simple body listing rejected docs and comments
    lines = []
    for r in rejected:
        when = r.verified_at.strftime("%Y-%m-%d %H:%M:%S") if r.verified_at else str(r.created_at)
        comment = r.comment or "No comment provided"
        lines.append(f"{r.document_type} ✖ : {comment} (verified by: {getattr(r.verified_by, 'email', '')} on {when})")

    body = "The following documents were rejected. Please re-upload corrected documents:\n\n" + "\n".join(lines)

    recipient = [emp.email] if emp.email else []
    if recipient:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipient)
        return {"status": "sent", "to": recipient}
    return {"status": "no_recipient"}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={'max_retries': 3})
def send_rejection_summary_email(self, employee_id, rejected):
    print("🔥 REJECTION TASK STARTED")

    # ===========================
    # 1️⃣ Get Employee & User
    # ===========================
    try:
        employee = Employee.objects.select_related("user").get(id=employee_id)
    except Employee.DoesNotExist:
        print("❌ Employee not found")
        return "Employee not found"

    if not employee.user:
        print("❌ Employee has no linked user")
        return "Employee has no user"

    user = employee.user
    print("✅ Email Receiver:", user.email)

    # ===========================
    # 2️⃣ Determine Sender
    # ===========================
    sender = (
        employee.parent.HrHead
        if employee.parent and hasattr(employee.parent, "HrHead")
        else user
    )

    # ===========================
    # 3️⃣ Prepare Rejection Text
    # ===========================
    rejected_text = "\n".join(
        [f"• {r['document_type'].upper()} – {r['comment']}" for r in rejected]
    )

    # ===========================
    # 4️⃣ Create Notification
    # ===========================
    with transaction.atomic():
        Notification.objects.create(
            sender=sender,
            receiver=user,
            message=(
                "❌ Documents Rejected\n\n"
                "The following documents require correction:\n\n"
                f"{rejected_text}\n\n"
                "Please re-upload the corrected documents in the HRMS portal."
            )
        )

    print("🔔 Notification created")

    # ===========================
    # 5️⃣ Email Subject
    # ===========================
    subject = "Action Required: Document Verification Update"

    # ===========================
    # 6️⃣ HTML Email Body
    # ===========================
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color:#b71c1c;">Document Verification – Action Required</h2>

        <p>Dear <strong>{user.first_name or user.username}</strong>,</p>

        <p>
          We have reviewed the documents you submitted as part of the verification
          process. Unfortunately, some documents require correction or re-submission.
        </p>

        <hr>

        <h3 style="color:#d32f2f;">❌ Rejected Documents</h3>
        <ul>
          {''.join([
              f"<li><strong>{r['document_type'].upper()}</strong>: {r['comment']}</li>"
              for r in rejected
          ])}
        </ul>

        <hr>

        <h3>Next Steps</h3>
        <ol>
          <li>Review the comments mentioned above.</li>
          <li>Re-upload the corrected documents in the HRMS portal.</li>
          <li>Ensure all documents are valid, clear, and readable.</li>
        </ol>

        <p>
          If you believe this is an error or need assistance, please contact the HR team.
        </p>

        <br>

        <p>Best regards,<br>
        <strong>HR Team</strong></p>

        <p style="font-size:12px;color:#777;">
          This is an automated message. Please do not reply.
        </p>
      </body>
    </html>
    """

    # ===========================
    # 7️⃣ Send Email
    # ===========================
    email = EmailMultiAlternatives(
        subject=subject,
        body="Please view this email in HTML format.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.attach_alternative(html_body, "text/html")
    email.send()

    print("✅ Rejection email sent successfully")
    return "Success"


User = get_user_model()


# =========================================================
# 📧 Helper: Send HTML Certificate Email
# =========================================================
def _send_certificate_email(user, cert, subject, heading, message_line):
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color:#b71c1c;">{heading}</h2>

        <p>Dear <strong>{user.first_name or user.username}</strong>,</p>

        <p>{message_line}</p>

        <hr>

        <h3>📄 Certificate Details</h3>
        <ul>
          <li><strong>Name:</strong> {cert.name}</li>
          <li><strong>Expiry Date:</strong> {cert.expiry_date}</li>
        </ul>

        <hr>

        <h3>Next Steps</h3>
        <ol>
          <li>Renew the certificate.</li>
          <li>Upload the renewed certificate in the HRMS portal.</li>
          <li>Contact HR if assistance is needed.</li>
        </ol>

        <p>Best regards,<br>
        <strong>HR Team</strong></p>

        <p style="font-size:12px;color:#777;">
          This is an automated message. Please do not reply.
        </p>
      </body>
    </html>
    """

    email = EmailMultiAlternatives(
        subject=subject,
        body="Please view this email in HTML format.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.attach_alternative(html_body, "text/html")
    email.send()


# =========================================================
# 🔔 Main Task: Certification Expiry Notifications
# =========================================================
@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=10, retry_kwargs={"max_retries": 3})
def certification_expiry_notification(self):
    print("🔥 CERTIFICATION EXPIRY TASK STARTED")

    today = timezone.localdate()
    alert_30 = today + timedelta(days=30)
    alert_7 = today + timedelta(days=7)
    alert_1 = today + timedelta(days=1)

    # =====================================================
    # 👤 FIXED HR USER LOOKUP  ✅ (THIS SOLVES YOUR ERROR)
    # =====================================================
    hr_user = (
        User.objects.filter(hr_head=True).first()
        or User.objects.filter(is_superuser=True).first()
    )

    # =====================================================
    # 📄 Fetch Certifications
    # =====================================================
    certs = EmployeeCertifications.objects.filter(
        expiry_date__isnull=False
    ).select_related("employee__user")

    for cert in certs:
        user = cert.employee.user if cert.employee else None
        if not user:
            continue

        expiry_date = cert.expiry_date

        # =========================
        # 🔔 30 DAYS BEFORE
        # =========================
        if expiry_date == alert_30 and not cert.notified_30_days:
            msg = f"⏳ Your certificate '{cert.name}' will expire on {expiry_date} (30 days remaining)."

            Notification.objects.create(
                sender=hr_user,
                receiver=user,
                message=msg
            )

            _send_certificate_email(
                user=user,
                cert=cert,
                subject="Certificate Expiry Reminder – 30 Days",
                heading="Certificate Expiry Reminder",
                message_line="Your certificate will expire in 30 days. Please renew it in advance."
            )

            cert.notified_30_days = True
            cert.save(update_fields=["notified_30_days"])

        # =========================
        # ⚠️ 7 DAYS BEFORE
        # =========================
        if expiry_date == alert_7 and not cert.notified_7_days:
            msg = f"⚠️ Your certificate '{cert.name}' will expire in 7 days on {expiry_date}."

            Notification.objects.create(
                sender=hr_user,
                receiver=user,
                message=msg
            )

            _send_certificate_email(
                user=user,
                cert=cert,
                subject="Urgent: Certificate Expiry in 7 Days",
                heading="Urgent Certificate Expiry Reminder",
                message_line="Your certificate will expire in 7 days. Immediate action is required."
            )

            cert.notified_7_days = True
            cert.save(update_fields=["notified_7_days"])

        # =========================
        # 🚨 1 DAY BEFORE
        # =========================
        if expiry_date == alert_1 and not cert.notified_1_day:
            msg = f"🚨 Your certificate '{cert.name}' expires tomorrow ({expiry_date})."

            Notification.objects.create(
                sender=hr_user,
                receiver=user,
                message=msg
            )

            _send_certificate_email(
                user=user,
                cert=cert,
                subject="Final Reminder: Certificate Expiry Tomorrow",
                heading="Final Certificate Expiry Reminder",
                message_line="Your certificate will expire tomorrow. Please renew immediately."
            )

            cert.notified_1_day = True
            cert.save(update_fields=["notified_1_day"])

        # =========================
        # ❌ ON EXPIRY DAY
        # =========================
        if expiry_date == today and not cert.notified_on_expiry:
            msg = f"❌ Your certificate '{cert.name}' expires TODAY ({today})."

            Notification.objects.create(
                sender=hr_user,
                receiver=user,
                message=msg
            )

            _send_certificate_email(
                user=user,
                cert=cert,
                subject="Certificate Expired Today",
                heading="Certificate Expired",
                message_line="Your certificate has expired today. Please upload the renewed certificate immediately."
            )

            cert.notified_on_expiry = True
            cert.save(update_fields=["notified_on_expiry"])

        # =========================
        # ⚠️ AFTER EXPIRY (ONCE)
        # =========================
        if expiry_date < today and not cert.notified_after_expiry:
            msg = f"⚠️ Your certificate '{cert.name}' expired on {expiry_date}. Immediate action required."

            Notification.objects.create(
                sender=hr_user,
                receiver=user,
                message=msg
            )

            _send_certificate_email(
                user=user,
                cert=cert,
                subject="Certificate Expired – Action Required",
                heading="Expired Certificate",
                message_line="Your certificate has expired. Upload a renewed certificate to remain compliant."
            )

            cert.notified_after_expiry = True
            cert.save(update_fields=["notified_after_expiry"])

    print("✅ CERTIFICATION EXPIRY TASK COMPLETED")
    return "SUCCESS"

