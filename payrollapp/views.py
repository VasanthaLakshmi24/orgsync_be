import random
from django.apps import apps
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.shortcuts import get_object_or_404
from datetime import datetime,timedelta
from num2words import num2words
from rest_framework.decorators import api_view
from django.http import JsonResponse,HttpResponse
from django.contrib.auth import authenticate
from rest_framework import status
from .models import *
from .decorators import *
from .serializers import *
from .tasks import *
from rest_framework.views import APIView
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import razorpay
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
from .utils import *
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .serializers import EmployeeCertificationsSerializer,EmployeeSkillsSerializer
from rest_framework.response import Response
from .models import Employee, EmployeeExperience
from .serializers import EmployeeExperienceSerializer
from django.http import FileResponse, Http404
from .models import DocumentVerification, DocumentAccessRule, Employee, Document, EmployeeBasicDetails,Roles
from .serializers import DocumentVerificationSerializer, DocumentAccessRuleSerializer
# from .tasks import send_document_verification_email
from django.db.models import Q
from payrollapp.models import (
    RoleRequests,
    Employee,
    Roles,
    ChildAccount as Child  # 👈 REQUIRED IMPORT
)
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from payrollapp.tasks import send_rejection_summary_email
from payrollapp.utils import can_verify_document
from rest_framework.pagination import PageNumberPagination


def get_user_employee(user):
    """
    Safely return Employee or None
    """
    try:
        return Employee.objects.get(user=user)
    except Employee.DoesNotExist:
        return None


ist = pytz.timezone('Asia/Kolkata')

load_dotenv()
apiurl=os.environ.get('apiurl')
backendurl=os.environ.get('backendurl')

