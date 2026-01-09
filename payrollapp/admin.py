from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin
from import_export import resources 
from .models import EmployeeCertifications, EmployeeSkills
from .models import EmployeeExperience
from .models import DocumentAccessRule, DocumentVerification
from .models import BusinessUnit, Location
from .models import CLevelSeat, CLevelAssignment



class ReportResource(resources.ModelResource):
     class Meta:
         model = leaves
        

class LeavessAdmin(ImportExportModelAdmin):
     resource_class = ReportResource 


class ReportResourceAttendance(resources.ModelResource):
     class Meta:
         model = Attendance
        

class AttendancesAdmin(ImportExportModelAdmin):
     resource_class = ReportResourceAttendance

class UserAdmin(admin.ModelAdmin):
    list_display = ['username','email','roles',]

class RegAdmin(admin.ModelAdmin):
    list_display = ['fullName','email','contactNo','noOfEmployees','token','is_verified']

# class EmployeeAdmin(admin.ModelAdmin):
#     list_display = ['employeeid','userName','email','get_childs','get_roles','dateOfJoining','dateOfBirth','phoneNumber','parent','designation','department','type','reporting_manager',]
    
#     def get_childs(self, obj):
#         return " ,".join([child.name for child in obj.child.all()])
    
#     def get_roles(self, obj):
#         return ",".join([role.name+" "+ role.child.name for role in obj.roles.all()])
    
#     list_filter = ['department','designation','parent','child']
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'employeeid',
        'userName',
        'email',
        'get_childs',
        'get_roles',
        'dateOfJoining',
        'dateOfBirth',
        'phoneNumber',
        'parent',
        'designation',
        'department',
        'type',
        'reporting_manager',
    )

    search_fields = (
        'userName',
        'email',
        'employeeid',
    )

    # ❌ DO NOT put ManyToMany in list_filter
    list_filter = (
        'department',
        'designation',
        'parent',
        'type',
    )

    # ---------- CUSTOM DISPLAY METHODS ----------

    def get_childs(self, obj):
        return ", ".join(
            child.name for child in obj.child.all()
        )
    get_childs.short_description = "Child Accounts"

    def get_roles(self, obj):
        roles = []
        for role in obj.roles.all():
            if role.child:
                roles.append(f"{role.name} ({role.child.name})")
            else:
                roles.append(role.name)
        return ", ".join(roles)
    get_roles.short_description = "Roles"

class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee','parent','child','date','time_in','time_out','net_time_in','status')
    list_filter = ['date','employee','child','parent']
    date_hierarchy = 'date'

class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['orgName','regUser','contactPerson','contactNo',]
    search_fields = ('orgName', 'regUser__username')

class ChildAccountAdmin(admin.ModelAdmin):
    list_display = ['name','parent','contactPerson','contactNo','bussinessOwner','HrHead','iprestriction']

class PaymentAdmin(admin.ModelAdmin):
    list_display = ['Account','paymentId','amount','date']

class RolesDisplay(admin.ModelAdmin):
    list_display = ['name','parent','child','user']

class NotificataionDisplay(admin.ModelAdmin):
    list_display = ['sender','receiver','message','date','is_read']

class OrgStructureApprovalsDisplay(admin.ModelAdmin):
    list_display = ['sender','receiver','parent','child','roles','date','status']

class RolesApprovalDisplay(admin.ModelAdmin):
    list_display = ['role','parent','child','user','status']

class EmployeeEducationAdmin(admin.ModelAdmin):
    list_display = ['employee']
    
class EmployeePayrollAdmin(admin.ModelAdmin):
    list_display = ['employee','month','year','gross','basic_salary','net_salary','lop']
    list_filter = ('month', 'year')
    search_fields = ('employee',)

class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'data','ip_address')
    search_fields = ('user__username',  'data', 'ip_address')
    list_filter = ('timestamp',)

