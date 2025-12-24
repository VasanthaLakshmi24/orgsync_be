from rest_framework import serializers
from .models import *
from django.utils.translation import gettext as _
from django.apps import apps
from .models import DocumentVerification, DocumentAccessRule
from .models import Employee, Document


        
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username','password', 'email','roles']
        extra_kwargs = {'password': {'write_only': True}}

class QuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model=Quotes
        fields = '__all__'

class HolidaysSerializer(serializers.ModelSerializer):
    class Meta:
        model = Holidays
        fields = '__all__'

class OptionalHolidaysSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptionalHolidays
        fields = '__all__'

class EmployeeOptHolidaySerializer(serializers.ModelSerializer):
    holiday=serializers.CharField(source='holiday.name',read_only=True)
    employee=serializers.CharField(source='employee.userName',read_only=True)
    date=serializers.CharField(source='holiday.date',read_only=True)
    workDelegated=serializers.CharField(source='workDelegated.userName',read_only=True)
    class Meta:
        model=EmployeeOptHoliday
        fields = '__all__'

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    parent = serializers.CharField(source='parent.orgName', read_only=True)
    child = serializers.CharField(source='child.name', read_only=True)
    designation = serializers.CharField(source='designation.name', read_only=True)
    department = serializers.CharField(source='department.name', read_only=True)
    reported_to = serializers.CharField(source='reported_to.email', read_only=True)

    class Meta:
        model = Employee
        fields = '__all__'


class AllowanceSerializer(serializers.ModelSerializer):
    parent = serializers.CharField(source='parent.orgName', read_only=True)
    child = serializers.CharField(source='child.name', read_only=True)
    

    class Meta:
        model = Allowance
        fields = '__all__'

class ProdAllowanceSerializer(serializers.ModelSerializer):
    parent = serializers.CharField(source='parent.orgName', read_only=True)
    child = serializers.CharField(source='child.name', read_only=True)


    class Meta:
        model = ProductionAllowance
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

class EmployeeBasicDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeBasicDetails
        fields = '__all__'
class EmployeeBankDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeBankDetails
        fields = '__all__'

class ChildAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChildAccount
        fields = '__all__'

class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = '__all__'

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designation
        fields = '__all__'

class IPSerializer(serializers.ModelSerializer):
    class Meta:
        model = IPData
        fields = '__all__'

class PolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = Policy
        fields = '__all__'

class AssetsOwnedByOrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetsOwnedByOrganisation
        fields = '__all__'

class EmpRelationSetializer(serializers.ModelSerializer):
    employee = serializers.CharField(source='employee.userName', read_only=True)
    
    class Meta:
        model = EmployeeRelation
        fields = '__all__'
        
class EmpOccSetializer(serializers.ModelSerializer):
    employee = serializers.CharField(source='employee.userName', read_only=True)
    parent = serializers.CharField(source='parent.orgName', read_only=True)
    child = serializers.CharField(source='child.name', read_only=True)
    class Meta:
        model = EmployeeOccasions
        fields = '__all__'


class PfSlabsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PfSlabs
        fields = '__all__'

# class EmployeeEducationDetailsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = EmployeeEducationDetails
#         fields = '__all__'
        
class IPExceptionsSerializer(serializers.ModelSerializer):
    employee = serializers.CharField(source='employee.userName', read_only=True)
    class Meta:
        model = IPExceptions
        fields = '__all__'

class EmployeeExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeExperience
        fields = "__all__"
class AttendenceSerializer(serializers.ModelSerializer):
    employee = serializers.CharField(source='employee.userName', read_only=True)
    parent = serializers.CharField(source='parent.orgName', read_only=True)
    child = serializers.CharField(source='child.name', read_only=True)
    time_in = serializers.SerializerMethodField()
    time_out = serializers.SerializerMethodField()
    
    def get_time_in(self, obj):
        return obj.time_in.strftime("%H:%M:%S") if obj.time_in else None

    def get_time_out(self, obj):
        return obj.time_out.strftime("%H:%M:%S") if obj.time_out else None

    class Meta:
        model = Attendance
        fields = '__all__'