class CreateOrganization(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        orgName = request.data.get('orgName')
        regUser = user.id
        type = request.data.get('type')
        regNo = request.data.get('regNo')
        companyRegistrationDate = request.data.get('companyRegistrationDate')
        contactPerson = request.data.get('contactPerson')
        contactNo = request.data.get('contactNo')
        email = request.data.get('email')
        address = request.data.get('address')
        designation = request.data.get('designation')
        companyGstRegNo = request.data.get('companyGstRegNo')
        companyPanNo = request.data.get('companyPanNo')
        companyTanNo = request.data.get('CompanyTanNo')
        try:
            account = Accounts.objects.get(email=user.email)
            if(account.addedOrganization==True):
                return Response({"error": "Account Already Exists"}, status=status.HTTP_400_BAD_REQUEST)
            new_org = Organization.objects.create(
                orgName=orgName,
                regUser=user,
                type=type,
                regNo=regNo,
                companyRegistrationDate=companyRegistrationDate,
                contactPerson=contactPerson,
                contactNo=contactNo,
                email=email,
		        address = address,
                designation=designation,
                companyGstRegNo=companyGstRegNo,
                companyPanNo=companyPanNo,
                companyTanNo=companyTanNo,
                Account = account
            )
            if new_org:
                account.addedOrganization = True
                account.save()
            return Response({'message': 'Organization created successfully'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CreateChild(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        parent = Organization.objects.get(regUser = user)
        name = request.data.get('name')
        regNo = request.data.get('regNo')
        contactPerson = request.data.get('contactPerson')
        designation = request.data.get('designation')
        contactNo = request.data.get('contactNo')
        email = request.data.get('email')
        companyGstRegNo = request.data.get('companyGstRegNo')
        companyPanNo = request.data.get('companyPanNo')
        companyTanNo = request.data.get('companyTanNo')
        PFType = request.data.get('PFType')
        attendanceType = request.data.get('attendanceType')
        try:
            account = Accounts.objects.get(email=user.email)
            childs = ChildAccount.objects.filter(parent = parent)
            if(account.noOfChilds <= childs.count()):
                return Response({"error": f"Your subscribed plan allows you to only create {account.noOfChilds} child accounts only."}, status=status.HTTP_400_BAD_REQUEST)
            new_child = ChildAccount(
                name=name,
                parent = parent,
                regNo=regNo,
                contactPerson=contactPerson,
                contactNo=contactNo,
                email=email,
                designation=designation,
                companyGstRegNo=companyGstRegNo,
                companyPanNo=companyPanNo,
                companyTanNo=companyTanNo,
                PFType = PFType,
                attendanceType = attendanceType,
            )
            new_child.save()
            return Response({'message': 'Organization created successfully'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class fetchChilds(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        user = request.user
        organization = Organization.objects.get(regUser=user)
        childs = ChildAccount.objects.filter(parent = organization).values()
        return Response({'data':list(childs)},status=status.HTTP_200_OK)
    def post(self,request):
        id = request.data.get('id')
        try:
            child = ChildAccount.objects.get(id=id)
            if(not child.bussinessOwner):
                bo = None
            else:
                user = child.bussinessOwner
                b= Employee.objects.get(user = user)
                bs = EmployeeSerializer(b)
                bo = bs.data
            data = {
                    'name':child.name,
                    'regNo':child.regNo,
                    'contactPerson':child.contactPerson,
                    'designation':child.designation,
                    'contactNo':child.contactNo,
                    'email':child.email,
                    'companyGstRegNo':child.companyGstRegNo,
                    'companyPanNo':child.companyPanNo,
                    'companyTanNo':child.companyTanNo,
                    'bussinessOwner':bo,
            }
            return Response({'data':data},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class Appraisal(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        user=request.user
        childid=request.data.get('childid')
        if childid:
            child = ChildAccount.objects.get(id = childid)
        else:
            child = None
            
        if child.HrHead==user:
            employeeid=request.data['employeeid']
            description=request.data['description']
            currentctc=request.data['currentctc']
            employee=Employee.objects.get(id=employeeid)
            employee.ctc=currentctc
            employee.save()
            message=f"Congratulations {employee.userName} Your Appraisal is done !"
            Notification.objects.create(sender=user,receiver=employee.user,message=description)
            try:
                sendemail('Appraisal',message,[employee.email])
            except:
                pass
            return Response({'success':'Appraisal Done Successfully'},status=status.HTTP_200_OK)
        return Response({'error':'You are not eligible to change the appraisal status'},status=status.HTTP_400_BAD_REQUEST)

class FetchChildAccounts(APIView):
    def get(self,request):
        user=request.user
        if user.roles=="SUPER_USER":
            return Response({'data':"SUPER_USER"})
        employee=Employee.objects.get(user=user)
        childs=employee.child.all()
        Data=[]
        for child in childs:
            roles=Roles.objects.filter(child=child,user=user)
            serializeddata=RolesSerializer(roles,many=True).data
            Data.append({
                "child":child.name,
                "id":child.id,
                "roles":serializeddata,
                "attendance_type":employee.main_child.attendanceType
            })
        return Response({'data':Data})

class fetchChild(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        childid=request.data.get('childid')
        child=ChildAccount.objects.get(id=childid)
        try:
            userDetails = Employee.objects.get(email=user.email)
            parent = userDetails.parent
            if not child:
                child = None
            if child and not child.bussinessOwner:
                bo = None
            else:
                user = child.bussinessOwner
                b= Employee.objects.get(email = user.email)
                bo = {
                    'userName':b.userName,
                    'dateOfBirth':b.dateOfBirth,
                    'designation' : b.designation.name if b.designation else None,
                    'department':b.department.name if b.department else None,
                    'type':b.type,
                    'gender':b.gender,
                    'email':b.email,
                    'phoneNumber':b.phoneNumber,
                }
            if child and not child.HrHead:
                hr = None
                hrStatus = None
            else:
                user = child.HrHead
                h= Employee.objects.get(email = user.email)
                hr = {
                    'userName':h.userName,
                    'dateOfBirth':h.dateOfBirth,
                    'designation' : h.designation.name if h.designation else None,
                    'department':h.department.name if h.department else None,
                    'type':h.type,
                    'gender':h.gender,
                    'email':h.email,
                    'phoneNumber':h.phoneNumber,
                }
                role = Roles.objects.get(child=child, parent=parent, name="HR_HEAD",user = user)
                hrStatus = "approved"
            data = {
                'id': child.id,
                'name': child.name,
                'regNo': child.regNo,
                'contactPerson': child.contactPerson,
                'designation': child.designation,
                'contactNo': child.contactNo,
                'email': child.email,
                'companyGstRegNo': child.companyGstRegNo,
                'companyPanNo': child.companyPanNo,
                'companyTanNo': child.companyTanNo,
                'bussinessOwner': bo,
                'hr': hr,
                'hrStatus' :hrStatus,
            }
            return Response({'data': data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class fetchRole(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        user = request.user
        employee = Employee.objects.get(email = user.email)
        childid=request.data['childid']
        child=ChildAccount.objects.get(id=childid)
        try:
            roles = Roles.objects.filter(parent = employee.parent,child = child).values()
        except:
            roles = Roles.objects.filter(parent = employee.parent).values()
        return Response({'data':list(roles)},status=status.HTTP_200_OK)
class updateRole(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        role_request_id = request.data.get("id")
        stat = request.data.get("status")
        child_id = request.data.get("childid")

        try:
            role_req = RoleRequests.objects.get(id=role_request_id)
            employee = Employee.objects.get(user=role_req.user)

            # 🔒 SAFETY CHECKS
            if not role_req.parent:
                return Response(
                    {"error": "Parent organization missing in role request"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not child_id:
                return Response(
                    {"error": "Child ID not provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            child = Child.objects.filter(id=child_id).first()
            if not child:
                return Response(
        {"error": "Invalid child ID"},
        status=status.HTTP_400_BAD_REQUEST
    )

            role_req.status = stat
            role_req.save()

            if stat == "approved":
                role_user = role_req.user

                role_obj, created = Roles.objects.get_or_create(
                    parent=role_req.parent,
                    child=child,
                    name=role_req.role
                )

                # remove role from old user if exists
                if role_obj.user and role_obj.user != role_user:
                    old_emp = Employee.objects.get(user=role_obj.user)
                    old_emp.roles.remove(role_obj)

                    if role_obj.child != old_emp.main_child:
                        old_emp.child.remove(role_obj.child)

                    old_emp.save()

                # assign role to new user
                role_obj.user = role_user
                role_obj.save()

                employee.roles.add(role_obj)
                employee.child.add(child)
                employee.save()

                # HR_HEAD special case
                if role_obj.name == "HR_HEAD":
                    child.HrHead = role_user
                    child.save()

            return Response(
                {"message": "Status Updated Successfully"},
                status=status.HTTP_200_OK
            )

        except RoleRequests.DoesNotExist:
            return Response(
                {"error": "Role request not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Child.DoesNotExist:
            return Response(
                {"error": "Invalid child ID"},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Employee.DoesNotExist:
            return Response(
                {"error": "Employee matching query does not exist."},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
class addRole(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        user = request.user
        role = request.data.get('role')
        role_user_id = request.data.get('user')
        role_user_email = Employee.objects.get(id = role_user_id).email
        role_user_name = Employee.objects.get(id = role_user_id).userName
        role_user = User.objects.get(email = role_user_email)
        child_id = request.data.get('child_id')
        child = ChildAccount.objects.get(id = child_id)
        if "SUPER_USER" in user.get_roles():
            org = Organization.objects.get(regUser = user)
            if role == "BUSINESS_OWNER":
                try:
                    role_obj = Roles.objects.get(name = role,child = child,parent = org)
                except:
                    role_obj = Roles.objects.create(name = role,child = child,parent = org)
                child.bussinessOwner = role_user
                employee=Employee.objects.get(user=role_user)
                employee.child.add(child)
                employee.save()
                role_obj.user=role_user
                role_user.save()
            else:
                try:
                    role_obj = Roles.objects.get(name = role,child = child,parent = org)
                except:
                    role_obj = Roles.objects.create(name = role,child = child,parent = org)
                exis_roles = get_roles_list(role_user)
                if role not in exis_roles:
                    exis_roles.append(role)
                    role_user.set_roles(",".join(exis_roles))
                    role_user.save()

        else:
            emp = Employee.objects.get(user = user)
            org = emp.parent
            role_obj = RoleRequests.objects.create(role = role,child = child,parent = org,sender = user,receiver = emp.reported_to,user = role_user)
            role_obj.status = "underreview"
            role_obj.save()
            
            context = {
                'reported_to': emp.reported_to.username,
                'sender': emp.userName,
                'role_user_name' : role_user_name,
                'role':role
            }
            
            message = f"Dear {emp.reported_to.username},\nWe hope this message finds you well.\nWe would like to inform you that {emp.userName} has requested approval to add {role_user_name} as {role} in our organization. Your prompt attention to this matter is greatly appreciated.\nPlease visit the approvals tab for more details and to complete the approval process.\nThank you for your cooperation.\nBest regards,\nGA Org Sync"
            Notification.objects.create(sender = user,receiver = emp.reported_to,message=message)
            sendemailTemplate(
                'New Request - Action Required',
                'emails/AddRoleRequest.html',
                context,
                [emp.reported_to.email]
            )
        role_obj.save()
        child.save()
        return Response({'message':'Role Added Successfully'},status=status.HTTP_200_OK)

class fetchreviewroles(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        my_req = RoleRequests.objects.filter(sender = user)
        req = RoleRequests.objects.filter(receiver = user)
        my_serializer = RoleRequestsSerializer(my_req, many=True)
        req_serializer = RoleRequestsSerializer(req, many=True)
        return Response({'my_req':my_serializer.data , 'req':req_serializer.data}, status=status.HTTP_200_OK)

class Departments(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        given_departments = request.data['departments']
        user = request.user
        childid=request.data['childid']
        child=ChildAccount.objects.get(id=childid)
        emp = Employee.objects.get(email = user.email)
        approval_obj =  OrgStructureApprovals.objects.create(sender = user,receiver = emp.reported_to,parent = emp.parent,child = child,type = "departments")
        existing_departments = approval_obj.get_departments()
        for department in given_departments:
            if(department not in existing_departments):
                existing_departments.append(department)
        approval_obj.set_departments(existing_departments)
        approval_obj.save()
        message = f"Dear {emp.reported_to.username},We hope this message finds you well.\nWe would like to inform you that there is an action required regarding the addition of departments in our organization.\nYour assistance is needed for defining departments within the organization. Please visit the approvals tab for more details.\nIf you have any questions or require clarification, please don't hesitate to reach out.\nThank you for your cooperation.\nBest regards,\nGA Org Sync"
        Notification.objects.create(sender = user,receiver =  emp.reported_to,message=message)
        try:
            sendemail(
                'Designation Addition - Action Required',
                message,
                [emp.reported_to.email],
            )
        except:
            pass
        return Response({'data': 'Data sent Successfully. Awaiting Approval'}, status=status.HTTP_200_OK)

class FetchDepartments(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        childid = request.data.get('childid')

        employee = Employee.objects.get(email=user.email)
        child = ChildAccount.objects.filter(id=childid).first()

        queryset = Department.objects.filter(parent=employee.parent)

        if child:
            queryset = queryset.filter(child=child)

        data = queryset.values("id", "name")

        return Response({"data": list(data)}, status=status.HTTP_200_OK)

class GetDepartments(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = Department.objects.values("id", "name")
        return Response(data, status=200)

class Designations(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        given_designations = request.data['designations']
        user = request.user
        childid=request.data['childid']
        child=ChildAccount.objects.get(id=childid)
        emp = Employee.objects.get(email = user.email)
        approval_obj =  OrgStructureApprovals.objects.create(sender = user,receiver = emp.reported_to,parent = emp.parent,child = child,type = "designations")
        existing_designations = approval_obj.get_designations()
        for designation in given_designations:
            if(designation not in existing_designations):
                existing_designations.append(designation)
        approval_obj.set_designations(existing_designations)
        approval_obj.save()
        message = f"Dear {emp.reported_to.username},We hope this message finds you well.\nWe would like to inform you that there is an action required regarding the addition of designations in our organization. Your input is crucial in defining these roles.\nYour assistance is needed for defining designations within the organization. Please visit the approvals tab for more details.\nIf you have any questions or require clarification, please don't hesitate to reach out.\nThank you for your cooperation.\nBest regards,\nGA Org Sync"
        Notification.objects.create(sender = user,receiver =  emp.reported_to,message=message)
        try:
            sendemail(
                'Designation Addition - Action Required',
                message,
                [ emp.reported_to.email],
            )
        except:
            pass
        return Response({'data': 'Data sent Successfully. Awaiting Approval'}, status=status.HTTP_200_OK)

class FetchDesignations(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        childid = request.data.get('childid')

        employee = Employee.objects.get(email=user.email)
        child = ChildAccount.objects.filter(id=childid).first()

        queryset = Designation.objects.filter(parent=employee.parent)

        if child:
            queryset = queryset.filter(child=child)

        data = queryset.values("id", "name")

        return Response({"data": list(data)}, status=status.HTTP_200_OK)

class GetDesignations(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = Designation.objects.values("id", "name")
        return Response(data, status=200)

class fetchNotification(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        user = request.user
        notifications = Notification.objects.filter(receiver = user).order_by('-date').values()
        return Response({'data':list(notifications)},status=status.HTTP_200_OK)
    def put(self,request):
        id = request.data.get('id')
        stat = request.data.get('status')
        print(stat)
        notification = Notification.objects.get(id = id)
        if notification:
            if stat == 'Read':
                notification.is_read = True
            elif stat == 'Unread':
                notification.is_read = False
            notification.save()
            return Response({'message':'Updated Successfully.'},status=status.HTTP_200_OK)
        else:
            return Response({'error':'Notification not Found'},status=status.HTTP_404_NOT_FOUND)


class fetchRoles(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        emp = Employee.objects.get(user = user)
        childid=request.data['childid']
        child=ChildAccount.objects.get(id=childid)
        children_ids = emp.child.all().values_list('id', flat=True)
        roles = Roles.objects.filter(parent=emp.parent, child=child).values()
        for i in roles:
            if i['user_id']:
                u = User.objects.get(id = i['user_id'])
                emp = Employee.objects.get(email = u.email)
                i['user'] = emp.userName
            else:
                i['user'] = None
        return Response({'roles': list(roles)}, status=status.HTTP_200_OK)              

class createOrgStructure(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        given_roles = request.data['roles']
        user = request.user
        childid=request.data['childid']
        child=ChildAccount.objects.get(id = childid)
        if ('SUPER_USER' in user.get_roles()):
            for role in given_roles:
                Roles.objects.create(parent = emp.parent,child = child, name = role)
            return Response({'data': 'Roles created Successfully.'}, status=status.HTTP_200_OK)
        else:
            emp = Employee.objects.get(email = user.email)
            approval_obj = OrgStructureApprovals.objects.create(sender = user,receiver = emp.reported_to,parent = emp.parent,child = child,type='roles')
            existing_role = approval_obj.get_roles()
            for role in given_roles:
                existing_role.append(role)
            approval_obj.set_roles(existing_role)
            approval_obj.save()    
            message = f"Dear {emp.reported_to.username},\nWe hope this message finds you well.\nWe are writing to inform you that {emp.userName} requires your approval for defining roles within the organization. Your prompt attention to this matter is greatly appreciated.\nPlease visit the approvals tab for more details and to provide your approval.\nIf you have any questions or need further information, feel free to contact our support team.\nThank you for your cooperation.\nBest regards,\nGA Org Sync"
            message = f"{emp.userName} needs an approval for defining the roles in the organization. Please visit approvals tab for more details."
            Notification.objects.create(sender = user,receiver = emp.reported_to,message=message)
            try:
                sendemail(
                    'Approval Needed for Defining Roles',
                    message,
                    [emp.reported_to.email],
                )
            except:
                pass
            return Response({'data': 'Data sent Successfully. Awaiting Approval'}, status=status.HTTP_200_OK)


class fetchApprovals(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        user = request.user
        my_approvals = OrgStructureApprovals.objects.filter(receiver = user)
        my_serializer = OrgStructureApprovalsSerializer(my_approvals, many=True)
        pending_approvals = OrgStructureApprovals.objects.filter(sender = user)
        p_serializer = OrgStructureApprovalsSerializer(pending_approvals, many=True)
        return Response({'my': my_serializer.data,'awaiting':p_serializer.data}, status=status.HTTP_200_OK)

class updateApproval(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        user = request.user
        id = request.data.get('id')
        stat = request.data.get('status')
        try:
            app = OrgStructureApprovals.objects.get(id = id)
            child = app.child
            sender = app.sender
            emp = Employee.objects.get(user = sender)
            if(stat == "approved"):
                if app.type == "roles":
                    roles = app.get_roles()
                    for role in roles:
                        Roles.objects.create(parent = emp.parent,child = child, name = role)
                if app.type == "departments":
                    depts = app.get_departments()
                    for dept in depts:
                        Department.objects.create(parent = emp.parent,child = child, name = dept)
                if app.type == "designations":
                    desigs = app.get_designations()
                    for desig in desigs:
                        Designation.objects.create(parent = emp.parent,child = child, name = desig)
            app.status = stat
            app.save()
            return Response({'message':'Status Updated Successfully'},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class QuoteUpload(APIView):
    @transaction.atomic
    def post(self,request,**kwargs):
        print("entered")
        file = request.FILES.get('file')
        print(file)
        if not file:
            return Response({"error": "No file provided in the request"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with file.open() as file:
                name_sheet_file = file.read().decode('utf-8')
                csv_reader = csv.reader(name_sheet_file.splitlines())
                next(csv_reader)
                for row in csv_reader:
                    print(row)
                    quote=row[0]
                    if row!="":
                        print("entered")
                        Quotes.objects.create(quote=quote)
            return Response({'message':'Quotes Uploaded Successfully'},status=status.HTTP_200_OK)
        except:
            pass
        return Response({"error": "Something went wrong"}, status=status.HTTP_400_BAD_REQUEST)

def GenerateQuote(request):
    quotes=len(Quotes.objects.all())
    quote=random.randint(0,quotes-1)
    for parent in Organization.objects.all():
        parent.quote=QuoteSerializer(Quotes.objects.get(id=quote)).data['quote']
        parent.save()

def verify_otp(email, otp):
    stored_otp = otp_storage.get(email)
    return stored_otp == otp


def generate_otp():
    digits = "0123456789"
    otp = ""
    for _ in range(6): 
        otp += random.choice(digits)
    return otp

otp_storage = {}

class OtpVerification(APIView):
    def get(self, request):
        email = request.query_params.get('email')
        if email:
            otp = generate_otp()
            send_otp_email(email, otp)
            otp_storage[email] = otp
            return Response(status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Email not provided'}, status=status.HTTP_400_BAD_REQUEST)
    def post(self, request):   
        data = request.data
        email = data.get('email')
        otp = data.get('otp')
        if email and otp:
            if verify_otp(email, otp):
                del otp_storage[email]
                return Response(status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid OTP'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({'error': 'Email or OTP not provided'}, status=status.HTTP_400_BAD_REQUEST)



class FetchOptionalHolidays(APIView):
    def post(self, request):
        user = request.user
        try:
            employee = Employee.objects.get(user=user)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

        childid = request.data.get('childid')
        try:
            child = ChildAccount.objects.get(id=childid)
        except ChildAccount.DoesNotExist:
            return Response({"error": "Child account not found"}, status=status.HTTP_404_NOT_FOUND)
        year=datetime.now().year
        holidays = OptionalHolidays.objects.filter(child=child,date__year=year).exclude(
            id__in=EmployeeOptHoliday.objects.filter(employee=employee).values_list('holiday_id', flat=True)
        )
        data = OptionalHolidaysSerializer(holidays, many=True)
        return Response(data.data, status=status.HTTP_200_OK)

class EmpOptionalHolidays(APIView):
    def post(self,request):
        user=request.user
        current_year = datetime.now().year
        childid=request.data['childid']
        child=ChildAccount.objects.get(id=childid)
        no_of_days_allowed=OptionalHolidaysPolicy.objects.get(child=child).opt_holidays_allowed
        employee=Employee.objects.get(user=user)
        length=len(EmployeeOptHoliday.objects.filter(timestamp__year=current_year,employee=employee))
        print("length",length)
        if length<no_of_days_allowed:
            parent=employee.parent
            holidayid=request.data['id']
            holiday=OptionalHolidays.objects.get(id=holidayid)
            print(holiday)
            work_delegated=request.data['workDelegated']
            workDelegated=Employee.objects.get(id=work_delegated)
            print(workDelegated)
            comments=request.data['comments']
            print(comments)
            EmployeeOptHoliday.objects.create(parent=parent,child=child,employee=employee,holiday=holiday,workDelegated=workDelegated,comments=comments)
            message=f"your Employee {employee} applied for an Optional Holiday for {holiday.name} on {holiday.date}"
            try:
                sendemail('Applied for an Optional Holiday',message,[child.HrHead.email])
            except:
                pass
            Notification.objects.create(sender=user,receiver=child.HrHead,message=message)
        else:
            return Response({'message': 'You have already crossed the limit for optional holidays'}, status=status.HTTP_403_FORBIDDEN)
        return Response({'message': 'Holiday request submitted successfully'}, status=status.HTTP_200_OK)
    def get(self,request):
        user=request.user
        year = datetime.now().year
        employee=Employee.objects.get(user=user)
        emp_opt_holidays=EmployeeOptHoliday.objects.filter(employee=employee,timestamp__year=year)
        data=EmployeeOptHolidaySerializer(emp_opt_holidays,many=True)
        return Response(data.data, status=status.HTTP_200_OK)


# class fetchNotificationscount(APIView):
#     def get(self,request):
#         user = request.user
#         notifications = Notification.objects.filter(receiver = user,is_read = False)
#         return Response({"notifications": len(notifications)}, status=status.HTTP_201_CREATED)

class fetchNotifications(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(
            receiver=request.user
        ).order_by("-date")

        return Response({
            "data": [
                {
                    "id": n.id,
                    "message": n.message,
                    "is_read": n.is_read,
                    "date": n.date,
                }
                for n in notifications
            ]
        }, status=status.HTTP_200_OK)

    def put(self, request):
        notif_id = request.data.get("id")
        status_value = request.data.get("status")  # "Read" / "Unread"

        if not notif_id:
            return Response(
                {"error": "Notification id required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        is_read = True if status_value == "Read" else False

        Notification.objects.filter(
            id=notif_id,
            receiver=request.user
        ).update(is_read=is_read)

        return Response(
            {"message": "Notification updated"},
            status=status.HTTP_200_OK
        )
class fetchNotificationsCount(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        unread_count = Notification.objects.filter(
            receiver=request.user,
            is_read=False
        ).count()

        return Response(
            {"notifications": unread_count},
            status=status.HTTP_200_OK
        )    
class uploadHolidays(APIView):
    permission_classes = [IsAuthenticated]
    @transaction.atomic
    def post(self,request,**kwargs):
        user = request.user
        childid=request.data['childid']
        child = ChildAccount.objects.get(id = childid)
        if child:
            parent = child.parent
        else:
            parent=Employee.objects.get(user=user).parent
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file provided in the request"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with file.open() as file:
                name_sheet_file = file.read().decode('utf-8')
                csv_reader = csv.reader(name_sheet_file.splitlines())
                next(csv_reader)
                for row in csv_reader:
                    names,dates= row
                    date=datetime.strptime(dates, '%Y-%m-%d')
                    try :
                        Holidays.objects.create(parent=parent,child=child,name=names,date=date)
                    except Exception as e:
                        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
                return Response({"message": "Uploaded Holidays Information  successfully"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class uploadOptionalHolidays(APIView):
    permission_classes = [IsAuthenticated]
    @transaction.atomic
    def post(self,request,**kwargs):
        user = request.user
        childid=request.data['childid']
        child = ChildAccount.objects.get(id = childid)
        if child:
            parent = child.parent
        else:
            parent=Employee.objects.get(user=user).parent
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file provided in the request"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with file.open() as file:
                name_sheet_file = file.read().decode('utf-8')
                csv_reader = csv.reader(name_sheet_file.splitlines())
                next(csv_reader)
                for row in csv_reader:
                    names,dates= row
                    date=datetime.strptime(dates, '%Y-%m-%d')
                    try :
                        OptionalHolidays.objects.create(parent=parent,child=child,name=names,date=date)
                        print("entered")
                    except Exception as e:
                        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
                return Response({"message": "Uploaded Optional Holidays Information  successfully"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GetHolidays(APIView):
    def post(self,request):
        user=request.user 
        childid=request.data['childid']
        month = request.data.get('month')
        year = request.data.get('year')
        child=ChildAccount.objects.get(id=childid)
        if child:
            parent = child.parent
        else:
            employee=Employee.objects.get(user=user)
            parent=employee.parent
        if month and year:
            holidays = Holidays.objects.filter(parent=parent, child=child, date__month=month, date__year=year)
        else:
            holidays = Holidays.objects.filter(parent=parent, child=child)
        count = holidays.count()
        holidays_data = holidays.values()
        return Response({'count': count, 'holidays': list(holidays_data)}, status=status.HTTP_200_OK)


class GetYearsMonths(APIView):
    def post(self, request):
        user = request.user
        child_id = request.data.get('id')
        employee = Employee.objects.get(user=user)
        parent = employee.parent
        dateofreg = parent.timestamp
        if child_id:
            child = ChildAccount.objects.get(id=child_id)
        else:
            child = None
        start_year = dateofreg.year
        start_month = dateofreg.month
        if start_year is None or start_month is None:
            return Response("No data available.", status=status.HTTP_400_BAD_REQUEST)
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month
        years_months = {}
        for year in range(start_year, current_year + 1):
            start = start_month if year == start_year else 1
            end = 12 if year != current_year else current_month
            months = []
            for month in range(start, end+1):
                months.append(month)
            years_months[year] = months
        return Response({'data': years_months}, status=status.HTTP_200_OK)



class Greetings(APIView):
    def get(self,request):
        user = request.user
        employee = Employee.objects.get(user = user)
        employeeGreetings = EmployeeOccasions.objects.filter(employee=employee,date = datetime.today())
        if employeeGreetings:
            serializer = EmpOccSetializer(employeeGreetings,many=True)
            return Response({'data':serializer.data},status=status.HTTP_200_OK)
    def post(self,request):
        user = request.user
        childid = request.data.get('childid')
        if childid:
            child = ChildAccount.objects.get(id=childid)
        else:
            child = None
        employee = Employee.objects.get(user = user)
        employeeGreetings = EmployeeOccasions.objects.filter(parent=employee.parent,date = datetime.today(),child=child)
        if employeeGreetings:
            serializer = EmpOccSetializer(employeeGreetings,many=True)
            return Response({'data':serializer.data},status=status.HTTP_200_OK) 



class isReportingManager(APIView):
    def post(self,request):
        user=request.user
        childid=request.data['childid']
        child=ChildAccount.objects.get(id=childid)
        employee=Employee.objects.get(user=user)
        parent=employee.parent
        employees=Employee.objects.filter(parent=parent,child=child,reported_to=user,status="onroll")
        if len(employees)>0:
            return Response({"isRM": True}, status=status.HTTP_200_OK)
        else:
            return Response({"isRM": False}, status=status.HTTP_200_OK)


class IpRestriction(APIView):
    def post(self, request):
        user=request.user
        id=request.data['childid']
        employee=Employee.objects.get(user=user)
        child=ChildAccount.objects.get(id=id)
        ipvalue=request.data['iprestriction']
        child.iprestriction=ipvalue
        child.save()
        return Response({'success': 'IP restriction updated successfully'}, status=status.HTTP_200_OK)

class FetchIP(APIView):
    def post(self, request):
        id=request.data['childid']
        child=ChildAccount.objects.get(id=id)
        return Response({'enabled':child.iprestriction,'success':"IP restriction updated successfully"},status=status.HTTP_200_OK)

class FetchOptionalHolidaysforHr(APIView):
    def post(self, request):
        user=request.user
        childid=request.data['childid']
        child=ChildAccount.objects.get(id=childid)
        holidays=EmployeeOptHoliday.objects.filter(child=child)
        serializer=EmployeeOptHolidaySerializer(holidays,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GetEmployeeBirthdays(APIView):
    def post(self,request):
        childid=request.data['childid']
        child=ChildAccount.objects.get(id=childid)
        employees=Employee.objects.filter(child=child,status="onroll")
        finaldata={}
        data=EmployeeSerializer(employees,many=True).data
        return Response(data, status=status.HTTP_200_OK)




class MonthlyDataAPIView(APIView):

    def get(self, request):
        child_id = request.GET.get('child_id')
        child=ChildAccount.objects.get(id = child_id)
        data = MonthlyData.objects.filter(child=child).order_by('year', 'month')
        serializer = MonthlyDataSerializer(data,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        try:
            data = request.data
            new_entry = MonthlyData.objects.create(
                year=data.get('year'),
                month=data.get('month'),
                no_of_working_days=data.get('no_of_working_days'),
                parent_id=data.get('parent'),
                child_id=data.get('child')
            )
            return Response({"message": "Monthly Data created successfully"}, status=status.HTTP_201_CREATED)
        except KeyError as e:
            return Response({'error': f'Missing field: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        try:
            data = request.data
            obj_id = data.get('id')
            entry = MonthlyData.objects.get(id=obj_id)
            entry.no_of_working_days = data.get('no_of_working_days', entry.no_of_working_days)
            entry.save()
            return Response({"message": "Monthly Data updated successfully"}, status=status.HTTP_200_OK)
        except MonthlyData.DoesNotExist:
            return Response({'error': 'MonthlyData not found'}, status=status.HTTP_404_NOT_FOUND)
        except KeyError as e:
            return Response({'error': f'Missing field: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

class AssetsView(APIView):
    def get(self,request):
        try:
            child_id = request.GET.get('child_id')
            child = ChildAccount.objects.get(id=child_id)
            data = Assets.objects.filter(child=child)
            serializer = AssetsSerializer(data,many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
    def post(self,request):
        try:
            child_id = request.data.get('child_id')
            child = ChildAccount.objects.get(id=child_id)
            name = request.data.get('name')
            dep_id = request.data.get('dep_id')
            department = Department.objects.get(id=dep_id)
            Assets.objects.create(name=name,child=child,parent=child.parent,department=department)
            return Response({"message": "Asset added successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
    def put(self,request):
        try:
            asset = Assets.objects.get(id=request.data.get('id'))
            asset.name = request.data.get('name')
            asset.save()
            return Response({"message": "Asset updated successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
    def delete(self,request):
        try:
            asset = Assets.objects.get(id=request.data.get('id'))
            asset.delete()
            return Response({"message": "Asset deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class AssetDetailsView(APIView):
    def get(self, request):
        try:
            asset_id = request.GET.get('asset_id')
            asset = Assets.objects.get(id=asset_id)
            data = AssetDetails.objects.filter(asset=asset)
            serializer = AssetDetailsSerializer(data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            asset_id = request.data.get('asset_id')
            asset = Assets.objects.get(id=asset_id)
            serial_number = request.data.get('serial_number')
            configuration = request.data.get('configuration')

            AssetDetails.objects.create(
                asset=asset,
                serial_number=serial_number,
                configuration=configuration
            )

            return Response({"message": "Asset details added successfully"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        try:
            asset_details_id = request.data.get('id')
            asset_details = AssetDetails.objects.get(id=asset_details_id)

            asset_details.serial_number = request.data.get('serial_number')
            asset_details.configuration = request.data.get('configuration')
            asset_details.save()

            return Response({"message": "Asset details updated successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        try:
            asset_details_id = request.data.get('id')
            asset_details = AssetDetails.objects.get(id=asset_details_id)
            asset_details.delete()

            return Response({"message": "Asset details deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EmployeeAssetFormView(APIView):
    def get(self, request):
        try:
            child_id = request.GET.get('child_id')
            child = ChildAccount.objects.get(id=child_id)
            employees = Employee.objects.filter(child=child)
            employee_data = []
            index = 1
            for employee in employees:
                issued_assets = EmployeeAssetForm.objects.filter(employee=employee)
                issued_assets_data = EmployeeAssetFormSerializer(issued_assets, many=True).data
                employee_s_data = EmployeeSerializer(employee).data
                employee_data.append({
                    'index':index,
                    'employee': employee_s_data,
                    'issued_assets': issued_assets_data,
                })
                index += 1

            return Response(employee_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            employee_id = request.data.get('employee_id')
            asset_detail_id = request.data.get('asset_configuration')
            user = request.user

            employee = Employee.objects.get(id=employee_id)
            asset_detail = AssetDetails.objects.get(id=asset_detail_id)
            issued_by = Employee.objects.get(user=user)

            EmployeeAssetForm.objects.create(
                employee=employee,
                assetdetails=asset_detail,
                issuedBy=issued_by,
                is_issued=True,
            )

            return Response({"message": "Asset issued successfully"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        try:
            issuance_id = request.data.get('id')
            issuance_record = EmployeeAssetForm.objects.get(id=issuance_id)
            issuance_record.is_issued = request.data.get('is_issues', issuance_record.is_issues)
            issuance_record.assetdetails = AssetDetails.objects.get(id=request.data.get('asset_detail_id', issuance_record.assetdetails.id))
            issuance_record.save()

            return Response({"message": "Asset issuance updated successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        try:
            issuance_id = request.data.get('id')
            issuance_record = EmployeeAssetForm.objects.get(id=issuance_id)
            issuance_record.delete()

            return Response({"message": "Asset issuance record deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BroadCastMessageView(APIView):
    def get(self,request):
        user = request.user
        if user:
            child_id = request.GET.get('child_id')
            child = ChildAccount.objects.get(id=child_id)
            parent = child.parent
            messages = BroadcastCommunications.objects.filter(parent=parent,child=child).order_by('-timestampp')
            serializer = BroadcastCommunicationSerializer(messages,many=True)
            return Response({'data':serializer.data},status=status.HTTP_200_OK)
        else:
            return Response({"error": "Login to continue"}, status=status.HTTP_404_NOT_FOUND)
    def post(self,request):
        try:
            user = request.user
            child_id = request.data.get('child_id')
            child = ChildAccount.objects.get(id=child_id)
            employee = Employee.objects.get(user=user)
            sender = employee
            content = request.data.get('content')
            ist = pytz.timezone('Asia/Kolkata')
            now_utc = timezone.now()
            timestampp = now_utc.astimezone(ist)
            broadcast = BroadcastCommunications.objects.create(sender=sender,child=child,content=content,timestampp = timestampp,parent = child.parent)
            message=f"You have a new communication from {sender.userName}.\n\nContent: \n\n{content}"
            for emp in Employee.objects.filter(main_child=child,parent=child.parent):
                sendemail('New Communication',message,[emp.email])
            return Response({'message':'Communication Sent'},status = status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class getAttendanceType(APIView):
    def get(self,request):
        user = request.user
        if user:
            try:
                employee = Employee.objects.get(user=user)
                ptype = employee.main_child.attendanceType
                return Response({'data':ptype},status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
Employee = apps.get_model('payrollapp', 'Employee')

# class CertificationsView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         user = request.user
#         emp = Employee.objects.get(user=user)
#         certs = EmployeeCertifications.objects.filter(employee=emp)
#         serializer = EmployeeCertificationsSerializer(certs, many=True)
#         return Response({"data": serializer.data})

#     def post(self, request):
#         user = request.user
#         emp = Employee.objects.get(user=user)
#         data = request.data
#         data["employee"] = emp.id

#         serializer = EmployeeCertificationsSerializer(data=data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({"message": "Certification added", "data": serializer.data})
#         return Response(serializer.errors, status=400)

#     def put(self, request):
#         cert = EmployeeCertifications.objects.get(id=request.data.get("id"))
#         serializer = EmployeeCertificationsSerializer(cert, data=request.data, partial=True)

#         if serializer.is_valid():
#             serializer.save()
#             return Response({"message": "Certification updated"})
#         return Response(serializer.errors, status=400)

#     def delete(self, request):
#         cert = EmployeeCertifications.objects.get(id=request.data.get("id"))
#         cert.delete()
#         return Response({"message": "Certification deleted"})
class CertificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        emp = Employee.objects.get(user=user)
        certs = EmployeeCertifications.objects.filter(employee=emp)
        serializer = EmployeeCertificationsSerializer(certs, many=True)
        return Response({"data": serializer.data})

    def post(self, request):
        user = request.user
        emp = Employee.objects.get(user=user)
        data = request.data
        data["employee"] = emp.id

        serializer = EmployeeCertificationsSerializer(data=data)
        if serializer.is_valid():
            cert = serializer.save()

            # 🔥 STEP-2: RESET NOTIFICATION FLAGS
            cert.notified_30_days = False
            cert.notified_on_expiry = False
            cert.notified_after_expiry = False
            cert.save(update_fields=[
                "notified_30_days",
                "notified_on_expiry",
                "notified_after_expiry"
            ])

            return Response(
                {"message": "Certification added", "data": serializer.data},
                status=200
            )
        return Response(serializer.errors, status=400)

    def put(self, request):
        cert = EmployeeCertifications.objects.get(id=request.data.get("id"))
        serializer = EmployeeCertificationsSerializer(cert, data=request.data, partial=True)

        if serializer.is_valid():
            updated_cert = serializer.save()

            # 🔥 STEP-2: RESET NOTIFICATION FLAGS
            updated_cert.notified_30_days = False
            updated_cert.notified_on_expiry = False
            updated_cert.notified_after_expiry = False
            updated_cert.save(update_fields=[
                "notified_30_days",
                "notified_on_expiry",
            ])

            return Response({"message": "Certification updated"}, status=200)
        return Response(serializer.errors, status=400)

    def delete(self, request):
        cert = EmployeeCertifications.objects.get(id=request.data.get("id"))
        cert.delete()
        return Response({"message": "Certification deleted"})

class SkillsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        emp = Employee.objects.get(user=user)
        skills = EmployeeSkills.objects.filter(employee=emp)
        serializer = EmployeeSkillsSerializer(skills, many=True)
        return Response({"data": serializer.data})

    def post(self, request):
        user = request.user
        emp = Employee.objects.get(user=user)
        data = request.data
        data["employee"] = emp.id

        serializer = EmployeeSkillsSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Skill added", "data": serializer.data})
        return Response(serializer.errors, status=400)

    def put(self, request):
        skill = EmployeeSkills.objects.get(id=request.data.get("id"))
        serializer = EmployeeSkillsSerializer(skill, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Skill updated"})
        return Response(serializer.errors, status=400)

    def delete(self, request):
        skill = EmployeeSkills.objects.get(id=request.data.get("id"))
        skill.delete()
        return Response({"message": "Skill deleted"})

    
class HandleImages(APIView):     # ✅ Standardized class name
    permission_classes = [IsAuthenticated]
    
    # ======================= UPLOAD FILES ============================
    def put(self, request, *args, **kwargs):
        user = request.user
        emp = get_object_or_404(Employee, user=user)
        print("put image ")

        doc_type = request.data.get("type")
        image = request.FILES.get("image")

        if not doc_type:
            return Response({"error": "Type is required"}, status=400)

        if not image:
            return Response({"error": "No file received"}, status=400)

        # Create Document instance if missing
        obj, created = Document.objects.get_or_create(employee=emp)

        # ==================== MAIN DOCUMENTS ====================
        if doc_type == "profile":
            obj.profile = image

        elif doc_type == "aadhaar":
            obj.aadhar = image

        elif doc_type == "pan":
            obj.panCard = image

        elif doc_type == "offerLetter":
            obj.offerLetter = image

        elif doc_type == "pfdeclaration":
            obj.pfdeclaration = image

        elif doc_type == "esi":
            obj.esi_card = image

        # ===================== EXPERIENCE DOCS =====================
        elif doc_type in ["rletter", "pay1", "pay2", "pay3"]:
            exp_id = request.data.get("id")
            if not exp_id:
                return Response({"error": "Experience ID is required"}, status=400)

            exp = get_object_or_404(EmployeeExperience, id=exp_id)

            if doc_type == "rletter":
                exp.attach_relieving_letter = image
            elif doc_type == "pay1":
                exp.payslip_1 = image
            elif doc_type == "pay2":
                exp.payslip_2 = image
            elif doc_type == "pay3":
                exp.payslip_3 = image

            exp.save()
            return Response({"message": "Successfully Updated"}, status=200)

        # ===================== EDUCATION DOCS ========================
        elif doc_type == "education_proof":
            edu_id = request.data.get("id")
            if not edu_id:
                return Response({"error": "Education ID required"}, status=400)

            try:
                edu = EmployeeEducationDetails.objects.get(id=edu_id)
                edu.education_proof = image
                edu.save()
                return Response({"message": "Education file uploaded"}, status=200)
            except EmployeeEducationDetails.DoesNotExist:
                return Response({"error": "Education not found"}, status=404)

        # ==================== CERTIFICATION FILES ====================
        elif doc_type == "certificate_file":
            cert_id = request.data.get("id")
            if not cert_id:
                return Response({"error": "Certificate ID required"}, status=400)

            try:
                cert = EmployeeCertifications.objects.get(id=cert_id)
                cert.certificate_file = image
                cert.save()
                return Response({"message": "Certificate uploaded"}, status=200)
            except EmployeeCertifications.DoesNotExist:
                return Response({"error": "Certification not found"}, status=404)

        else:
            return Response({"error": "Invalid document type"}, status=400)

        obj.save()
        return Response({"message": "Successfully Updated"}, status=200)

    def get(self, request, *args, **kwargs):
        print("===== GET DOCUMENT API HIT =====")
        user = request.user
        print("REQUEST USER:", user, "ID:", getattr(user, "id", None))
        try:
            emp = Employee.objects.get(user=user)
            print("EMPLOYEE FOUND:", emp.id)
            doc = Document.objects.get(employee=emp)
            print("DOCUMENT FOUND:", doc.id)
        except Employee.DoesNotExist:
            print("❌ Employee does NOT exist for user")
            return Response(
            {"error": "Employee not found"},
            status=status.HTTP_404_NOT_FOUND)
        except Document.DoesNotExist:
            print("❌ Document does NOT exist for employee")
            return Response(
            {"error": "Documents not found"},
            status=status.HTTP_404_NOT_FOUND
        )
        print("PROFILE FILE:", doc.profile)
        print("AADHAAR FILE:", doc.aadhar)
        print("PAN FILE:", doc.panCard)
        print("OFFER LETTER FILE:", doc.offerLetter)
        print("PF DECLARATION FILE:", doc.pfdeclaration)
        print("ESI FILE:", doc.esi_card)
        data = {
        "profile": doc.profile.url if doc.profile else None,
        "aadhaar": doc.aadhar.url if doc.aadhar else None,
        "pan": doc.panCard.url if doc.panCard else None,
        "offerLetter": doc.offerLetter.url if doc.offerLetter else None,
        "pfdeclaration": doc.pfdeclaration.url if doc.pfdeclaration else None,
        "esi": doc.esi_card.url if doc.esi_card else None,
    }
        print("RESPONSE DATA:", data)
        print("===== END GET DOCUMENT API =====")
        return Response({"data": data}, status=status.HTTP_200_OK)

class GethandleImages(APIView):

    def post(self, request, *args, **kwargs):
        emp_id = request.data.get('id')

        if not emp_id:
            return Response({'error': 'Employee ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        emp = get_object_or_404(Employee, id=emp_id)
        obj, created = Document.objects.get_or_create(employee=emp)

        data = {
            'pan_image': str(obj.panCard.url) if obj.panCard else None,
            'aadhar_image': str(obj.aadhar.url) if obj.aadhar else None,
            'profile_image': str(obj.profile.url) if obj.profile else None,
            'offer_letter': str(obj.offerLetter.url) if obj.offerLetter else None,
            'pf_declaration': str(obj.pfdeclaration.url) if obj.pfdeclaration else None,
            'esi_card': str(obj.esi_card.url) if obj.esi_card else None
        }

        return Response({'data': data}, status=status.HTTP_200_OK)


# class AssignedPendingVerifications(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         user = request.user

#         try:
#             my_employee = Employee.objects.get(user=user)
#         except Employee.DoesNotExist:
#             return Response({"error": "Employee profile not found"}, status=400)

#         if not can_verify_document(user):
#             return Response({"data": []}, status=200)

#         employees = Employee.objects.filter(parent=my_employee.parent)

#         result = []

#         for emp in employees:
#             doc_obj = Document.objects.filter(employee=emp).first()
#             all_verifications = (DocumentVerification.objects.filter(employee=emp).order_by("document_type", "-created_at"))
#             latest_map = {}
#             for v in all_verifications:
#                 if v.document_type not in latest_map:
#                     latest_map[v.document_type] = v
#             verifications = latest_map.values()

#             verification_summary = {
#                  v.document_type: {
#                      "status": v.status,
#                      "comment": v.comment,
#                      "verified_by": getattr(v.verified_by, "email", None),
#                      "verified_at": v.verified_at,
#                      }
#                      for v in verifications
# }
#             statuses = [v["status"] for v in verification_summary.values()]
#             if statuses and all(s == "ACCEPTED" for s in statuses):
#                 overall_status = "VERIFIED"
#             elif "REJECTED" in statuses:
#                 overall_status = "REJECTED"
#             else:
#                 overall_status = "PENDING"

#             result.append({
#                 "employee_id": str(emp.id),
#                 "employee_name": emp.userName,
#                  "overall_status": overall_status,  
#                 "documents": {
#                     "aadhaar": doc_obj.aadhar.url if doc_obj and doc_obj.aadhar else None,
#                     "pan": doc_obj.panCard.url if doc_obj and doc_obj.panCard else None,
#                     "profile": doc_obj.profile.url if doc_obj and doc_obj.profile else None,
#                     "offerLetter": doc_obj.offerLetter.url if doc_obj and doc_obj.offerLetter else None,
#                     "pfdeclaration": doc_obj.pfdeclaration.url if doc_obj and doc_obj.pfdeclaration else None,
#                     "esi": doc_obj.esi_card.url if doc_obj and doc_obj.esi_card else None,
#                 },
#                 "verification_summary": verification_summary,
#             })

#         return Response({"data": result}, status=200)
class AssignedPendingVerifications(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # 1️⃣ Get logged-in employee
        try:
            my_employee = Employee.objects.get(user=user)
        except Employee.DoesNotExist:
            return Response(
                {"error": "Employee profile not found"},
                status=400
            )

        # 2️⃣ Permission check
        if not can_verify_document(user):
            return Response({
                "count": 0,
                "current_page": 1,
                "results": []
            }, status=200)

        # 3️⃣ Base queryset (ORDERED for pagination)
        employees = Employee.objects.filter(
            parent=my_employee.parent
        ).order_by("-id")

        # 4️⃣ Apply pagination
        paginator = DocumentVerificationPagination()
        paginated_employees = paginator.paginate_queryset(
            employees, request
        )

        result = []

        # 5️⃣ Build response ONLY for paginated employees
        for emp in paginated_employees:
            doc_obj = Document.objects.filter(employee=emp).first()

            all_verifications = (
                DocumentVerification.objects
                .filter(employee=emp)
                .order_by("document_type", "-created_at")
            )

            latest_map = {}
            for v in all_verifications:
                if v.document_type not in latest_map:
                    latest_map[v.document_type] = v

            verification_summary = {
                v.document_type: {
                    "status": v.status,
                    "comment": v.comment,
                    "verified_by": getattr(v.verified_by, "email", None),
                    "verified_at": v.verified_at,
                }
                for v in latest_map.values()
            }

            statuses = [v["status"] for v in verification_summary.values()]

            if statuses and all(s == "ACCEPTED" for s in statuses):
                overall_status = "VERIFIED"
            elif "REJECTED" in statuses:
                overall_status = "REJECTED"
            else:
                overall_status = "PENDING"

            result.append({
                "employee_id": str(emp.id),
                "employee_name": emp.userName,
                "overall_status": overall_status,
                "documents": {
                    "aadhaar": doc_obj.aadhar.url if doc_obj and doc_obj.aadhar else None,
                    "pan": doc_obj.panCard.url if doc_obj and doc_obj.panCard else None,
                    "profile": doc_obj.profile.url if doc_obj and doc_obj.profile else None,
                    "offerLetter": doc_obj.offerLetter.url if doc_obj and doc_obj.offerLetter else None,
                    "pfdeclaration": doc_obj.pfdeclaration.url if doc_obj and doc_obj.pfdeclaration else None,
                    "esi": doc_obj.esi_card.url if doc_obj and doc_obj.esi_card else None,
                },
                "verification_summary": verification_summary,
            })

        # 6️⃣ Return paginated response
        return paginator.get_paginated_response(result)


def can_verify_document(user):
    try:
        my_employee = Employee.objects.get(user=user)
    except Employee.DoesNotExist:
        return False

    my_roles = list(
        my_employee.roles.values_list("name", flat=True)
    )
    if "HR_HEAD" in my_roles:
        return True
    return DocumentAccessRule.objects.filter(
        role__in=my_roles,
        function="Document Verification",
        specific_action="Verify",
        access="Access",
        parent=my_employee.parent
    ).exists()

class VerifyDocumentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data

        emp_id = data.get("employee_id")
        doc_type = data.get("document_type")
        action = (data.get("action") or "").upper()
        comment = data.get("comment", "").strip()

        if action not in ("ACCEPTED", "REJECTED"):
            return Response({"error": "Invalid action"}, status=400)

        if action == "REJECTED" and not comment:
            return Response({"error": "Comment required"}, status=400)

        employee = get_object_or_404(Employee, id=emp_id)

        # ✅ permission check (CORRECT)
        if not can_verify_document(user):
            return Response(
                {"error": "Not authorized to verify documents"},
                status=403
            )

        # ✅ FIX: fetch employee of logged-in user
        my_employee = Employee.objects.get(user=user)
        my_roles = list(my_employee.roles.values_list("name", flat=True))
        latest = (
    DocumentVerification.objects
    .filter(employee=employee, document_type=doc_type)
    .order_by("-created_at")
    .first()
)
        if latest:
            if action == "ACCEPTED":
                latest.mark_accepted(user)
            else:latest.mark_rejected(user, comment)
            dv = latest   # ✅ FIX: ALWAYS assign d
        else:
            dv = DocumentVerification.objects.create(employee=employee,document_type=doc_type,status=action,comment=comment if action == "REJECTED" else "",verified_by=user,verified_at=timezone.now(),assigned_role=my_roles[0] if my_roles else None
    )

        serializer = DocumentVerificationSerializer(dv)
        return Response({"data": serializer.data}, status=200)

class EmployeesByRole(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role_name = request.GET.get("role")

        if not role_name:
            return Response({"data": []}, status=200)

        employees = Employee.objects.filter(
            roles__name=role_name
        ).distinct()

        return Response({
            "data": [
                {
                    "id": emp.id,
                    "name": emp.userName,
                    "email": emp.email,
                }
                for emp in employees
            ]
        }, status=200)

class EmployeeVerificationHistory(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id):
        employee = get_object_or_404(Employee, id=employee_id)

        user = request.user

        # HR_Admin can view all
        if hasattr(user, "employee"):
            my_roles = user.employee.roles.all()
            role_names = [r.name.lower() for r in my_roles]
        else:
            role_names = []

        if "hr_head" not in role_names:
            allowed = DocumentAccessRule.objects.filter(
                Q(target_employee=employee) |
                Q(role__in=my_roles)
            ).exists()

            if not allowed:
                return Response(
                    {"error": "Not authorized to view verification history"},
                    status=403
                )

        verifications = DocumentVerification.objects.filter(
            employee=employee
        ).order_by("-created_at")

        serializer = DocumentVerificationSerializer(verifications, many=True)
        return Response({"data": serializer.data}, status=200)
class AllowedActionsByRole(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = request.GET.get("role")
        employee_id = request.GET.get("employee")

        if not role:
            return Response({"data": []}, status=200)

        # HR_Admin → ALL actions
        # HR_HEAD → ALL actions
        if role.upper() == "HR_HEAD":
            return Response({
                "data": ["View", "Download", "Verify", "Reject"]
            }, status=200)

        rules = DocumentAccessRule.objects.filter(
            role=role,
            access="Access"
        )

        # If employee-specific rule exists, filter it
        if employee_id:
            rules = rules.filter(
                target_employee_id=employee_id
            )

        actions = list(
            rules.values_list("specific_action", flat=True).distinct()
        )

        return Response({"data": actions}, status=200)    
class DocumentAccessRuleDetail(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DocumentAccessRuleSerializer
    lookup_field = "id"

    def get_queryset(self):
        emp = get_user_employee(self.request.user)
        if not emp:
            return DocumentAccessRule.objects.none()
        return DocumentAccessRule.objects.filter(parent=emp.parent)


    @transaction.atomic
    def perform_update(self, serializer):
        rule = serializer.save()
        if rule.access == "Access" and rule.specific_action == "Verify" and rule.target_employee:
            docs = Document.objects.filter(employee=rule.target_employee)

        DOCUMENT_FIELDS = {
            "profile": docs.first().profile,
            "aadhaar": docs.first().aadhar,
            "pan": docs.first().panCard,
            "offerLetter": docs.first().offerLetter,
            "pfdeclaration": docs.first().pfdeclaration,
            "esi": docs.first().esi_card,
        }

        for doc_type, file in DOCUMENT_FIELDS.items():
            if file:
                DocumentVerification.objects.get_or_create(
                    employee=rule.target_employee,
                    document_type=doc_type,
                    defaults={"assigned_role": rule.role}
                )


    @transaction.atomic
    def perform_destroy(self, instance):
        # Remove pending assignments
        DocumentVerification.objects.filter(
            employee=instance.target_employee,
            assigned_role=instance.role,
            status="PENDING"
        ).delete()

        instance.delete()

class AllEmployeesInOrg(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        emp = get_user_employee(request.user)
        if not emp:
            return Response({"data": []}, status=200)

        employees = Employee.objects.filter(parent=emp.parent)

        return Response({
            "data": [
                {"id": e.id, "name": e.userName}
                for e in employees
            ]
        }, status=200)

class DocumentAccessRuleListCreate(ListCreateAPIView):
    serializer_class = DocumentAccessRuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        emp = get_user_employee(self.request.user)
        if not emp:
            return DocumentAccessRule.objects.none()
        return DocumentAccessRule.objects.filter(parent=emp.parent)

    @transaction.atomic
    def perform_create(self, serializer):
        emp = get_user_employee(self.request.user)

        rule = serializer.save(
            parent=emp.parent if emp else None,
            created_by=self.request.user
        )

        # ✅ Auto-assign verification
        if rule.access == "Access" and rule.specific_action == "Verify" and rule.target_employee:
            docs = Document.objects.filter(employee=rule.target_employee).first()

            if not docs:
                return

            DOCUMENT_FIELDS = {
                "profile": docs.profile,
                "aadhaar": docs.aadhar,
                "pan": docs.panCard,
                "offerLetter": docs.offerLetter,
                "pfdeclaration": docs.pfdeclaration,
                "esi": docs.esi_card,
            }

            for doc_type, file in DOCUMENT_FIELDS.items():
                if file:
                    existing = DocumentVerification.objects.filter(
                        employee=rule.target_employee,
                        document_type=doc_type,
                        assigned_role=rule.role,
                        status="PENDING"
                    ).first()

                    if not existing:
                        DocumentVerification.objects.create(
                            employee=rule.target_employee,
                            document_type=doc_type,
                            assigned_role=rule.role,
                            status="PENDING"
                        )
class SendRejectionSummary(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        employee_id = request.data.get("employee_id")
        rejected = request.data.get("rejected", [])
        if not employee_id or not rejected:
            return Response(
                {"error": "employee_id and rejected list are required"},
                status=400
            )
        send_rejection_summary_email.delay(employee_id, rejected)
        

        return Response({"message": "Rejection email sent"}, status=200)
class MyDocumentVerificationStatus(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return Response({"all_accepted": False}, status=200)

        verifications = DocumentVerification.objects.filter(employee=employee)

        if not verifications.exists():
            return Response({"all_accepted": False}, status=200)

        all_accepted = not verifications.exclude(status="ACCEPTED").exists()

        return Response({
            "all_accepted": all_accepted
        }, status=200)
class MyRoles(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        emp = Employee.objects.filter(user=request.user).first()
        if not emp:
            return Response({"data": []})

        roles = list(emp.roles.values_list("name", flat=True))
        return Response({"data": roles})

class UpdateDocumentVerification(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        verification_id = request.data.get("verification_id")
        status_value = request.data.get("status")   # ACCEPTED / REJECTED
        comment = request.data.get("comment", "")

        verification = get_object_or_404(
            DocumentVerification,
            id=verification_id
        )

        verification.status = status_value
        verification.comment = comment
        verification.save()

        # ================= 🔔 TRIGGER REJECTION ALERT =================
        if status_value == "REJECTED":
            print("🔥 DOCUMENT REJECTED → TRIGGERING NOTIFICATION")

            send_rejection_summary_email.delay(
                str(verification.employee.id),
                [
                    {
                        "document_type": verification.document_type,
                        "comment": comment
                    }
                ]
            )

        return Response(
            {"message": "Verification updated"},
            status=200
        )

class DocumentVerificationPagination(PageNumberPagination):
    page_size = 8                     # rows per page
    page_size_query_param = "page_size"
    max_page_size = 50

    def get_paginated_response(self, data):
        return Response({
            "count": self.page.paginator.count,
            "total_pages": self.page.paginator.num_pages,
            "current_page": self.page.number,
            "results": data,
        })