class CompOffAdmin(admin.ModelAdmin):
    list_display = ('employee','reason','Date','parent','child','managerstatus','hrstatus','approvedbyhr','approvedbyrm')

class LeavesAdmin(admin.ModelAdmin):
    list_display = ('employee','type','parent','child','timeStamp','fromDate','toDate','durationn','approvingPerson','status','approvedTimestamp','leavetype')
    
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('employee',)
    search_fields = ('employee__name',)

class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('employee','parent','child','month','year','bonus','advance','carry_forwarded_leave_balance','current_leave_balance','lop')
    list_filter = ['month','year','employee']

class EmployeeLeavesAdmin(admin.ModelAdmin):
    list_display = ('employee','child','leaves','parent','lop','bonus','advance',)

class MonthlyDataAdmin(admin.ModelAdmin):
    list_display = ('parent','child','year','month','no_of_working_days')

class BreakTimeAdmin(admin.ModelAdmin):
    list_display = ('employee','child','parent','date','reason','time_in','time_out','net_time_in')
    list_filter = ('date','employee','child')
    date_hierarchy = 'date'

class EmployeeBasicDetailsAdmin(admin.ModelAdmin):
    list_display = ('employee', 'firstName', 'lastName', 'contactNumber', 'emergencyContactNumber', 'aadharNumber', 'panCardNumber')
    search_fields = ('firstName', 'lastName', 'contactNumber', 'emergencyContactNumber', 'aadharNumber', 'panCardNumber')
    list_filter = ('employee',)
    readonly_fields = ('is_editable',)

class EmployeeBankDetailsAdmin(admin.ModelAdmin):
    list_display = ('employee', 'bankName', 'bankAcNo')
    search_fields = ('bankName', 'bankAcNo')

class EmployeeRelationAdmin(admin.ModelAdmin):
    list_display = ('employee', 'relationName', 'relationType')
    search_fields = ('relationName', 'relationType')
    readonly_fields = ('is_editable',)



class EmployeeReferenceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'Organization_name', 'Designation', 'Department_name', 'Contact_no')
    search_fields = ('Organization_name', 'Designation', 'Department_name', 'Contact_no')
    readonly_fields = ('is_editable',)

class EmployeeOccasionsAdmin(admin.ModelAdmin):
    list_display = ('parent', 'child', 'employee', 'type', 'date')
    list_filter = ('type', 'date')
    search_fields = ('employee__firstName', 'employee__lastName')
    raw_id_fields = ('parent', 'child', 'employee')
    date_hierarchy = 'date'
class EmployeeEducationDetailsAdmin(admin.ModelAdmin):
    list_display = ('employee', 'institution', 'degree', 'field_of_study', 'start_date', 'end_date')
    search_fields = ('institution', 'degree', 'field_of_study')
    readonly_fields = ('is_editable',)

class HolidayAdmin(admin.ModelAdmin):
    list_display = ('parent', 'child','name', 'date')
    list_filter = ('name', 'date')
    search_fields = ('name',)
    raw_id_fields = ('parent', 'child')
    date_hierarchy = 'date'
class EmployeeEducationAdmin(admin.ModelAdmin):
    list_display = ['employee']
class EmployeeExperienceAdmin(admin.ModelAdmin):
    list_display = (
        'employee', 
        'organization', 
        'designation', 
        'department',
        'worked_from', 
        'worked_to', 
        'reason_for_resign',
        'previous_positions', 
        'promotions', 
        'transfers', 
        'role_changes',
        'relieving_letter',
        'payslip_1',
        'payslip_2',
        'payslip_3',
    )
    search_fields = (
        'organization', 
        'designation', 
        'department', 
        'reason_for_resign',
        'previous_positions',
    )
    readonly_fields = ('is_editable',)