class BreakTimeSerializer(serializers.ModelSerializer):
    employee = serializers.CharField(source='employee.userName', read_only=True)
    parent = serializers.CharField(source='parent.orgName', read_only=True)
    child = serializers.CharField(source='child.name', read_only=True)
    time_in = serializers.SerializerMethodField()
    time_out = serializers.SerializerMethodField()
    
    def get_time_in(self, obj):
        return obj.time_in.strftime("%H:%M:%S") if obj.time_in else None

    def get_time_out(self, obj):
        return obj.time_out.strftime("%H:%M:%S") if obj.time_out else None

    class Meta:
        model = BreakTime
        fields = '__all__'
    

class LeavesSerializer(serializers.ModelSerializer):
    parent = serializers.CharField(source='parent.orgName', read_only=True)
    child = serializers.CharField(source='child.name', read_only=True)
    workDelegated = serializers.CharField(source='workDelegated.userName', read_only=True)
    approvingPerson = serializers.CharField(source='approvingPerson.email', read_only=True)
    employee = serializers.CharField(source='employee.userName', read_only=True)

    class Meta:
        model = leaves
        fields = '__all__'


class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = '__all__'



class RaiseTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = RaiseTicket
        fields = '__all__'

class LeavePolicySerializer(serializers.ModelSerializer):
    framedBy = serializers.CharField(source='framedBy.username', read_only=True)
    parent = serializers.CharField(source='parent.orgName', read_only=True)
    child = serializers.CharField(source='child.name', read_only=True)
    class Meta:
        model = LeavePolicy
        fields = '__all__'

class PayrollPolicySerializer(serializers.ModelSerializer):
    framedBy = serializers.CharField(source='framedBy.username', read_only=True)
    parent = serializers.CharField(source='parent.orgName', read_only=True)
    child = serializers.CharField(source='child.name', read_only=True)
    class Meta:
        model = PayrollPolicy
        fields = '__all__'

class OrgStructureApprovalsSerializer(serializers.ModelSerializer):
    parent = serializers.CharField(source='parent.orgName', read_only=True)
    child = serializers.CharField(source='child.name', read_only=True)
    sender = serializers.CharField(source='sender.username', read_only=True)
    receiver = serializers.CharField(source='receiver.username', read_only=True)
    
    
    class Meta:
        model = OrgStructureApprovals
        fields = '__all__'

class RoleRequestsSerializer(serializers.ModelSerializer):
    parent = serializers.CharField(source='parent.orgName', read_only=True)
    child = serializers.CharField(source='child.name', read_only=True)
    sender = serializers.CharField(source='sender.username', read_only=True)
    receiver = serializers.CharField(source='receiver.username', read_only=True)
    user = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = RoleRequests
        fields = '__all__'


        
class GrievanceCommentSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()

    class Meta:
        model = GrievanceComment
        fields = ['id', 'comment', 'sender', 'created_at']

    def get_sender(self, obj):
        if obj.grievance.is_anon and obj.sender==obj.grievance.sender:
            return "Anonymous"
        else:
            return obj.sender.username if obj.sender else None

class TicketCommentSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    class Meta:
        model =TicketComment
        fields = ['id', 'comment', 'sender', 'created_at']
    def get_sender(self, obj):
    #         return obj.sender.username 
        return obj.sender.username if obj.sender else None


class GrievanceSerializer(serializers.ModelSerializer):
    parent = serializers.CharField(source='parent.orgName', read_only=True)
    child = serializers.CharField(source='child.name', read_only=True)
    sender = serializers.SerializerMethodField()
    comments = GrievanceCommentSerializer(many=True, read_only=True)

    class Meta:
        model = Grievance
        fields = ['id', 'title', 'description', 'status', 'created_at', 'updated_at', 'is_anon', 'comments', 'sender', 'parent', 'child']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_sender(self, obj):
        if obj.is_anon:
            return "Anonymous"
        else:
            return obj.sender.username if obj.sender else None

