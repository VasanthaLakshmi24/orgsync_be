from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
import string
import random
from django.core.mail import EmailMessage
import decimal
from decimal import Decimal , ROUND_HALF_UP
import json
from datetime import datetime,timedelta
from payrollapp.models import DocumentAccessRule, Employee



def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip



def get_day_of_week(year, month, day):
    date_obj = datetime(year, month, day)
    return date_obj.strftime('%A')

def get_last_date_of_month(year, month):
    if month == 12:
        last_date = datetime(year, month, 31)
    else:
        last_date = datetime(year, month + 1, 1) + timedelta(days=-1)
    return last_date.strftime("%Y-%m-%d")


def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    subject = 'OTP Verification'
    message = f'Your OTP is: {otp}'
    from_email = ''
    to_email = email
    email = EmailMessage(subject, message, from_email, [to_email])
    email.send()




def currencyInIndiaFormat(n):
    d = decimal.Decimal(str(n))
    if d.as_tuple().exponent < -2:
        s = str(n)
    else:
        s = '{0:.2f}'.format(n)
    l = len(s)
    i = l-1;
    res = ''
    flag = 0
    k = 0
    while i>=0:
        if flag==0:
            res = res + s[i]
            if s[i]=='.':
                flag = 1
        elif flag==1:
            k = k + 1
            res = res + s[i]
            if k==3 and i-1>=0:
                res = res + ','
                flag = 2
                k = 0
        else:
            k = k + 1
            res = res + s[i]
            if k==2 and i-1>=0:
                res = res + ','
            flag = 2
            k = 0
        i = i - 1
    return res[::-1]

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def SubscriptionAmount(total_months,no_of_employees,no_of_childs,feature):
        BASE_PRICE = 60
        PAYROLL_PRICE = 5
        LEAVE_PRICE = 2
        PER_CHILD = 100
        TOTAL_MONTHS = total_months
        NO_OF_EMPLOYEES = no_of_employees
        NO_OF_CHILDS = no_of_childs
        if(feature == 'BASIC'):
            DAILY_AMOUNT = ((BASE_PRICE) * NO_OF_EMPLOYEES) + (PER_CHILD * NO_OF_CHILDS)
        elif(feature == 'PMS'):
            DAILY_AMOUNT = ((BASE_PRICE + PAYROLL_PRICE ) * NO_OF_EMPLOYEES) + (PER_CHILD * NO_OF_CHILDS)
        elif(feature == 'LMS'):
            DAILY_AMOUNT = ((BASE_PRICE + LEAVE_PRICE ) * NO_OF_EMPLOYEES) + (PER_CHILD * NO_OF_CHILDS)
        else:
            DAILY_AMOUNT = ((BASE_PRICE + PAYROLL_PRICE + LEAVE_PRICE) * NO_OF_EMPLOYEES) + (PER_CHILD * NO_OF_CHILDS)
        MONTHLY_AMOUNT = DAILY_AMOUNT * 30
        FINAL_PRICE = MONTHLY_AMOUNT * TOTAL_MONTHS
        return FINAL_PRICE

def subtract_times(time1, time2):
    hours_diff = time1.hour - time2.hour
    minutes_diff = time1.minute - time2.minute
    if minutes_diff < 0:
        hours_diff -= 1
        minutes_diff += 60
    res = f"{hours_diff} : {minutes_diff}"
    return res


def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits
    password = ''.join(random.choice(characters) for _ in range(length))
    return password


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



def balance_allowances(ctc, basic_value, basic_type, allowance_percentages, pf):
    result = {}
    monthly_ctc = Decimal(ctc) / Decimal(12)

    if basic_type == 'percentage':
        basic = (Decimal(basic_value) / Decimal(100)) * monthly_ctc
    elif basic_type == 'amount':
        basic = Decimal(basic_value)

    hra_percentage = Decimal(50)
    hra = (hra_percentage / Decimal(100)) * basic

    remaining_ctc_for_allowances = monthly_ctc - basic - hra -pf

    allowance_amounts = {}
    if remaining_ctc_for_allowances > 0:
        total_allowance_percentage = Decimal(sum(allowance_percentages.values()))
        for allowance, percentage in allowance_percentages.items():
            allowance_amounts[allowance] = (Decimal(percentage)/100) * remaining_ctc_for_allowances

    allowance_amounts['HRA'] = hra

    gross_salary = basic + sum(allowance_amounts.values())

    esi = (Decimal(3.25) / Decimal(100)) * gross_salary if gross_salary <= Decimal(21000) else Decimal(0)

    while True:
        total_deductions = pf + esi
        new_gross_salary = monthly_ctc - total_deductions
        new_esi = (Decimal(3.25) / Decimal(100)) * new_gross_salary if new_gross_salary <= Decimal(21000) else Decimal(0)

        
        if new_gross_salary == gross_salary and new_esi == esi:
            break

        gross_salary = new_gross_salary
        esi = new_esi

    remaining_ctc_for_allowances = gross_salary - basic - hra 

    if remaining_ctc_for_allowances > 0:
        total_allowance_percentage = Decimal(sum(allowance_percentages.values()))
        for allowance, percentage in allowance_percentages.items():
            allowance_amounts[allowance] = (Decimal(percentage)/100) * remaining_ctc_for_allowances
    allowance_amounts['HRA'] = hra
    result['Deductions'] = {"PF": pf, "ESI": esi.quantize(Decimal('1.'), rounding=ROUND_HALF_UP),"Total" : total_deductions.quantize(Decimal('1.'), rounding=ROUND_HALF_UP)}

    
    result['FinalSummary'] = {
        'GrossSalary': gross_salary.quantize(Decimal('1.'), rounding=ROUND_HALF_UP),
        'BasicSalary': basic.quantize(Decimal('1.'), rounding=ROUND_HALF_UP),
        'Sumofallallowances': sum(allowance_amounts.values()).quantize(Decimal('1.'), rounding=ROUND_HALF_UP),
        'FinalPF': pf.quantize(Decimal('1.'), rounding=ROUND_HALF_UP)
    }

    
    result['Allowances'] = {k: v.quantize(Decimal('1.'), rounding=ROUND_HALF_UP) for k, v in allowance_amounts.items()}

    return result

def get_roles_list(user):
    """
    Always return roles as a Python list.
    Handles string, list, None safely.
    """
    roles = user.get_roles()

    if not roles:
        return []

    if isinstance(roles, str):
        return [r.strip() for r in roles.split(",") if r.strip()]

    return list(roles)


def can_verify_document(user, employee):
    try:
        my_employee = Employee.objects.get(user=user)
    except Employee.DoesNotExist:
        return False

    roles = list(
        my_employee.roles.values_list("name", flat=True)
    )
    roles = [r.strip().lower() for r in roles]

    # HR_Admin always allowed
    if "hr_admin" in roles:
        return True

    return DocumentAccessRule.objects.filter(
        function__iexact="Document Verification",
        specific_action__iexact="Verify",
        role__in=roles,
        target_employee=employee,
        access__iexact="Access"
    ).exists()