# Register all models
admin.site.register(AttendanceRequestObject)
admin.site.register(AttendanceRequestPolicy)
admin.site.register(AttendancePolicy)
admin.site.register(CompOffRequestObject, CompOffAdmin)
admin.site.register(ActivityLog, ActivityLogAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Accounts, RegAdmin)
admin.site.register(OptionalHolidays)
admin.site.register(ChildAccount, ChildAccountAdmin)
admin.site.register(Roles, RolesDisplay)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Notification, NotificataionDisplay)
admin.site.register(OrgStructureApprovals, OrgStructureApprovalsDisplay)
admin.site.register(RoleRequests , RolesApprovalDisplay)
admin.site.register(User, UserAdmin)
admin.site.register(BreakTime, BreakTimeAdmin)
# admin.site.register(Employee, EmployeeAdmin)
admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(leaves, LeavesAdmin)
admin.site.register(LateLoginRequestObject)
admin.site.register(Holidays, HolidayAdmin)
admin.site.register(LateLoginPolicy)
admin.site.register(EmployeeOptHoliday)
admin.site.register(EmployeePay)
admin.site.register(ProdEmployeePay)
admin.site.register(Form12BB)
admin.site.register(Evidence)
admin.site.register(Allowance)
admin.site.register(PayrollAllowance)
admin.site.register(EmployeeAllowance)
admin.site.register(EmployeeProdAllowance)
admin.site.register(ProductionAllowance)
admin.site.register(Conversation)
admin.site.register(Participant)
admin.site.register(Message)
admin.site.register(Resignation)
admin.site.register(LeaveApprovalFlow)
admin.site.register(BroadcastCommunications)
admin.site.register(MonthlyData, MonthlyDataAdmin)
# admin.site.register(Department)
# admin.site.register(Designation)
admin.site.register(LeaveBalance, LeaveBalanceAdmin)
admin.site.register(LeavePolicy)
admin.site.register(Quotes)
admin.site.register(EmployeeBasicDetails, EmployeeBasicDetailsAdmin)
admin.site.register(EmployeeBankDetails, EmployeeBankDetailsAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(EmployeeRelation, EmployeeRelationAdmin)
admin.site.register(EmployeeEducationDetails, EmployeeEducationDetailsAdmin)
admin.site.register(EmployeeExperience, EmployeeExperienceAdmin)
admin.site.register(EmployeeReference, EmployeeReferenceAdmin)
admin.site.register(GrievanceComment)
admin.site.register(Grievance)
admin.site.register(TicketComment)
admin.site.register(Ticket)
admin.site.register(EmployeeLeaves, EmployeeLeavesAdmin)
admin.site.register(PayrollPolicy)
admin.site.register(EmployeePayroll, EmployeePayrollAdmin)
admin.site.register(IPData)
admin.site.register(IPAddr)
admin.site.register(EmployeeOccasions, EmployeeOccasionsAdmin)



@admin.register(EmployeeCertifications)
class EmployeeCertificationsAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'name',
        'certificate_number',
        'issue_date',
        'expiry_date',
        'issuing_authority',
        'created_at'
    )

    search_fields = ('name', 'certificate_number', 'issuing_authority')
    list_filter = ('issue_date', 'expiry_date')

    readonly_fields = ('created_at', 'updated_at')   # ONLY fields that exist


@admin.register(EmployeeSkills)
class EmployeeSkillsAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'skill_name',
        'level',
        'years_of_experience',
        'created_at'
    )

    search_fields = ('skill_name',)
    list_filter = ('level',)

    readonly_fields = ('created_at',)  # VALID as per your model


# Admin for Document Verification records
# ---------------- Document Management Admin ----------------

# Admin for Document Access Rules
@admin.register(DocumentAccessRule)
class DocumentAccessRuleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "role",
        "target_employee",
        "function",
        "specific_action",
        "access",
        "created_by",
        "created_at",
    )
    list_filter = ("role", "access", "created_at")
    search_fields = (
        "role",
        "target_employee__userName",
        "function",
        "specific_action",
        "created_by__username",
    )
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # optimize FK lookups
        return qs.select_related("target_employee", "created_by")