class TicketSerializer(serializers.ModelSerializer):
    parent = serializers.CharField(source='parent.orgName', read_only=True)
    child = serializers.CharField(source='child.name', read_only=True)
    sender = serializers.SerializerMethodField()
    comments = TicketCommentSerializer(many=True, read_only=True)
    class Meta:
        model = Ticket
        fields = ['id', 'issue', 'description', 'status', 'created_at', 'updated_at', 'sender', 'parent', 'child','comments']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_sender(self, obj):
        return obj.sender.username
        
class AttendanceRequestsSerializer(serializers.ModelSerializer):
    employee = serializers.CharField(source='employee.userName', read_only=True)
    class Meta:
        model = AttendanceRequestObject
        fields = '__all__'

class CompOffRequestsSerializer(serializers.ModelSerializer):
    employee = serializers.CharField(source='employee.userName', read_only=True)
    parent = serializers.CharField(source='parent.orgName', read_only=True)
    child = serializers.CharField(source='child.name', read_only=True)
    approvedbyhr=serializers.SerializerMethodField()
    approvedbyrm=serializers.SerializerMethodField()
    class Meta:
        model = CompOffRequestObject
        fields = '__all__'
    def get_approvedbyhr(self,obj):
        return obj.approvedbyhr.username if obj.approvedbyhr else None
    def get_approvedbyrm(self,obj):
        return obj.approvedbyrm.username if obj.approvedbyrm else None
    


class AttendancePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendancePolicy
        fields = '__all__'


class AssetsSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer()
    class Meta:
        model = Assets
        fields = '__all__'

class AssetDetailsSerializer(serializers.ModelSerializer):
    asset = AssetsSerializer()
    class Meta:
        model = AssetDetails
        fields = '__all__'

class EmployeeAssetFormSerializer(serializers.ModelSerializer):
    assetdetails = AssetDetailsSerializer()
    employee = EmployeeSerializer()
    issuedBy = EmployeeSerializer()

    class Meta:
        model = EmployeeAssetForm
        fields = '__all__'

class AttendanceRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceRequestPolicy
        fields = '__all__'

class LateLoginPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = LateLoginPolicy
        fields = '__all__'

class LateLoginRequestSerializer(serializers.ModelSerializer):
    parent = serializers.CharField(source='parent.orgName', read_only=True)
    child = serializers.CharField(source='child.name', read_only=True)
    employee = serializers.CharField(source='employee.userName', read_only=True)
    reported_to = serializers.SerializerMethodField()
    comments = TicketCommentSerializer(many=True, read_only=True)
    class Meta:
        model=LateLoginRequestObject
        fields='__all__'
    def get_reported_to(self, obj):
        return obj.reported_to.userName

class Form12BBSerializer(serializers.ModelSerializer):
    class Meta:
        model = Form12BB
        fields = '__all__'

class EvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evidence
        fields = '__all__'


class MonthlyDataSerializer(serializers.ModelSerializer):
    parent = OrganizationSerializer()
    child = ChildAccountSerializer()
    
    class Meta:
        model=MonthlyData
        fields='__all__'

class LeaveApprovalFlowSerializer(serializers.ModelSerializer):
    parent = OrganizationSerializer()
    child = ChildAccountSerializer()
    
    class Meta:
        model=LeaveApprovalFlow
        fields='__all__'
        
class ResignationSerializer(serializers.ModelSerializer):
    hr = serializers.SerializerMethodField()
    rm = serializers.SerializerMethodField()
    bo = serializers.SerializerMethodField()
    employee = serializers.SerializerMethodField()

    class Meta:
        model = Resignation
        fields = "__all__"

    def get_hr(self, obj):
        return obj.hr.username if obj.hr else None

    def get_rm(self, obj):
        return obj.rm.username if obj.rm else None

    def get_bo(self, obj):
        return obj.bo.username if obj.bo else None

    def get_employee(self, obj):
        return obj.employee.userName if obj.employee else None

