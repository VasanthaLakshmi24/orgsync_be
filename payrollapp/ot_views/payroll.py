import random
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.shortcuts import get_object_or_404
from datetime import datetime,timedelta
from num2words import num2words
from rest_framework.decorators import api_view
from django.http import JsonResponse,HttpResponse
from django.contrib.auth import authenticate
from rest_framework import status
from ..models import *
from ..decorators import *
from ..serializers import *
from ..tasks import *
from rest_framework.views import APIView
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import csv
from django.db import transaction
import jwt
from dotenv import load_dotenv
import os
import calendar
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from decimal import Decimal , ROUND_HALF_UP
import pytz
import json
from django.db.models import Max,Value
from django.db.models.functions import Coalesce
import uuid
from rest_framework.response import Response
from django.db.models import Sum
import pdfkit

from django.shortcuts import render
from django.db.models import Q
import qrcode
from io import BytesIO
from ..utils import *



ist = pytz.timezone('Asia/Kolkata')

load_dotenv()
apiurl=os.environ.get('apiurl')
backendurl=os.environ.get('backendurl')



class NotifyAccountsManagerAPIView(APIView):
    def post(self, request):
        try:
            user = request.user
            month = int(request.data.get('month'))
            year = int(request.data.get('year'))
            childid = request.data.get('childid')

            child = ChildAccount.objects.get(id=childid)

            accounts_manager = Roles.objects.filter(
                parent=child.parent, 
                child=child, 
                name='ACCOUNTS_MANAGER'
            ).first()

            if not accounts_manager:
                return Response(
                    {"error": "No Accounts Manager found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            recipient_email = accounts_manager.user.email  
            subject = f"Payroll Preview for {month}/{year} - Action Required"
            message = f"""
Dear {accounts_manager.user.username},

The payroll preview for {month}/{year} has been generated for {child.name} under {child.parent.orgName}. 
Please review and approve it in the system.

For any issues or questions, feel free to contact the administrator.

Regards,
{user.username}
"""

            sendemail(
                subject=subject,
                message=message,
                recipient_list=[recipient_email],
            )
            
            Notification.objects.create(sender=user,receiver=accounts_manager.user,message=message)

            return Response(
                {"message": "Email notification sent to Accounts Manager."},
                status=status.HTTP_200_OK
            )

        except ChildAccount.DoesNotExist:
            return Response(
                {"error": "Child account not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PreviewPayrollAPIView(APIView):
    def post(self,request):
        try:
            user = request.user
            child_id = request.data.get('childid')
            child = ChildAccount.objects.get(id=child_id)
            month = int(request.data.get('month'))
            year = int(request.data.get('year'))
            payrollobjs = EmployeePayroll.objects.filter(child=child,parent=child.parent,year=year,status="Preview",month=month)
            serializer = EmployeePayrollSerializer(payrollobjs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def put(self, request):
        try:
            with transaction.atomic():
                user = request.user
                child_id = request.data.get('childid')
                child = ChildAccount.objects.get(id=child_id)
                month = int(request.data.get('month'))
                year = int(request.data.get('year'))
                stat = request.data.get('status')
                payrollobjs = EmployeePayroll.objects.filter(
                    child=child, 
                    parent=child.parent, 
                    year=year, 
                    status="Preview", 
                    month=month
                )
                if stat == "Approved":
                    for payrollobj in payrollobjs:
                        payrollobj.status = "Approved"
                        payrollobj.save()
                        # subject = f"Payslip generated for {month}/{year}"
                        # message = f"""
                        # Dear {payrollobj.employee.userName},

                        # The payrolls for the period {month}/{year} have been successfully approved.
                        # Please check the system for your payslip.
                        # """

                        # recipient_email = payrollobj.employee.email
                        # sendemail(
                        #     subject=subject,
                        #     message=message,
                        #     recipient_list=[recipient_email],
                        # )
                    subjectr = f"Payroll status update for {month}/{year}"
                    messager = f"""
                    Dear Manager,

                    The payrolls for {child.name} for the period {month}/{year} have been approved

                    Please address the issue and resubmit for approval.

                    Regards,
                    {user.username}
                    """
                    payrollmanager = Roles.objects.get(parent = child.parent,child = child,name = "PAYROLL_MANAGER").user
                    sendemail(
                        subject=subjectr,
                        message=messager,
                        recipient_list=[payrollmanager.email],
                        )
                else:
                    reason = request.data.get('reason')
                    subjectr = f"Payroll status update for {month}/{year}"
                    messager = f"""
                    Dear Manager,

                    The payrolls for {child.name} for the period {month}/{year} have been rejected for the following reason:

                    {reason}

                    Please address the issue and resubmit for approval.

                    Regards,
                    {user.username}
                    """
                    payrollmanager = Roles.objects.get(parent = child.parent,child = child,name = "PAYROLL_MANAGER").user
                    sendemail(
                    subject=subjectr,
                    message=messager,
                    recipient_list=[payrollmanager.email],
                    )
            return Response({"message": "Payrolls status updated successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ValidateQR(APIView):
    def get(self, request):
        code = request.GET.get('code') 
        
        if not code:
            return Response({'error': 'Code is required'}, status=400)

        try:
            payroll_obj = EmployeePayroll.objects.filter(id=code).exclude(status="Preview").first()
        except EmployeePayroll.DoesNotExist:
            return Response({'error': 'Invalid code or payroll not found'}, status=404)
        
        serializer = EmployeePayrollSerializer(payroll_obj)

        return Response({'message': 'Code is valid', 'payroll': serializer.data}, status=200)

def updateLeaveBal(employee,month,year):
    leaves =len(Attendance.objects.filter(employee=employee,date__month=month,date__year=year,status="leave")) 
    absent=len(Attendance.objects.filter(employee=employee,date__month=month,date__year=year,status="absent"))
    leavebalanceobj=LeaveBalance.objects.get(employee=employee,month=month,year=year)
    leavebalanceobj.lop =max(0,leaves+absent-leavebalanceobj.current_leave_balance)
    newlb=max(0,leavebalanceobj.current_leave_balance-leaves-absent)
    leavebalanceobj.current_leave_balance=newlb
    leavebalanceobj.save()

class PayCalculator(APIView):
    def post(self,request):
        user = request.user
        employeeobj = Employee.objects.get(user = user)
        parent = employeeobj.parent
        childId = request.data.get('childid',None)
        month = request.data.get('month',None)
        year = request.data.get('year',None)
        if childId:
            child = ChildAccount.objects.get(id=childId)
            employees = Employee.objects.filter(parent = parent,main_child=child,status='onroll')
            at_type = child.attendanceType
        else:
            employees = Employee.objects.filter(parent = parent,status='onroll')
        with transaction.atomic():
            for employee in employees:
                updateLeaveBal(employee=employee,month=int(month),year=int(year))
                empleaves =len(Attendance.objects.filter(employee=employee,date__month=month,date__year=year,status="leave")) 
                absent=len(Attendance.objects.filter(employee=employee,date__month=month,date__year=year,status="absent"))
                present = len(Attendance.objects.filter(
                    employee=employee,
                    date__month=month,
                    date__year=year,
                    status__in=["latelogin", "present", "halfday"]
                ))

                no_leaves = empleaves+absent

                leave_obj = LeaveBalance.objects.get(employee = employee,month=month,year=year)
                bonus=leave_obj.bonus
                advance=leave_obj.advance
                lop = leave_obj.lop
                # if at_type == 'punch':
                #     latelogins = Attendance.objects.filter(employee=employee,status='latelogin',date__month = month,date__year=year)
                #     lateloginreq = LateLoginRequestObject.objects.filter(employee=employee,status='approved',Date__month=month,Date__year = year)
                    # if len(latelogins)>0:
                    #     lop += (len(latelogins)-len(lateloginreq))//3
                    # if (len(latelogins)-len(lateloginreq))//3 >0:
                    #     if ((len(latelogins)-len(lateloginreq))%3)%2 == 0 :
                    #         lop += decimal.Decimal(0.50)
                    # leave_obj.lop=lop

                leave_obj.save()

                allowances = Allowance.objects.filter(child=child, parent=parent)
                allowances_dict = {allowance.name: allowance.min_value for allowance in allowances}

                
                basic_val = 0
                if(employee.emp_type == 'Blue-Collar'):
                    prodemppayobj = ProdEmployeePay.objects.get(employee=employee)
                    basic_vall = prodemppayobj.per_day_wage * present
                    pf_deduction = prodemppayobj.employer_pf * present
                    esi_deduction = prodemppayobj.employer_esi * present
                    tax_deduction = 0
                    lop = 0
                    if basic_vall <= 15000:
                        tax_deduction = 0
                    elif basic_vall <= 20000:
                        tax_deduction = 150
                    else:
                        tax_deduction = 200

                    employee_esi = prodemppayobj.employee_esi * present
                    allowances = EmployeeProdAllowance.objects.filter(employee=employee,allowance__type = 'allowance')
                    deductions = EmployeeProdAllowance.objects.filter(employee=employee,allowance__type = 'deduction')
                    allowances_dict = {allowance.allowance.name: (allowance.amount * present) for allowance in allowances}
                    deductions_dict = {deduction.allowance.name: (deduction.amount * present) for deduction in deductions}
                    allowancejson = json.dumps(allowances_dict, cls=DecimalEncoder)
                    deductionsjson = json.dumps(deductions_dict, cls=DecimalEncoder)
                    gross_salary = basic_vall + sum(allowances_dict.values())
                    net_salary = gross_salary - pf_deduction - employee_esi + bonus - advance - sum(deductions_dict.values()) - tax_deduction
                    try:
                        obj = EmployeePayroll.objects.get(employee=employee,parent=parent,child=child,month=month,year=year)
                        obj.delete()
                    except:
                        pass
                    EmployeePayroll.objects.create(
                        employee=employee,
                        parent=parent,
                        child=child,
                        month=month,
                        year=year,
                        lop = lop,
                        present=present,
                        no_leaves = no_leaves,
                        gross=gross_salary,
                        basic_salary=basic_vall,
                        allowances = allowancejson,
                        deductions = deductionsjson,
                        pf_deduction=pf_deduction,
                        employer_pf=pf_deduction,
                        employer_esi=esi_deduction,
                        esi_deduction=employee_esi,
                        net_salary=net_salary,
                        tax_deduction=tax_deduction
                    )
                else:
                    ctc = EmployeePay.objects.get(employee=employee).ctc
                    newctc = (ctc)*Decimal(1-(lop/30))
                    basic_val = EmployeePay.objects.get(employee=employee).basic
                    newbasic = (newctc/ctc) * basic_val
                    result = balance_allowances(
                        ctc=Decimal(newctc),
                        basic_value=newbasic,
                        basic_type="amount",
                        allowance_percentages=allowances_dict,
                        pf=newbasic*Decimal(0.12),
                    )

                    allowances = result["Allowances"]
                    allowancejson = json.dumps(allowances, cls=DecimalEncoder)
                    gross_salary = result["FinalSummary"]["GrossSalary"]
                    basic_salary = result["FinalSummary"]["BasicSalary"]

                    if gross_salary <= 15000:
                        tax_deduction = 0
                    elif gross_salary <= 20000:
                        tax_deduction = 150
                    else:
                        tax_deduction = 200
                    if result["Deductions"]["ESI"] > 0:
                        employee_esi = gross_salary*Decimal(0.0075)
                    else:
                        employee_esi = 0
                    net_salary = gross_salary - result["Deductions"]["PF"] - employee_esi + bonus - advance

                    net_salary -= tax_deduction
                    try:
                        obj = EmployeePayroll.objects.get(employee=employee,parent=parent,child=child,month=month,year=year)
                        obj.delete()
                    except:
                        pass
                    EmployeePayroll.objects.create(
                        employee=employee,
                        parent=parent,
                        child=child,
                        month=month,
                        present=present,
                        year=year,
                        lop = lop,
                        no_leaves = no_leaves,
                        gross=gross_salary,
                        basic_salary=basic_salary,
                        allowances = allowancejson,
                        pf_deduction=result["Deductions"]["PF"],
                        employer_pf=result["Deductions"]["PF"],
                        employer_esi=result["Deductions"]["ESI"],
                        esi_deduction=employee_esi,
                        net_salary=net_salary,
                        tax_deduction=tax_deduction
                    )
            updateLeaveBalAfterPayroll(parent=parent,child=child,month=int(month),year=int(year))
        return Response({'message':"Success"},status=status.HTTP_200_OK)

class PayrollCSVExport(APIView):
    def post(self, request, *args, **kwargs):
        child_id = request.data.get('childId')
        month = request.data.get('month')
        year = request.data.get('year')

        try:
            child = ChildAccount.objects.get(id=child_id)
            payrolls = EmployeePayroll.objects.filter(child=child, month=month, year=year,).exclude(status="Preview").select_related('employee__department', 'employee__designation')

            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="payroll_data.csv"'

            writer = csv.writer(response)

            header = [
                'Employee ID','UAN','ESIC Number','Employee Name', 'Department', 'Designation',
                'Year', 'Month','Basic'
            ]

            allowance_names = set()

            for payroll in payrolls:
                allowances = payroll.allowances
                if isinstance(allowances, str):
                    allowances = json.loads(allowances)
                allowance_names.update(allowances.keys())

            header.extend(allowance_names)

            header.extend([
                'Employee Gross', 'PF Deduction', 'ESI Deduction',
                'PT', 'Total Deductions(Employee)', 'Employer PF', 'Employer ESI',
                'Total Company Contribution','Net Salary'
            ])

            writer.writerow(header)

            totals = {
                "employee_gross": Decimal(0), 
                "total_basic": Decimal(0),
                "total_allowances": Decimal(0),
                "total_deductions": Decimal(0),
                "total_pf": Decimal(0),
                "total_esi": Decimal(0),
                "total_pt": Decimal(0),
                "employer_pf": Decimal(0),
                "employer_esi": Decimal(0),
                "employer_contributions": Decimal(0)
            }

            for payroll in payrolls:
                employee = payroll.employee
                empbd = EmployeeBasicDetails.objects.get(employee=employee)
                uan = empbd.pfAccountNumber if empbd.pfAccountNumber else ''
                esic = empbd.esiAccountNumber if empbd.esiAccountNumber else ''
                allowances = payroll.allowances
                if isinstance(allowances, str):
                    allowances = json.loads(allowances)
                row = [
                    employee.employeeid,
                    uan,
                    esic,
                    employee.userName,
                    employee.department.name if employee.department else '',
                    employee.designation.name if employee.designation else '',
                    payroll.year,
                    payroll.month,
                    payroll.basic_salary
                ]

                allowance_values = [Decimal(allowances.get(name, 0)) for name in allowance_names]  
                row.extend(allowance_values)

                total_allowance_value = sum(allowance_values)
                
                net_salary = payroll.net_salary
                
                total_deductions = payroll.pf_deduction + payroll.esi_deduction + payroll.tax_deduction

                row.extend([
                    payroll.gross,
                    payroll.pf_deduction,
                    payroll.esi_deduction,
                    payroll.tax_deduction,
                    total_deductions,
                    payroll.employer_pf,
                    payroll.employer_esi,
                    payroll.employer_pf + payroll.employer_esi,
                    net_salary
                ])

                writer.writerow(row)
                
                totals["employee_gross"] += payroll.gross
                totals["total_basic"] += payroll.basic_salary
                totals["total_allowances"] += total_allowance_value
                totals["total_pf"] += payroll.pf_deduction
                totals["total_esi"] += payroll.esi_deduction
                totals["total_pt"] += payroll.tax_deduction
                totals["total_deductions"] += total_deductions
                totals["employer_pf"] += payroll.employer_pf
                totals["employer_esi"] += payroll.employer_esi
            
            total_row = [
                'Total', '', '', '', '', '', totals["employee_gross"], totals["total_basic"]
            ]
            total_row.extend([totals["total_allowances"]])
            total_row.extend([
                totals["total_basic"] + totals["total_allowances"],
                totals["total_pf"], totals["total_esi"], totals["total_pt"],
                totals["total_deductions"], totals["employer_pf"],
                totals["employer_esi"], totals["employer_pf"] + totals["employer_esi"]
            ])

            writer.writerow(total_row)

            return response

        except ChildAccount.DoesNotExist:
            return Response({'error': 'ChildAccount does not exist'}, status=status.HTTP_404_NOT_FOUND)
        except json.JSONDecodeError:
            return Response({'error': 'Invalid JSON format in allowances'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DisplayPayrollAPIView(APIView):
    def post(self, request):
        user = request.user
        month = int(request.data.get('month'))
        year = int(request.data.get('year'))
        childid = request.data.get('childid')
        child = ChildAccount.objects.get(id=childid)
        if user:
            payroll = EmployeePayroll.objects.filter(month=month,year=year,child=child,parent=child.parent)
            serializer = EmployeePayrollSerializer(payroll, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Login to continue"}, status=status.HTTP_404_NOT_FOUND)


class PayslipView(APIView):
    def post(self, request):
        user = request.user
        month = int(request.data['month'])
        year = int(request.data['year'])
        employee = Employee.objects.get(user=user)
        emp = EmployeePayroll.objects.filter(employee=employee, month=month, year=year).exclude(status="Preview").first()

        working_days = MonthlyData.objects.get(parent=employee.parent, child=employee.main_child, year=year, month=month).no_of_working_days
        lobj = LeaveBalance.objects.get(employee=employee, month=month, year=year)
        bonus = lobj.bonus
        advance = lobj.advance
        leaves = len(Attendance.objects.filter(employee=employee, date__month=month, date__year=year, status="leave")) + len(Attendance.objects.filter(employee=employee, date__month=month, date__year=year, status="absent"))
        present_days = working_days - leaves
        
        if(emp.present and emp.present > 0):
            present_days = emp.present

        basic_salary = emp.basic_salary
        allowances = emp.allowances
        deductions = emp.deductions
        esi_deduction = emp.esi_deduction
        pf_deduction = emp.pf_deduction
        tax_deduction = emp.tax_deduction
        net_salary = emp.net_salary
        amount_words = num2words(net_salary).capitalize()
        company_name = employee.parent.orgName
        company_address = employee.parent.address
        empbasicdet = EmployeeBasicDetails.objects.get(employee=employee)
        empbankdet = EmployeeBankDetails.objects.get(employee=employee)
        pan = empbasicdet.panCardNumber
        pf = empbasicdet.pfAccountNumber
        esic = empbasicdet.esiAccountNumber
        employee_address = empbasicdet.communicationAddress

        payslip_det = PayrollPolicy.objects.get(child=employee.main_child, parent=employee.parent)
        emp_type = 'Full Time' if employee.type == "full_time" else 'Part Time' if employee.type == "part_time" else 'Contract' if employee.type == "contract" else "Intern" if employee.type == "intern" else "N/A"

        s_all = 0
        if allowances:
            allowances = json.loads(allowances)
            s_all = sum(allowances.values())
        else:
            allowances = None
        d_all = 0
        if deductions:
            deductions = json.loads(deductions)
            d_all = sum(deductions.values())
        else:
            deductions = None

        api_url = f"{apiurl}/validatepayslip/{emp.id}"
        qr = qrcode.make(api_url)

        buffered = BytesIO()
        if(deductions):
            leng = ['']*(len(allowances.items()) - len(deductions.items()) - 1)
            aleng = ['']*(len(deductions.items()) - len(allowances.items()) + 2 - 1)
        else:
            leng = ['']*(len(allowances.items()) - 1)
            aleng = ['']*(2 - 1)

        qr.save(buffered, format='PNG')
        qr_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
        header_url = None
        if payslip_det.payslipHeaderlogo:
            header_url = backendurl + payslip_det.payslipHeaderlogo.url
        template_context = {
            'month': calendar.month_name[month],
            'year': year,
            'header_logo': header_url,
            'header_name': payslip_det.payslipHeaderCompany,
            'header_tagline': payslip_det.payslipHeadertagline,
            'header_address': payslip_det.payslipHeaderAddress,
            'employee': employee,
            'working_days': working_days,
            'present_days': int(present_days),
            'loss': int(emp.lop),
            'basic_salary': currencyInIndiaFormat(basic_salary),
            'allowances': allowances,
            'deductions': deductions,
            'uan': pf,
            'esic': esic,
            'pan': pan,
            'leng':leng,
            'aleng':aleng,
            'emp_type': emp_type,
            'company_name': company_name,
            'company_address': company_address,
            'employee_address': employee_address,
            'bonus': currencyInIndiaFormat(bonus),
            'advance': currencyInIndiaFormat(advance),
            'esi_deduction': currencyInIndiaFormat(esi_deduction),
            'empbankdet': empbankdet,
            'pf_deduction': currencyInIndiaFormat(pf_deduction),
            'tax_deduction': currencyInIndiaFormat(tax_deduction),
            'net_salary': currencyInIndiaFormat(net_salary),
            'amount_words': amount_words,
            'total_earnings': currencyInIndiaFormat(basic_salary + Decimal(s_all) + bonus),
            'total_deductions': currencyInIndiaFormat(tax_deduction + Decimal(d_all) + esi_deduction + pf_deduction + advance),
            'qr_code': qr_image
        }
        
        if(emp.employee.emp_type == 'Blue-Collar'):
            
            payslip_html = render_to_string('blue_pay.html', template_context)
        else:
            payslip_html = render_to_string('pay.html', template_context)

        return Response({'payslip_html': payslip_html}, status=status.HTTP_200_OK)

class PayslipEmailView(APIView):
    def post(self, request):
        user = request.user
        payslip_html = request.data.get('payslip_html')
        pdfkit_config = pdfkit.configuration(wkhtmltopdf=settings.PDFKIT_CONFIG['wkhtmltopdf'])
        pdf = pdfkit.from_string(payslip_html, False, configuration=pdfkit_config, options=settings.PDFKIT_CONFIG['options'])
        pdf_filename = f"payslip.pdf"
        email = EmailMessage(
            'Your Payslip',
            'Please find attached your payslip for the month.',
            '',
            [user.email]
        )
        email.attach(pdf_filename, pdf, 'application/pdf')
        email.send()
        
        return Response({'message': 'Mail sent successfully.'}, status=status.HTTP_200_OK)

def updateLeaveBalAfterPayroll(parent,month,year,child=None):
    employees=Employee.objects.filter(parent=parent,main_child=child)
    for employee in employees:
        leavepolicy=LeavePolicy.objects.get(parent=parent,child=child).leaves_per_year
        leavebalanceobj=LeaveBalance.objects.get(employee=employee,parent=parent,child=child,month=month,year=year)
        if month>12:
            next_month=1
            next_year=year+1
        else:
            next_month=month+1
            next_year=year
        newlbobj=LeaveBalance.objects.create(employee=employee,parent=parent,child=child,month=next_month,year=next_year)
        newlbobj.carry_forwarded_leave_balance=leavebalanceobj.current_leave_balance
        newlbobj.current_leave_balance=leavebalanceobj.current_leave_balance + decimal.Decimal(leavepolicy/12)
        newlbobj.save()

class PayrollInfo(APIView):
    def post(self,request):
        user=request.user 
        parent=Employee.objects.get(user=user).parent
        childid=request.data['childid']
        month=int(request.data['month'])
        year=int(request.data['year'])
        child=ChildAccount.objects.get(id=childid)
        employees=Employee.objects.filter(main_child=child,parent=parent)
        data=[]
        for employee in employees:
            empdata={}
            empdata['employee']=employee.userName
            empdata['id']=employee.id
            empdata['childid']=child.id
            empdata['parentid']=parent.id
            empdata['ctc']=employee.ctc
            empdata['parent']=employee.parent.orgName 
            try:
                leave_balance_obj=LeaveBalance.objects.get(employee=employee,month=month,year=year,parent=parent,child=child)
            except:
                leave_balance_obj=LeaveBalance.objects.create(employee=employee,month=month,year=year,parent=parent,child=child)
                if child:
                    leavePolicy = LeavePolicy.objects.get(parent = parent,child=child)
                else:
                    leavePolicy = LeavePolicy.objects.get(parent = parent)
                leave_balance_obj.carry_forwarded_leave_balance=leavePolicy.leaves_per_year/12
                leave_balance_obj.current_leave_balance=leavePolicy.leaves_per_year/12
                leave_balance_obj.save()
                

            
            empdata['currentleavebalance']=leave_balance_obj.current_leave_balance
            empdata['forwardedleavebalance']=leave_balance_obj.carry_forwarded_leave_balance
            empdata['bonus']=leave_balance_obj.bonus
            empdata['advance']=leave_balance_obj.advance
            if child:
                empdata['child']=child.name
            empdata['leaves']=len(Attendance.objects.filter(employee=employee,child=child,parent=parent,date__month=month,date__year=year,status="leave"))
            empdata['absent']=len(Attendance.objects.filter(employee=employee,child=child,parent=parent,date__month=month,date__year=year,status="absent"))
            data.append(empdata)
        return Response({'data':data},status=status.HTTP_200_OK)
    
    def put(self, request):
        try:
            user = request.user
            ip = get_client_ip(request)
            childid = request.data['childid']
            child = ChildAccount.objects.get(id=childid)
            id = request.data['id']
            month = request.data['month']
            year = request.data['year']
            employee = Employee.objects.get(id=id)
            leavebalance = Decimal(request.data['currentleavebalance'])
            carry_leave_balance = Decimal(request.data['forwardedleavebalance'])
            bonus = int(request.data['bonus'])
            advance = int(request.data['advance'])
            ctc = Decimal(request.data['ctc'])
            prev_ctc = employee.ctc
            
            employee.ctc = ctc
            employee.save()
            
            lb = LeaveBalance.objects.get(employee=employee, month=month, year=year,parent=child.parent,child=child)
            prev_lb = lb.current_leave_balance
            prev_advances = lb.advance
            prev_bonus = lb.bonus
            
            lb.current_leave_balance = leavebalance 
            lb.carry_forwarded_leave_balance = carry_leave_balance
            lb.advance = advance
            lb.bonus = bonus
            lb.save()
            lb.refresh_from_db()

            lb = LeaveBalance.objects.get(employee=employee, month=month, year=year)

            comments = request.data.get("comments")
            data = (f"{request.user.username} Updated the Paydetails of the employee {employee.userName} \n"
                    f"Leave Balance: {prev_lb} to {leavebalance} \n"
                    f"CTC: {prev_ctc} to {ctc} \n"
                    f"Advances: {prev_advances} to {advance} \n"
                    f"Bonus: {prev_bonus} to {bonus} \n")
            log = ActivityLog.objects.create(parent=child.parent, child=child, user=user, 
                                            data=data, ip_address=ip, reason=comments)
            return Response({'data': "Updated Successfully"}, status=status.HTTP_200_OK)
        
        except Exception as e:
            print(f"An error occurred: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class GetAvailYearsMonths(APIView):
    def post(self, request):
        user = request.user
        employee = Employee.objects.get(user=user)
        empobjs = EmployeePayroll.objects.filter(employee=employee).exclude(status="Preview").order_by('year', 'month')
        monthsdata = {}
        for obj in empobjs:
            if obj.year not in monthsdata:
                monthsdata[obj.year] = []
            monthsdata[obj.year].append(obj.month)
        return Response({'data': monthsdata}, status=status.HTTP_200_OK)