# Admin for Document Verification
@admin.register(DocumentVerification)
class DocumentVerificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "employee",
        "document_type",
        "status",
        "comment",
        "verified_by",
        "verified_at",
        "assigned_role",
    )
    list_filter = ("status", "document_type", "verified_at")
    search_fields = (
        "employee__userName",
        "document_type",
        "verified_by__username",
        "comment",
        "assigned_role",
    )
    readonly_fields = ("verified_at", "created_at")
    ordering = ("-created_at",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # optimize FK lookups
        return qs.select_related("employee", "verified_by")
@admin.register(BusinessUnit)
class BusinessUnitAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "profit_center_code",
        "parent",
        "is_active",
        "created_at",
        "updated_at",
    )

    list_filter = ("is_active", "parent")
    search_fields = ("name", "profit_center_code")
    ordering = ("-created_at",)

    readonly_fields = ("created_at", "updated_at")
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
       "timezone_name",      
       "capacity",
        "parent",
        "is_active",
    )

    list_filter = ("is_active", "parent")
    search_fields = ("name", "address")

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = (
        "department_code",
        "name",
        "organization",
        "business_unit",
        "parent_department",
        "reports_to_clevel",
        "is_active",
        "created_at",
    )
    list_filter = (
        "organization",
        "business_unit",
        "reports_to_clevel",
        "is_active",
    )
    search_fields = (
        "department_code",
        "name",
    )
    ordering = ("name",)
    list_per_page = 25

    readonly_fields = (
    "department_code",
    "id",
    "created_at",
    "updated_at",
)

    fieldsets = (
        ("Basic Information", {
            "fields": ("department_code", "name", "description")
        }),
        ("Organization Mapping", {
            "fields": ("organization", "business_unit")
        }),
        ("Hierarchy (Optional)", {
            "fields": ("parent_department",)
        }),
        ("C-Level Control", {                
        "fields": ("reports_to_clevel",),
        "description": "Assign which C-Level seat controls this department"
    }),
        ("Status", {
            "fields": ("is_active",)
        }),
        ("Audit Information", {
            "fields": ("id", "created_at", "updated_at")
        }),
    )
@admin.register(CLevelSeat)
class CLevelSeatAdmin(admin.ModelAdmin):
    list_display = (
        "seat_code",
        "parent",
        "cxo_code",
        "title",
        "is_filled",
        "is_active"
    )
    readonly_fields = ("seat_code",)
    search_fields = ("seat_code", "cxo_code", "parent__orgName")
    list_filter = ("cxo_code", "is_filled", "is_active")
@admin.register(CLevelAssignment)
class CLevelAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "c_level_seat",
        "employee",
        "is_current",
        "start_date",
    )
    list_filter = ("is_current",)
# payrollapp/admin.py
@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    # ===================== LIST VIEW =====================
    list_display = (
        "name",
        "job_family",
        "level",
        "band",
        "parent",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "job_family",
        "level",
        "parent",
    )

    search_fields = (
        "name",
        "band",
        "job_family",
        "level",
    )

    ordering = ("name",)

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    # ===================== ACTIONS =====================
    actions = ["disable_designations"]

    def disable_designations(self, request, queryset):
        queryset.update(is_active=False)

    disable_designations.short_description = "Disable selected designations"

    # ===================== PERMISSIONS =====================
    def _allowed(self, request):
        user = request.user

        if not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        if not hasattr(user, "employee"):
            return False

        return user.employee.role in ["HR_HEAD", "BUSINESS_OWNER"]

    def has_module_permission(self, request):
        return self._allowed(request)

    def has_view_permission(self, request, obj=None):
        return self._allowed(request)

    def has_add_permission(self, request):
        return self._allowed(request)

    def has_change_permission(self, request, obj=None):
        return self._allowed(request)

    def has_delete_permission(self, request, obj=None):
        return False
