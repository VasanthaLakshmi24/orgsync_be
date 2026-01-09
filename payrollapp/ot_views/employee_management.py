from rest_framework import status
from ..models import *
from ..decorators import *
from ..serializers import *
from ..tasks import *
from rest_framework.response import Response
from ..utils import *
from rest_framework.views import APIView
from decimal import Decimal , ROUND_HALF_UP
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import csv
from django.db import transaction



class basicDetails(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request, *args, **kwargs):
        user = request.user
        empobj = Employee.objects.get(user = user)
        firstName = request.data.get("firstName") or None
        lastName = request.data.get("lastName") or None
        middleName = request.data.get("middleName") or None
        communicationAddress = request.data.get("communicationAddress") or None
        permanentAddress = request.data.get("permanentAddress") or None
        aadharNumber = request.data.get("aadharNumber") or None
        if aadharNumber is not None:
            aadharNumber = int(aadharNumber)
        panCardNumber = request.data.get("panCardNumber") or None
        if panCardNumber is not None:
            panCardNumber = panCardNumber
        bloodGroup = request.data.get("bloodGroup") or None
        healthIssues = request.data.get("healthIssues") or None
        pfAccountNumber = request.data.get("pfAccountNumber") or None
        esiAccountNumber = request.data.get("esiAccountNumber") or None
        gratuityNumber = request.data.get("gratuityNumber") or None
        healthInsuranceNumber = request.data.get("healthInsuranceNumber") or None
        obj = EmployeeBasicDetails.objects.get(employee = empobj)
        obj.firstName = firstName or obj.firstName
        obj.lastName = lastName or obj.lastName
        obj.middleName = middleName or obj.middleName
        obj.communicationAddress = communicationAddress or obj.communicationAddress
        obj.permanentAddress = permanentAddress or obj.permanentAddress
        obj.aadharNumber = aadharNumber or obj.aadharNumber
        obj.panCardNumber = panCardNumber or obj.panCardNumber
        obj.bloodGroup = bloodGroup or obj.bloodGroup
        obj.healthIssues = healthIssues or obj.healthIssues
        obj.pfAccountNumber = pfAccountNumber or obj.pfAccountNumber
        obj.gratuityNumber = gratuityNumber or obj.gratuityNumber
        obj.esiAccountNumber = esiAccountNumber or obj.esiAccountNumber
        obj.healthInsuranceNumber = healthInsuranceNumber or obj.healthInsuranceNumber
        obj.is_editable = True
        obj.save()
        return Response({'message':'Updated Successfully'},status=status.HTTP_200_OK)
    def get(self,request,**kwargs):
        user = request.user
        empobj = Employee.objects.get(user=user)
        employee_basic_details = EmployeeBasicDetails.objects.get(employee = empobj)
        data = {
            "firstName" : employee_basic_details.firstName,
            "lastName" : employee_basic_details.lastName,
            "middleName" : employee_basic_details.middleName,
            "communicationAddress" : employee_basic_details.communicationAddress,
            "permanentAddress" : employee_basic_details.permanentAddress,
            "aadharNumber" : employee_basic_details.aadharNumber,
            "panCardNumber" : employee_basic_details.panCardNumber,
            "bloodGroup" : employee_basic_details.bloodGroup,
            "healthIssues" : employee_basic_details.healthIssues,
            "pfAccountNumber" : employee_basic_details.pfAccountNumber,
            "esiAccountNumber" : employee_basic_details.esiAccountNumber,
            "healthInsuranceNumber" : employee_basic_details.healthInsuranceNumber,
            "gratuityNumber" : employee_basic_details.gratuityNumber,
            "is_editable" : employee_basic_details.is_editable
        }
        return Response({'data':data},status=status.HTTP_200_OK)

class GetbasicDetails(APIView):
    def post(self,request,**kwargs):
        id= request.data['id']
        empobj = Employee.objects.get(id=id)
        employee_basic_details = EmployeeBasicDetails.objects.get(employee = empobj)
        data = {
            "firstName" : employee_basic_details.firstName,
            "lastName" : employee_basic_details.lastName,
            "middleName" : employee_basic_details.middleName,
            "communicationAddress" : employee_basic_details.communicationAddress,
            "permanentAddress" : employee_basic_details.permanentAddress,
            "aadharNumber" : employee_basic_details.aadharNumber,
            "panCardNumber" : employee_basic_details.panCardNumber,
            "bloodGroup" : employee_basic_details.bloodGroup,
            "healthIssues" : employee_basic_details.healthIssues,
            "pfAccountNumber" : employee_basic_details.pfAccountNumber,
            "esiAccountNumber" : employee_basic_details.esiAccountNumber,
            "healthInsuranceNumber" : employee_basic_details.healthInsuranceNumber,
            "gratuityNumber" : employee_basic_details.gratuityNumber,
            "is_editable" : employee_basic_details.is_editable
        }
        return Response({'data':data},status=status.HTTP_200_OK)

class GetbankDetails(APIView):
    def post(self,request,**kwargs):
        id= request.data['id']
        empobj = Employee.objects.get(id=id)
        employeebank = EmployeeBankDetails.objects.get(employee=empobj)
        serializer = EmployeeBankDetailsSerializer(employeebank)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)