class BroadcastCommunicationSerializer(serializers.ModelSerializer):
    parent = OrganizationSerializer()
    child = ChildAccountSerializer()
    sender = EmployeeSerializer()
    
    class Meta:
        model=BroadcastCommunications
        fields='__all__'
        

class EmployeePayrollSerializer(serializers.ModelSerializer):
    parent = serializers.CharField(source='parent.orgName', read_only=True)
    child = serializers.CharField(source='child.name', read_only=True)
    employee = EmployeeSerializer()
    class Meta:
        model = EmployeePayroll
        fields = '__all__'  
class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'

class EmployeeEducationDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeEducationDetails
        fields = '__all__'

from rest_framework import serializers
from .models import EmployeeCertifications


class EmployeeCertificationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeCertifications
        fields = [
            'id',
            'employee',
            'name',
            'certificate_number',
            'issue_date',
            'expiry_date',
            'issuing_authority',
            'certificate_file',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'notified_30_days',
            'notified_on_expiry',
            'notified_after_expiry',
            'created_at',
            'updated_at',
        ]

        extra_kwargs = {
            'certificate_number': {'required': False, 'allow_blank': True},
            'expiry_date': {'required': False, 'allow_null': True},
            'certificate_file': {'required': False, 'allow_null': True},
        }

    def update(self, instance, validated_data):
        """
        Reset notification flags if certificate is renewed
        (expiry date or file updated)
        """

        old_expiry = instance.expiry_date
        new_expiry = validated_data.get("expiry_date", old_expiry)

        new_file = validated_data.get("certificate_file", None)

        instance = super().update(instance, validated_data)

        # 🔁 RESET FLAGS IF CERTIFICATE IS UPDATED
        if new_expiry != old_expiry or new_file is not None:
            instance.notified_30_days = False
            instance.notified_on_expiry = False
            instance.notified_after_expiry = False
            instance.save(
                update_fields=[
                    "notified_30_days",
                    "notified_on_expiry",
                    "notified_after_expiry",
                ]
            )

        return instance

# class EmployeeCertificationsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = EmployeeCertifications
#         fields = [
#             'id',
#             'employee',
#             'name',
#             'certificate_number',
#             'issue_date',
#             'expiry_date',
#             'certificate_file',
#             'created_at',
#             'updated_at',
#         ]
        # read_only_fields = [
        #     'notified_30_days',
        #     'notified_on_expiry',
        #     'notified_after_expiry',
        #     'created_at',
        #     'updated_at',
        # ]

        # # None of these are forced unless in the model
        # extra_kwargs = {
        #     'certificate_number': {'required': False, 'allow_blank': True},
        #     'expiry_date': {'required': False, 'allow_null': True},
        #     'certificate_file': {'required': False, 'allow_null': True},
        # }


class EmployeeSkillsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeSkills
        fields = [
            'id',
            'employee',
            'skill_name',
            'level',
            'years_of_experience',
            'created_at',
        ]

        extra_kwargs = {
            'level': {'required': False, 'allow_blank': True},
            'years_of_experience': {'required': False, 'allow_null': True},
        }
# serializers.py (add)

class DocumentVerificationSerializer(serializers.ModelSerializer):
    verified_by_name = serializers.SerializerMethodField()

    class Meta:
        model = DocumentVerification
        fields = [
            'id', 'employee', 'document_type', 'status', 'comment',
            'verified_by', 'verified_by_name', 'verified_at', 'assigned_role', 'created_at'
        ]
        read_only_fields = ['verified_by', 'verified_at', 'created_at', 'verified_by_name']

    def get_verified_by_name(self, obj):
        if obj.verified_by:
            return getattr(obj.verified_by, 'email', str(obj.verified_by))
        return None


class DocumentAccessRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAccessRule
        fields = [
            "id",
            "role",
            "target_employee",
            "function",
            "specific_action",
            "access",
            "created_by",
            "created_at",
        ]
        read_only_fields = ["created_by", "created_at"]