class CalculateRem(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        child_id = request.data.get('child_id')
        ctc = Decimal(request.data.get('ctc'))
        basic = Decimal(request.data.get('basic'))
        pf = Decimal(request.data.get('pf'))
        basic_type = request.data.get('basic_type')
        if child_id:
            try:
                child = ChildAccount.objects.get(id=child_id)
                parent = child.parent
            except ChildAccount.DoesNotExist:
                return Response({"error": "Child account not found."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                emp = Employee.objects.get(user=user)
                parent = emp.parent
                child = None
            except Employee.DoesNotExist:
                return Response({"error": "Employee not found."}, status=status.HTTP_400_BAD_REQUEST)
        allowances = Allowance.objects.filter(child=child, parent=parent)
        allowances_dict = {allowance.name: allowance.min_value for allowance in allowances}
        result = balance_allowances(ctc, basic, basic_type, allowances_dict, pf)

        return Response(result, status=status.HTTP_200_OK)
    
def createobjs(request):
    employees= Employee.objects.all()
    for employee in employees:
        EmployeePay.objects.create(employee=employee,ctc=employee.ctc,gross=employee.ctc/Decimal(12),basic=employee.ctc/Decimal(24),employer_pf = employee.ctc*Decimal(0.12/24),employer_esi = 0.00)




class OnboardProdEmployee(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        childId = request.data.get('childId', None)

        try:
            parent = Organization.objects.get(regUser=user)
        except Organization.DoesNotExist:
            try:
                userEmp = Employee.objects.get(user=user)
                parent = userEmp.parent
            except Employee.DoesNotExist:
                return Response({"error": "Parent organization or employee not found."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            child = ChildAccount.objects.get(id=childId)
        except ChildAccount.DoesNotExist:
            child = None

        designationId = request.data.get("designation", None)
        empid = request.data.get("empid")
        departmentId = request.data.get("department", None)
        reported_to_id = request.data.get("reported_to", None)
        reported_to = None
        if reported_to_id:
            try:
                reported_to = Employee.objects.get(id=reported_to_id).user
            except Employee.DoesNotExist:
                return Response({"error": "Reported-to employee not found."}, status=status.HTTP_400_BAD_REQUEST)

        designation = Designation.objects.get(id=designationId) if designationId else None
        department = Department.objects.get(id=departmentId) if departmentId else None
        allowances = request.data.get("allowances", [])

        types = 'other'
        gender = request.data.get("gender")
        userName = request.data.get("userName")
        email = request.data.get("email")
        dateOfBirth = request.data.get("dateOfBirth")
        phoneNumber = request.data.get("phoneNumber")
        role = request.data.get("role")
        dateOfJoining = request.data.get("dateOfJoining")
        per_day_wage = request.data.get("per_day_wage")
        employer_pf = request.data.get("pfDeduction")
        employee_pf = request.data.get("emppfDeduction")
        employer_esi = request.data.get("esiDeduction")
        employee_esi = request.data.get("empesiDeduction")
        jobdescription = request.data.get("jobdescription")
        kras = request.data.get("kras")
        careerpath = request.data.get("careerpath")
        labour_cat = request.data.get("labout_cat")

        users = Employee.objects.filter(parent=parent)
        if parent.Account.noOfEmployees <= users.count():
            return Response({"error": f"Your subscribed plan allows you to only create {parent.Account.noOfEmployees} employee accounts."}, status=status.HTTP_400_BAD_REQUEST)

        password = generate_random_password()

        try:
            with transaction.atomic():
                employee = Employee.objects.create(
                    employeeid=empid,
                    careerpath=careerpath,
                    jobdescription=jobdescription,
                    kras=kras,
                    parent=parent,
                    designation=designation,
                    department=department,
                    type=types,
                    gender=gender,
                    userName=userName,
                    labour_category=labour_cat,
                    emp_type = 'Blue-Collar',
                    email=email,
                    dateOfBirth=dateOfBirth,
                    phoneNumber=phoneNumber,
                    dateOfJoining=dateOfJoining,
                    ctc=per_day_wage
                )

                empsalary = ProdEmployeePay.objects.create(
                    employee=employee,
                    per_day_wage = per_day_wage,
                    employer_esi=employer_esi,
                    employer_pf=employer_pf,
                    employee_esi=employee_esi,
                    employee_pf=employee_pf
                )

                for allowance_data in allowances:
                    allowance_name = allowance_data.get("name")
                    allowance_amount = allowance_data.get("value")
                    if allowance_name != 'HRA':
                        allowance = ProductionAllowance.objects.get(parent=parent, child=child, name=allowance_name)
                        EmployeeProdAllowance.objects.create(allowance=allowance, employee=employee, amount=allowance_amount)

                employee.child.add(child)
                employee.main_child = child
                if child:
                    leavePolicy = LeavePolicy.objects.get(parent=parent, child=child)
                else:
                    leavePolicy = LeavePolicy.objects.get(parent=parent)

                leave_balance = leavePolicy.leaves_per_year / 12 if leavePolicy else 0
                LeaveBalance.objects.create(employee=employee, parent=parent, child=child, current_leave_balance=leave_balance)

                EmployeeOccasions.objects.create(parent=parent, child=child, employee=employee, type="birthday", date=dateOfBirth)

                if reported_to:
                    employee.reported_to = reported_to
                else:
                    employee.reported_to = request.user
                employee.save()

                new_user_name = employee.userName.replace(" ", "_")
                account = User.objects.create_user(username=new_user_name, email=email, password=password)
                employee.user = account
                employee.save()

                if role == 'BUSINESS_OWNER':
                    givenrole = Roles.objects.get_or_create(name=role, parent=parent, child=child, user=account)[0]
                    child.bussinessOwner = account
                    child.save()
                    account.save()
                elif role != 'EMPLOYEE':
                    bo = userEmp.reported_to
                    RoleRequests.objects.create(sender=user, receiver=bo, role=role, parent=parent, child=child, user=account)
                    notification_message = f"Dear {bo.username}, {userEmp.userName} has requested approval to add {userName} as {role} in our organization."
                    Notification.objects.create(sender=user, receiver=bo, message=notification_message)

                welcome_message = f"Dear {userName}, your account has been created. Username: {account.email}, Password: {password}. Please login at https://www.gaorgsync.com."
                sendemail('Account Created', welcome_message, [account.email])

            return Response({"message": "Employee onboarded successfully"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)




# class OnboardEmployee(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         user = request.user
#         childId = request.data.get('childId', None)

#         try:
#             parent = Organization.objects.get(regUser=user)
#         except Organization.DoesNotExist:
#             try:
#                 userEmp = Employee.objects.get(user=user)
#                 parent = userEmp.parent
#             except Employee.DoesNotExist:
#                 return Response({"error": "Parent organization or employee not found."}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             child = ChildAccount.objects.get(id=childId)
#         except ChildAccount.DoesNotExist:
#             child = None

#         designationId = request.data.get("designation", None)
#         empid = request.data.get("empid")
#         departmentId = request.data.get("department", None)
#         reported_to_id = request.data.get("reported_to", None)
#         reported_to = None
#         if reported_to_id:
#             try:
#                 reported_to = Employee.objects.get(id=reported_to_id).user
#             except Employee.DoesNotExist:
#                 return Response({"error": "Reported-to employee not found."}, status=status.HTTP_400_BAD_REQUEST)

#         designation = Designation.objects.get(id=designationId) if designationId else None
#         designation_name = designation.name.upper() if designation else None
#         is_c_level = designation_name in ["CEO", "CTO", "CFO", "CHRO", "CMO"]

#         department = Department.objects.get(id=departmentId) if departmentId else None
#         allowances = request.data.get("allowances", [])

#         types = request.data.get("type")
#         gender = request.data.get("gender")
#         userName = request.data.get("userName")
#         email = request.data.get("email")
#         dateOfBirth = request.data.get("dateOfBirth")
#         phoneNumber = request.data.get("phoneNumber")
#         role = request.data.get("role")
#         dateOfJoining = request.data.get("dateOfJoining")
#         ctc = request.data.get("ctc")
#         gross = request.data.get("grossSalary")
#         basic = request.data.get("basicSalary")
#         employer_pf = request.data.get("pfDeduction")
#         employer_esi = request.data.get("esiDeduction")
#         jobdescription = request.data.get("jobdescription")
#         kras = request.data.get("kras")
#         careerpath = request.data.get("careerpath")

#         users = Employee.objects.filter(parent=parent)
#         if parent.Account.noOfEmployees <= users.count():
#             return Response({"error": f"Your subscribed plan allows you to only create {parent.Account.noOfEmployees} employee accounts."}, status=status.HTTP_400_BAD_REQUEST)

#         password = generate_random_password()

#         try:
#             with transaction.atomic():
#                 employee = Employee.objects.create(
#                     employeeid=empid,
#                     careerpath=careerpath,
#                     jobdescription=jobdescription,
#                     kras=kras,
#                     parent=parent,
#                     designation=designation,
#                     department=department,
#                     type=types,
#                     gender=gender,
#                     userName=userName,
#                     email=email,
#                     dateOfBirth=dateOfBirth,
#                     phoneNumber=phoneNumber,
#                     dateOfJoining=dateOfJoining,
#                     ctc=ctc
#                 )

#                 empsalary = EmployeePay.objects.create(
#                     employee=employee,
#                     basic=basic,
#                     gross=gross,
#                     ctc = ctc,
#                     employer_esi=employer_esi,
#                     employer_pf=employer_pf
#                 )

#                 for allowance_data in allowances:
#                     allowance_name = allowance_data.get("name")
#                     allowance_amount = allowance_data.get("value")
#                     if allowance_name != 'HRA':
#                         allowance = Allowance.objects.get(parent=parent, child=child, name=allowance_name)
#                         EmployeeAllowance.objects.create(allowance=allowance, employee=employee, amount=allowance_amount)

#                 employee.child.add(child)
#                 employee.main_child = child
#                 if child:
#                     leavePolicy = LeavePolicy.objects.get(parent=parent, child=child)
#                 else:
#                     leavePolicy = LeavePolicy.objects.get(parent=parent)

#                 leave_balance = leavePolicy.leaves_per_year / 12 if leavePolicy else 0
#                 LeaveBalance.objects.create(employee=employee, parent=parent, child=child, current_leave_balance=leave_balance)

#                 EmployeeOccasions.objects.create(parent=parent, child=child, employee=employee, type="birthday", date=dateOfBirth)

#                 # if reported_to:
#                 #     employee.reported_to = reported_to
#                 # else:
#                 #     employee.reported_to = request.user
#                 # employee.save()
#                  # ================= REPORTING LOGIC =================
#                 designation_name = designation.name.upper() if designation else None
#                 if role == "BUSINESS_OWNER":
#                     employee.reported_to = None
#                 elif designation_name == "CEO":
#                     business_owner_emp = Employee.objects.filter( parent=parent, user=parent.regUser).first()
#                     if business_owner_emp:
#                         employee.reported_to = business_owner_emp.user
#                     elif designation_name in ["CTO", "CFO", "CHRO", "CMO"]:
#                         ceo_emp = Employee.objects.filter(parent=parent, designation__name__iexact="CEO").first()
#                         if not ceo_emp:
#                             return Response( {"error": "CEO must be created before adding other C-Level executives"},
#                                             status=status.HTTP_400_BAD_REQUEST )
#                             employee.reported_to = ceo_emp.user
#                         else:
#                             if reported_to:
#                                 employee.reported_to = reported_to
#                             else:
#                                 employee.reported_to = None
#                                 employee.save()

#                 if role == 'BUSINESS_OWNER':
#                     givenrole = Roles.objects.get_or_create(name=role, parent=parent, child=child, user=account)[0]
#                     child.bussinessOwner = account
#                     child.save()
#                     account.save()
#                 elif role != 'EMPLOYEE':
#                     bo = userEmp.reported_to
#                     RoleRequests.objects.create(sender=user, receiver=bo, role=role, parent=parent, child=child, user=account)
#                     notification_message = f"Dear {bo.username}, {userEmp.userName} has requested approval to add {userName} as {role} in our organization."
#                     Notification.objects.create(sender=user, receiver=bo, message=notification_message)

#                 welcome_message = f"Dear {userName}, your account has been created. Username: {account.email}, Password: {password}. Please login at https://www.gaorgsync.com."
#                 sendemail('Account Created', welcome_message, [account.email])

#             return Response({"message": "Employee onboarded successfully"}, status=status.HTTP_201_CREATED)

#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OnboardEmployee(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        user = request.user
        childId = data.get("childId")

        # ================= ORG RESOLUTION =================
        try:
            parent = Organization.objects.get(regUser=user)
            userEmp = None
        except Organization.DoesNotExist:
            try:
                userEmp = Employee.objects.get(user=user)
                parent = userEmp.parent
            except Employee.DoesNotExist:
                return Response(
                    {"error": "Parent organization not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        child = None
        if childId:
            child = ChildAccount.objects.filter(id=childId).first()

        # ================= BASIC DATA =================
        role = data.get("role")
        designation = Designation.objects.filter(id=data.get("designation")).first()
        designation_name = designation.name.upper() if designation else None
        is_c_level = role == "C_LEVEL"


        department = Department.objects.filter(id=data.get("department")).first()

        # ================= PLAN LIMIT =================
        if Employee.objects.filter(parent=parent).count() >= parent.Account.noOfEmployees:
            return Response(
                {"error": "Employee limit exceeded"},
                status=status.HTTP_400_BAD_REQUEST
            )

        password = generate_random_password()
        email = data.get("email")
        if User.objects.filter(email=email).exists():
            return Response(
        {"error": "An account with this email already exists"},
        status=status.HTTP_400_BAD_REQUEST
    )

        try:
            with transaction.atomic():

                # ================= CREATE USER =================
                username = data.get("userName").replace(" ", "_")
                account = User.objects.create_user(
                    username=username,
                    email=data.get("email"),
                    password=password
                )

                # ================= CREATE EMPLOYEE =================
                employee = Employee.objects.create(
                    user=account,
                    parent=parent,
                    employeeid=data.get("empid"),
                    userName=data.get("userName"),
                    email=data.get("email"),
                    phoneNumber=data.get("phoneNumber"),
                    gender=data.get("gender"),
                    type=data.get("type"),
                    dateOfBirth=data.get("dateOfBirth"),
                    dateOfJoining=data.get("dateOfJoining"),
                    designation=designation,
                    department=department,
                )

                employee.child.add(child)
                employee.main_child = child

                # ================= REPORTING LOGIC =================
                if designation_name == "CEO":
                    # CEO → Business Owner
                    bo_emp = Employee.objects.filter(
                        parent=parent,
                        user=parent.regUser
                    ).first()

                    if not bo_emp:
                        return Response(
                            {"error": "Business Owner employee not found"},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    employee.reported_to = bo_emp

                elif designation_name in ["CTO", "CFO", "CHRO", "CMO"]:
                    # Other C-levels → CEO
                    ceo_emp = Employee.objects.filter(
                        parent=parent,
                        designation__name__iexact="CEO"
                    ).first()

                    if not ceo_emp:
                        return Response(
                            {"error": "Create CEO before adding other C-level executives"},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    employee.reported_to = ceo_emp

                else:
                    # Normal employees
                    reported_to_id = data.get("reported_to")
                    if reported_to_id:
                        manager = Employee.objects.filter(id=reported_to_id).first()
                        employee.reported_to = manager

                employee.save()

                # ================= PAY (OPTIONAL FOR C-LEVEL) =================
                if not is_c_level:
                    EmployeePay.objects.create(
                        employee=employee,
                        basic=data.get("basicSalary"),
                        gross=data.get("grossSalary"),
                        ctc=data.get("ctc"),
                        employer_pf=data.get("pfDeduction"),
                        employer_esi=data.get("esiDeduction"),
                    )

                # ================= LEAVE =================
                leavePolicy = LeavePolicy.objects.filter(parent=parent, child=child).first()
                LeaveBalance.objects.create(
                    employee=employee,
                    parent=parent,
                    child=child,
                    current_leave_balance=(leavePolicy.leaves_per_year / 12) if leavePolicy else 0
                )

                # ================= EMAIL =================
                sendemail(
                    "Account Created",
                    f"Dear {employee.userName}, Username: {account.email}, Password: {password}",
                    [account.email]
                )

                return Response(
                    {"message": "Employee onboarded successfully"},
                    status=status.HTTP_201_CREATED
                )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class GetCreateEmployee(APIView):
    def post(self, request):
        id=request.data['id']
        try:
            userDetails = Employee.objects.get(id = id)
            data = {
                'empid' : userDetails.employeeid,
                'parent' : userDetails.parent.orgName,
                'dateOfBirth' : userDetails.dateOfBirth,
                'designation' : userDetails.designation.name if userDetails.designation else None,
                'department':userDetails.department.name if userDetails.department else None,
                'type' : userDetails.type,
                'gender' : userDetails.gender,
                'userName' : userDetails.userName,
                'email' : userDetails.email,
                'rm':userDetails.reported_to.username,
                'jobdescription':userDetails.jobdescription,
                'kras':userDetails.kras,
                'careerpath':userDetails.careerpath,
                'dateOfJoining' : userDetails.dateOfJoining,
                'phoneNumber' : userDetails.phoneNumber,
                'quote':userDetails.parent.quote,
            }
            return Response({'data':data},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
class CreateEmployee(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        childId = request.data.get('childId',None)
        try:
            parent = Organization.objects.get(regUser = user)
        except Organization.DoesNotExist:
            userEmp = Employee.objects.get(user = user)
            parent = userEmp.parent
        try:
            child = ChildAccount.objects.get(id=childId)
        except ChildAccount.DoesNotExist:
            child = None
        designationId = request.data.get("designation",None)
        empid = request.data.get("empid")
        departmentId = request.data.get("department",None)
        reported_to_id = request.data.get("reported_to",None)
        designation = None
        department = None
        reported_to = None
        if reported_to_id:
            reported_to = Employee.objects.get(id = reported_to_id).user
        if designationId:
            designation = Designation.objects.get(id = designationId)
        if departmentId:
            department = Department.objects.get(id = departmentId)
        types = request.data.get("type")
        is_blue = request.data.get('is_blue')
        emp_type = None
        if is_blue == 'true':
            emp_type = 'Blue-Collar'
        else:
            emp_type = 'White-Collar'
        gender = request.data.get("gender")
        userName = request.data.get("userName")
        email = request.data.get("email")
        dateOfBirth = request.data.get("dateOfBirth")
        phoneNumber = request.data.get("phoneNumber")
        role = request.data.get("role")
        dateOfJoining = request.data.get("dateOfJoining")
        labour_cat = request.data.get("labour_cat")
        ctc=request.data.get("ctc")
        needbank = request.data.get("bank")
        jobdescription=request.data.get("jobdescription")
        kras=request.data.get("kras")
        careerpath=request.data.get("careerpath")
        password = generate_random_password()
        users = Employee.objects.filter(parent = parent)
        if(parent.Account.noOfEmployees <= users.count()):
            return Response({"error": f"Your subscribed plan allows you to only create {account.noOfEmployees} employee accounts only."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            employee = Employee.objects.create(employeeid = empid,labour_category=labour_cat, emp_type = emp_type, careerpath=careerpath,jobdescription=jobdescription,kras=kras,parent = parent,designation = designation,department = department, type = types,gender = gender,userName = userName,email = email,dateOfBirth = dateOfBirth,phoneNumber = phoneNumber,dateOfJoining=dateOfJoining, ctc=ctc)
            employee.child.add(child)
            employee.main_child = child
            allowances = request.data.get("allowances", [])
            for allowance in allowances:
                allowance_name = allowance.get("name")
                amount = allowance.get("value")
                allowance_obj = ProductionAllowance.objects.get(id=allowance_name)
                EmployeeProdAllowance.objects.create(
                    allowance=allowance_obj,
                    employee=employee,
                    amount=amount or allowance_obj.min_value
                )
            try:
                if child:
                    leavePolicy = LeavePolicy.objects.get(parent = parent,child=child)
                else:
                    leavePolicy = LeavePolicy.objects.get(parent = parent)
                if leavePolicy:
                    LeaveBalance.objects.create(employee = employee,parent=parent,child=child,current_leave_balance = leavePolicy.leaves_per_year/12)
                else:
                    LeaveBalance.objects.create(employee = employee,parent=parent,child=child,current_leave_balance = 0)
            except:
                pass
            employee.save()
            if(employee):
                EmployeeOccasions.objects.create(parent=parent,child=child,employee=employee,type="birthday",date = dateOfBirth)
                if needbank == 'yes':
                    try:
                        rm = Roles.objects.get(name='RELATIONSHIP_MANAGER',parent=parent,child=child).user
                        bank_message = f"A new bank account is to be created for the user {employee.userName}."
                        Notification.objects.create(sender = user,receiver = rm,message=bank_message)
                        try:
                            sendemail(
                                    'New Bank Account Creation - Action Required',
                                    bank_message,
                                    [rm.email],
                                )
                        except:
                            sendemail('New Bank Account Creation - Action Required',bank_message,[rm.email])
                            pass
                    except:
                        pass
                if reported_to:
                    employee.reported_to = reported_to
                    employee.save()
                else:
                    employee.reported_to = request.user
                    employee.save()
                try:
                    new_user_name = employee.userName.replace(" ", "_")
                    account = User.objects.create_user(
                        username = new_user_name,email=email, password=password
                    )
                    employee.user = account
                    employee.save()
                    if(role == 'BUSINESS_OWNER'):
                        try:
                            givenrole = Roles.objects.get(name = role,parent = parent,child = child)
                            if givenrole.user and givenrole.user != account:
                                u = givenrole.user
                                roles = u.get_roles()
                                roles.remove(role)
                                u.set_roles(roles)
                                u.save()
                            givenrole.user = account
                            existing_roles = account.get_roles()
                            if(givenrole.name in existing_roles):
                                error = f"{role.name} already assigned for given user"
                                return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)
                            existing_roles.append(givenrole.name)
                            account.set_roles(existing_roles)
                            account.save()
                            givenrole.save()
                            employee.reported_to = user
                            employee.save()
                        except:
                            givenrole = Roles.objects.create(name = role,parent = parent,child = child,user = account)
                            account.roles = givenrole.name
                        child.bussinessOwner = account
                        child.save()
                        account.save()
                        employee.save()
                    else:
                        bo = userEmp.reported_to
                        if role != 'EMPLOYEE':
                            givenrole = RoleRequests.objects.create(sender = user,receiver = bo,role = role,parent = parent,child = child,user = account)    
                            message = f"Dear {bo.username},\nWe hope this message finds you well.\nWe would like to inform you that {userEmp.userName} has requested approval to add {userName} as {role} in our organization. Your prompt attention to this matter is greatly appreciated.\nPlease visit the approvals tab for more details and to complete the approval process.\nThank you for your cooperation.\nBest regards,\nGA Org Sync"
                            Notification.objects.create(sender = user,receiver = bo,message=message)
                            try:
                                sendemail(
                                    'Approval Needed for Adding Roles',
                                    message,
                                    [bo.email],
                                )
                            except:
                                sendemail('Approval Needed for Adding Roles',message,[bo.email])
                                pass
                            child.save()
                            employee.save()
                    employee.save()
                    message=f'Dear {userName},\nWe are delighted to inform you that your account has been successfully created. Below are your account credentials:\nUsername: {account.email}\nPassword: {password}\n.Kindly Please Login into the website https://www.gaorgsync.com and update your profile. \n Please ensure to keep this information secure and refrain from sharing it with anyone.\nIf you have any queries or require further assistance, do not hesitate to reach out to our support team.\nWelcome aboard!\nBest regards,\nGA Org Sync\n',
                    try:
                        sendemail(
                            'Account Created Successfully - Here Are Your Credentials',
                            f'Dear {userName},\nWe are delighted to inform you that your account has been successfully created. Below are your account credentials:\nUsername: {account.email}\nPassword: {password}\n.Kindly Please Login into the website https://www.gaorgsync.com and update your profile. \n Please ensure to keep this information secure and refrain from sharing it with anyone.\nIf you have any queries or require further assistance, do not hesitate to reach out to our support team.\nWelcome aboard!\nBest regards,\nGA Org Sync\n',
                            [account.email],
                        )
                    except:
                        sendemail('Account Created Successfully - Here Are Your Credentials',message,[account.email])
                        pass
                except Exception as e:
                    employee.delete()
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"message": "Registration successful"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    def get(self, request):
        user  = request.user
        try:
            userDetails = Employee.objects.get(user = user)
            data = {
                'empid' : userDetails.employeeid,
                'parent' : userDetails.parent.orgName,
                'dateOfBirth' : userDetails.dateOfBirth,
                'designation' : userDetails.designation.name if userDetails.designation else None,
                'department':userDetails.department.name if userDetails.department else None,
                'type' : userDetails.type,
                'gender' : userDetails.gender,
                'userName' : userDetails.userName,
                'email' : userDetails.email,
                'rm': userDetails.reporting_manager.userName if userDetails.reporting_manager else None,

                # 'rm':userDetails.reported_to.username,
                'jobdescription':userDetails.jobdescription,
                'kras':userDetails.kras,
                'careerpath':userDetails.careerpath,
                'dateOfJoining' : userDetails.dateOfJoining,
                'phoneNumber' : userDetails.phoneNumber,
                'quote':userDetails.parent.quote,
            }
            return Response({'data':data},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    def put(self, request):
        id = request.data.get('id')
        type = request.data.get("type")
        gender = request.data.get("gender")
        dateOfBirth = request.data.get("dateOfBirth")
        phoneNumber = request.data.get("phoneNumber")
        role = request.data.get("role",None)
        dateOfJoining = request.data.get("dateOfJoining")
        stat = request.data.get("status")
        department_id = request.data.get("department")
        department = Department.objects.get(id=department_id)
        designation_id = request.data.get("designation")
        designation = Designation.objects.get(id=designation_id)
        empobj = Employee.objects.get(id=id)
        main_child = request.data.get('main_child')
        if empobj:
            empobj.type = type
            empobj.gender = gender
            empobj.dateOfBirth = dateOfBirth
            empobj.phoneNumber = phoneNumber
            empobj.role = role
            empobj.dateOfJoining = dateOfJoining
            empobj.status = stat
            empobj.department = department
            empobj.designation = designation
            empobj.main_child = main_child
            empobj.save()
            return Response({"message": "Updated Successful"}, status=status.HTTP_201_CREATED)


class EmployeeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            child_id = request.GET.get('child_id')
            emps = Employee.objects.filter(main_child__id = child_id,status='onroll')
            employees = emps.exclude(user=request.user)

            employee_data = []
            for employee in employees:
                employee_data.append({
                    'id': employee.id,
                    'userName': employee.userName,
                    'email': employee.email
                })

            return Response(employee_data, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)



class EmployeeBankDetailsAPIView(APIView):
    def get(self, request):
        user = request.user
        if user:
            employee = Employee.objects.get(user=user)
            employeebank = EmployeeBankDetails.objects.get(employee=employee)
            serializer = EmployeeBankDetailsSerializer(employeebank)
            return Response({'data': serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Login to continue"}, status=status.HTTP_404_NOT_FOUND)
    def put(self, request):
        user = request.user
        if user:
            employee = Employee.objects.get(user=user)
            employeebank = EmployeeBankDetails.objects.get(employee=employee)
            employeebank.bankName = request.data.get('bankName')
            employeebank.ifsc = request.data.get('ifsc')
            employeebank.bankAcNo = request.data.get('bankAcNo')
            employeebank.save()
            return Response({'message': "Details updated Successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Login to continue"}, status=status.HTTP_404_NOT_FOUND)




class fetchEmployees(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        user = request.user
        childid=request.data.get('childid')
        if childid:
            child = ChildAccount.objects.get(id = childid)
        else:
            child = None
        if('SUPER_USER' in user.get_roles()):
            organization = Organization.objects.get(regUser=user)
        else:
            emp = Employee.objects.get(user = user)
            organization = emp.parent
        if childid:
            employees = Employee.objects.filter(parent = organization,child=child).order_by('-dateOfJoining')
        else:
            employees = Employee.objects.filter(parent = organization).order_by('-dateOfJoining')
        serializer = EmployeeSerializer(employees, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

class fetchEmployee(APIView):
    def post(self,request):
        id = request.data.get('id')
        try:
            emp = Employee.objects.get(id=id)
            data = {
                    'userName':emp.userName,
                    'dateOfBirth':emp.dateOfBirth,
                    'designation' : emp.designation.name if emp.designation else None,
                    'department':emp.department.name if emp.department else None,
                    'type':emp.type,
                    'gender':emp.gender,
                    'email':emp.email,
                    'phoneNumber':emp.phoneNumber,
            }
            return Response({'data':data},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class GetRelationshipView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        id= request.data['id']
        empobj = Employee.objects.get(id= id)
        relobjs = EmployeeRelation.objects.filter(employee = empobj)
        serializer = EmpRelationSetializer(relobjs,many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK) 

class RelationshipView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        user = request.user
        empobj = Employee.objects.get(user = user)
        relobjs = EmployeeRelation.objects.filter(employee = empobj)
        serializer = EmpRelationSetializer(relobjs, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK) 
    def post(self, request, *args):
        try:
            user = request.user
            employee = Employee.objects.get(user=user)
            relationName = request.data.get('relationName')
            relationType = request.data.get('relationType')
            relationAge = request.data.get('relationAge')
            relationContact = request.data.get('relationContact')
            relationAadhar = request.data.get('relationAadhar')
            try:
                EmployeeRelation.objects.create(
                    employee=employee,
                    relationName=relationName,
                    relationType=relationType,
                    relationAge=relationAge,
                    relationContact=relationContact,
                    relationAadhar=relationAadhar
                )
                return Response({'message': "Relation Added Successfully."}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Employee.DoesNotExist:
            return Response({'error': "Employee does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def put(self, request, *args):
        try:
            id = request.data.get('id')
            relationName = request.data.get('relationName')
            relationType = request.data.get('relationType')
            relationAge = request.data.get('relationAge')
            relationContact = request.data.get('relationContact')
            relationAadhar = request.data.get('relationAadhar')
            try:
                relobj = EmployeeRelation.objects.get(id=id)
                relobj.relationName = relationName
                relobj.relationType = relationType
                relobj.relationAge = relationAge
                relobj.relationContact = relationContact
                relobj.relationAadhar = relationAadhar
                relobj.save()
                return Response({'message': "Relation Updated Successfully."}, status=status.HTTP_200_OK)
            except EmployeeRelation.DoesNotExist:
                return Response({'error': "Employee Relation does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetOccasionView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        id = request.data['id']
        empobj = Employee.objects.get(id= id)
        relobjs = EmployeeOccasions.objects.filter(employee = empobj)
        serializer = EmpOccSetializer(relobjs, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

class OccasionView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        user = request.user
        empobj = Employee.objects.get(user = user)
        relobjs = EmployeeOccasions.objects.filter(employee = empobj)
        serializer = EmpOccSetializer(relobjs, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK) 
    def post(self, request, *args):
        try:
            user = request.user
            employee = Employee.objects.get(user=user)
            type = request.data.get('type')
            date = request.data.get('date')
            try:
                EmployeeOccasions.objects.create(
                    employee=employee,
                    parent = employee.parent,
                    child = employee.main_child,
                    type = type,
                    date = date
                )
                return Response({'message': "Occassion Added Successfully."}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Employee.DoesNotExist:
            return Response({'error': "Employee does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def put(self, request, *args):
        try:
            id = request.data.get('id')
            date = request.data.get('date')
            try:
                relobj = EmployeeOccasions.objects.get(id=id)
                relobj.date = date
                relobj.save()
                return Response({'message': "Occasion Date Updated Successfully."}, status=status.HTTP_200_OK)
            except EmployeeRelation.DoesNotExist:
                return Response({'error': "Occassion does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetEducationView(APIView):
    
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        id = request.data['id']
        empobj = Employee.objects.get(id = id)
        eduobjs = EmployeeEducationDetails.objects.filter(employee = empobj)
        serializer = EmployeeEducationDetailsSerializer(eduobjs, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK) 

class EducationView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        user = request.user
        empobj = Employee.objects.get(user = user)
        eduobjs = EmployeeEducationDetails.objects.filter(employee = empobj)
        serializer = EmployeeEducationDetailsSerializer(eduobjs, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK) 
    def post(self, request, *args):
        try:
            user = request.user
            employee = Employee.objects.get(user=user)
            institution = request.data.get('institution')
            degree = request.data.get('degree')
            field_of_study = request.data.get('field_of_study')
            start_date = request.data.get('start_date')
            end_date = request.data.get('end_date')
            try:
                EmployeeEducationDetails.objects.create(
                    employee=employee,
                    institution=institution,
                    degree=degree,
                    field_of_study=field_of_study,
                    start_date=start_date,
                    end_date=end_date
                )
                return Response({'message': "Education Added Successfully."}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Employee.DoesNotExist:
            return Response({'error': "Employee does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def put(self, request, *args):
        try:
            id = request.data.get('id')
            institution = request.data.get('institution')
            degree = request.data.get('degree')
            field_of_study = request.data.get('field_of_study')
            start_date = request.data.get('start_date')
            end_date = request.data.get('end_date')
            try:
                obj = EmployeeEducationDetails.objects.get(id=id)
                obj.institution = institution
                obj.degree = degree
                obj.field_of_study = field_of_study
                obj.start_date = start_date
                obj.end_date = end_date
                obj.save()
                return Response({'message': "Education Updated Successfully."}, status=status.HTTP_200_OK)
            except EmployeeEducationDetails.DoesNotExist:
                return Response({'error': "Education object does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetExperienceView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        try:
            id= request.data['id']
            employee = Employee.objects.get(id=id)
            experiences = EmployeeExperience.objects.filter(employee=employee)
            serializer = EmployeeExperienceSerializer(experiences, many=True)
            return Response({'data': serializer.data}, status=status.HTTP_200_OK)
        except Employee.DoesNotExist:
            return Response({'error': "Employee does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ExperienceView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            employee = Employee.objects.get(user=user)
            experiences = EmployeeExperience.objects.filter(employee=employee)
            serializer = EmployeeExperienceSerializer(experiences, many=True)
            return Response({'data': serializer.data}, status=status.HTTP_200_OK)
        except Employee.DoesNotExist:
            return Response({'error': "Employee does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def post(self, request, *args):
        try:
            user = request.user
            employee = Employee.objects.get(user=user)
            worked_from = request.data.get('worked_from')
            worked_to = request.data.get('worked_to')
            designation = request.data.get('designation')
            department = request.data.get('department')
            organization = request.data.get('organization')
            reason_for_resign = request.data.get('reason_for_resign')
            try:
                EmployeeExperience.objects.create(
                    employee=employee,
                    worked_from=worked_from,
                    organization = organization,
                    worked_to=worked_to,
                    designation=designation,
                    department=department,
                    reason_for_resign=reason_for_resign,
                )
                return Response({'message': "Experience added successfully."}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Employee.DoesNotExist:
            return Response({'error': "Employee does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def put(self, request, *args):
        try:
            id = request.data.get('id')
            worked_from = request.data.get('worked_from')
            worked_to = request.data.get('worked_to')
            designation = request.data.get('designation')
            organization = request.data.get('organization')
            department = request.data.get('department')
            reason_for_resign = request.data.get('reason_for_resign')
            try:
                obj = EmployeeExperience.objects.get(id=id)
                obj.worked_from = worked_from
                obj.worked_to = worked_to
                obj.designation = designation
                obj.department = department
                obj.organization = organization
                obj.reason_for_resign = reason_for_resign
                obj.save()
                return Response({'message': "Experience updated successfully."}, status=status.HTTP_200_OK)
            except EmployeeExperience.DoesNotExist:
                return Response({'error': "Experience object does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmpDataForRM(APIView):
    def post(self, request):
        user=request.user
        employee=Employee.objects.get(user=user)
        childid=request.data['childid']
        month=request.data['month']
        year=request.data['year']
        parent=employee.parent
        child=ChildAccount.objects.get(id=childid)
        employees=Employee.objects.filter(parent=parent,child=child,reported_to=user,status="onroll")
        data=EmployeeSerializer(employees,many=True).data
        for i in range(len(data)):
            try:
                data[i]['leaves']=len(Attendance.objects.filter(parent=parent,child=child,date__month=month,date__year=year,employee=employees[i],status="leave"))
                data[i]['absent']=len(Attendance.objects.filter(parent=parent,child=child,date__month=month,date__year=year,employee=employees[i],status="absent"))
                data[i]['present']=len(Attendance.objects.filter(parent=parent,child=child,date__month=month,date__year=year,employee=employees[i],status="present"))
                data[i]['halfday']=len(Attendance.objects.filter(parent=parent,child=child,date__month=month,date__year=year,employee=employees[i],status="halfday"))
                data[i]['latelogin']=len(Attendance.objects.filter(parent=parent,child=child,date__month=month,date__year=year,employee=employees[i],status="latelogin"))

            except:
                data[i]['leaves']=None
            try:
                data[i]['carryleavebal']=LeaveBalance.objects.get(parent=parent,year=year,month=month,child=child,employee=employees[i]).carry_forwarded_leave_balance
                data[i]['currentleavebal']=LeaveBalance.objects.get(parent=parent,year=year,month=month,child=child,employee=employees[i]).current_leave_balance


            except:
                data[i]['carryleavebal']=None
                data[i]['currentleavebal']=None


        return Response(data, status=status.HTTP_200_OK)


class EmpDataForHR(APIView):
    def post(self, request):
        user=request.user
        employee=Employee.objects.get(user=user)
        childid=request.data['childid']
        child=ChildAccount.objects.get(id=childid)
        parent=employee.parent
        month=request.data['month']
        year=request.data['year']
        employees=Employee.objects.filter(parent=parent,child=child,status="onroll")
        data=EmployeeSerializer(employees,many=True).data
        for i in range(len(data)):
            try:
                data[i]['leaves']=len(Attendance.objects.filter(parent=parent,child=child,date__month=month,date__year=year,employee=employees[i],status="leave"))
                data[i]['absent']=len(Attendance.objects.filter(parent=parent,child=child,date__month=month,date__year=year,employee=employees[i],status="absent"))
                data[i]['halfday']=len(Attendance.objects.filter(parent=parent,child=child,date__month=month,date__year=year,employee=employees[i],status="halfday"))
                data[i]['present']=len(Attendance.objects.filter(parent=parent,child=child,date__month=month,date__year=year,employee=employees[i],status="present"))
                data[i]['latelogin']=len(Attendance.objects.filter(parent=parent,child=child,date__month=month,date__year=year,employee=employees[i],status="latelogin"))
            except:
                data[i]['leaves']=None
            try:
                data[i]['carryleavebal']=LeaveBalance.objects.get(parent=parent,child=child,employee=employees[i],month=month,year=year).carry_forwarded_leave_balance
                data[i]['currentleavebal']=LeaveBalance.objects.get(parent=parent,child=child,employee=employees[i],month=month,year=year).current_leave_balance


            except:
                data[i]['carryleavebal']=None
                data[i]['currentleavebal']=None
            try:
                data[i]['salary']=EmployeePayroll.objects.filter(month=month,year=year,employee=employees[i]).exclude(status="Preview").first().net_salary
            except:
                data[i]['salary']=None

        return Response(data, status=status.HTTP_200_OK)


class bulkUpload(APIView):
    permission_classes = [IsAuthenticated]
    @transaction.atomic
    def post(self,request,**kwargs):
        user = request.user
        empobj = Employee.objects.get(user = user)
        parent = empobj.parent
        childid=request.data['childid']
        child = ChildAccount.objects.get(id = childid)
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file provided in the request"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with file.open() as file:
                name_sheet_file = file.read().decode('utf-8')
                csv_reader = csv.reader(name_sheet_file.splitlines())
                next(csv_reader)
                for row in csv_reader:
                    empid,userName,email,phoneNumber,dateOfBirth,designation,department,ty,gender,reported_to,dateOfJoining,ctc = row
                    gender = gender.lower()
                    date_object = datetime.strptime(dateOfBirth, '%d/%m/%Y')
                    dateOfBirth = date_object.strftime('%Y-%m-%d')
                    date_joining_object = datetime.strptime(dateOfJoining, '%d/%m/%Y')
                    dateOfJoining = date_joining_object.strftime('%Y-%m-%d')
                    if designation and designation != '':
                        designation,_ = Designation.objects.get_or_create(name = designation,parent = parent,child = child)
                    else:
                        designation = None
                    if department and department != '':
                        department,_ = Department.objects.get_or_create(name = department,parent = parent,child = child)
                    else:
                        department = None
                    if reported_to and reported_to != '':
                        try:
                            reported_to = User.objects.get(email = reported_to)
                        except:
                            reported_to = None
                    else:
                        reported_to = None
                    emp = Employee.objects.create(
                        employeeid = empid,
                        parent = parent,
                        dateOfBirth = dateOfBirth,
                        designation = designation,
                        department = department,
                        type = ty,
                        gender = gender,
                        userName = userName,
                        email = email,
                        phoneNumber = phoneNumber,
                        reported_to = reported_to,
                        dateOfJoining = dateOfJoining,
                        ctc = ctc
                    )
                    emp.child.add(child)
                    emp.main_child = child
                    emp.save()
                    if(emp):
                        try:
                            password = generate_random_password()
                            new_user_name = emp.userName.replace(" ", "_")
                            while User.objects.filter(username=new_user_name).exists():
                                new_user_name = new_user_name + random.randint(0,9999)
                            account = User.objects.create_user(
                                username = new_user_name,email=email, password=password
                            )
                            emp.user = account
                            emp.save()
                            try:
                                if child:
                                        leavePolicy = LeavePolicy.objects.get(parent = parent,child=child)
                                else:
                                    leavePolicy = LeavePolicy.objects.get(parent = parent)
                                if leavePolicy:
                                    LeaveBalance.objects.create(employee = emp,leave_balance = leavePolicy.leaves_per_year/12)
                                else:
                                    LeaveBalance.objects.create(employee = emp,leave_balance = 0)
                                EmployeeOccasions.objects.create(parent=parent,child=child,employee=emp,type="birthday",date = dateOfBirth)

                            except:
                                pass
                            try:
                                sendemail(
                                    'Account Created Successfully - Here Are Your Credentials',
                                    f'Dear {emp.userName},\nWe are delighted to inform you that your account has been successfully created. Below are your account credentials:\nUsername: {account.email}\nPassword: {password}\nPlease ensure to keep this information secure and refrain from sharing it with anyone.\nIf you have any queries or require further assistance, do not hesitate to reach out to our support team.\nWelcome aboard!\nBest regards,\nGA Org Sync',
                                   [account.email],
                                )
                            except:
                                pass
                        except Exception as e:
                            emp.delete()
                            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
                return Response({"message": "Registration successful"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class preJoinEmployee(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        childId = request.data.get('childId', None)

        try:
            parent = Organization.objects.get(regUser=user)
        except Organization.DoesNotExist:
            try:
                userEmp = Employee.objects.get(user=user)
                parent = userEmp.parent
            except Employee.DoesNotExist:
                return Response({"error": "Parent organization or employee not found."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            child = ChildAccount.objects.get(id=childId)
        except ChildAccount.DoesNotExist:
            child = None

        designationId = request.data.get("designation", None)
        departmentId = request.data.get("department", None)

        designation = Designation.objects.get(id=designationId) if designationId else None
        department = Department.objects.get(id=departmentId) if departmentId else None

        types = request.data.get("type")
        gender = request.data.get("gender")
        userName = request.data.get("userName")
        email = request.data.get("email")
        dateOfBirth = request.data.get("dateOfBirth")
        phoneNumber = request.data.get("phoneNumber")
        dateOfJoining = request.data.get("dateOfJoining")
        jobdescription = request.data.get("jobdescription")
        kras = request.data.get("kras")
        careerpath = request.data.get("careerpath")

        users = Employee.objects.filter(parent=parent)
        if parent.Account.noOfEmployees <= users.count():
            return Response({"error": f"Your subscribed plan allows you to only create {parent.Account.noOfEmployees} employee accounts."}, status=status.HTTP_400_BAD_REQUEST)

        password = generate_random_password()

        try:
            with transaction.atomic():
                employee = Employee.objects.create(
                    careerpath=careerpath,
                    jobdescription=jobdescription,
                    kras=kras,
                    parent=parent,
                    designation=designation,
                    department=department,
                    type=types,
                    gender=gender,
                    userName=userName,
                    email=email,
                    dateOfBirth=dateOfBirth,
                    phoneNumber=phoneNumber,
                    dateOfJoining=dateOfJoining,
                    status = 'prejoining',
                )

                employee.child.add(child)
                employee.main_child = child

                new_user_name = employee.userName.replace(" ", "_")
                account = User.objects.create_user(username=new_user_name, email=email, password=password)
                employee.user = account
                employee.save()

                welcome_message = f"Dear {userName}, your account has been created. Username: {account.email}, Password: {password}. Please login at https://www.gaorgsync.com."
                sendemail('Account Created', welcome_message, [account.email])

            return Response({"message": "Employee onboarded successfully"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)