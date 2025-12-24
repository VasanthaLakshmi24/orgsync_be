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
from datetime import datetime,timedelta
import csv
from django.db import transaction
from django.db.models import Sum
from django.db.models import Q
from django.contrib.auth import get_user_model

User = get_user_model()

def mark_attendance_as_leave(leave_obj):
    employee = leave_obj.employee
    child = employee.main_child
    from_date = leave_obj.fromDate
    to_date = datetime.now().date() 

    try:
        attendance_policy = AttendancePolicy.objects.get(parent=child.parent, child=child)
        working_days = attendance_policy.get_workingDays() 
    except AttendancePolicy.DoesNotExist:
        working_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    holidays_in_range = Holidays.objects.filter(
        parent=child.parent,
        child=child,
        date__range=(from_date, to_date)
    ).values_list('date', flat=True)

    current_date = from_date
    working_dates = []

    while current_date <= to_date:
        if current_date.strftime('%A') in working_days and current_date not in holidays_in_range:
            working_dates.append(current_date)
        current_date += timedelta(days=1)

    attendance_records = Attendance.objects.filter(
        Q(employee=employee),
        Q(date__in=working_dates),
        Q(status='absent') | Q(status__isnull=True)
    )

    if attendance_records.exists():
        attendance_records.update(status='leave')

class Leave(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, **kwargs):
        user = request.user
        empobj = Employee.objects.get(user=user)
        leavepolicy = LeavePolicy.objects.get(child=empobj.main_child,parent = empobj.parent)
        leaveobjs = leaves.objects.filter(employee = empobj).order_by('-timeStamp')
        serializer = LeavesSerializer(leaveobjs, many=True)
        month = datetime.today().month
        year = datetime.today().year

        annual_leaves = leaveobjs.filter(status="approved", type="annual", timeStamp__month=month, timeStamp__year=year).aggregate(Sum('durationn'))['durationn__sum'] or 0
        sick_leaves = leaveobjs.filter(status="approved", type="sick", timeStamp__month=month, timeStamp__year=year).aggregate(Sum('durationn'))['durationn__sum'] or 0
        personal_leaves = leaveobjs.filter(status="approved", type="personal", timeStamp__month=month, timeStamp__year=year).aggregate(Sum('durationn'))['durationn__sum'] or 0
        comoff_leaves = leaveobjs.filter(status="approved", type="com_off", timeStamp__month=month, timeStamp__year=year).aggregate(Sum('durationn'))['durationn__sum'] or 0
        total_leaves = leaveobjs.filter(timeStamp__month=month, timeStamp__year=year)

        annual_leaves_year = leaveobjs.filter(status="approved", type="annual", timeStamp__year=year).aggregate(Sum('durationn'))['durationn__sum'] or 0
        sick_leaves_year = leaveobjs.filter(status="approved", type="sick", timeStamp__year=year).aggregate(Sum('durationn'))['durationn__sum'] or 0
        personal_leaves_year = leaveobjs.filter(status="approved", type="personal", timeStamp__year=year).aggregate(Sum('durationn'))['durationn__sum'] or 0
        comoff_leaves_year = leaveobjs.filter(status="approved", type="com_off", timeStamp__year=year).aggregate(Sum('durationn'))['durationn__sum'] or 0
        total_leaves_year = leaveobjs.filter(timeStamp__year=year)


        accepted_leaves_year = total_leaves_year.filter(status="approved");
        rejected_leaves_year = total_leaves_year.filter(status="rejected");
        pending_leaves_year = total_leaves_year.filter(status="pending");
        
        
        accepted_leaves = total_leaves.filter(status="approved");
        pending_leaves = total_leaves.filter(status="pending");
        rejected_leaves = total_leaves.filter(status="rejected");

        sickLeaves = leavepolicy.sickLeaves
        casualLeaves = leavepolicy.casualLeaves
        leaves_per_year = leavepolicy.leaves_per_year

        leavebal = LeaveBalance.objects.filter(employee=empobj).latest('year', 'month').current_leave_balance
        lvs = leaveobjs.filter(employee=empobj).order_by('timeStamp')
        last_leave = lvs[0].status if lvs else None
        metrics = {
            "total_leaves": len(total_leaves),
            "annual_leaves" : (annual_leaves),
            "sick_leaves" : (sick_leaves),
            "personal_leaves" : (personal_leaves),
            "comoff_leaves" : (comoff_leaves),
            "total_leaves_year": len(total_leaves_year),
            "annual_leaves_year" : (annual_leaves_year),
            "sick_leaves_year" : (sick_leaves_year),
            "personal_leaves_year" : (personal_leaves_year),
            "comoff_leaves_year" : (comoff_leaves_year),
            "allowed_sick" : sickLeaves,
            "allowed_casual" : casualLeaves,
            "allowed_leaves" : leaves_per_year,
            "leavebal":leavebal,
            "accepted_leaves" :len(accepted_leaves),
            "rejected_leaves" : len(rejected_leaves),
            "accepted_leaves_year" :len(accepted_leaves_year),
            "rejected_leaves_year" : len(rejected_leaves_year),
            "pending_leaves_year" : len(pending_leaves_year),
            "pending_leaves" : len(pending_leaves),
            "last_leave" : last_leave
        }

        return Response({'data': serializer.data,'metrics':metrics}, status=status.HTTP_200_OK)

    def post(self, request, **kwargs):
        user = request.user
        empobj = Employee.objects.get(user=user)
        parent = empobj.parent
        child = empobj.main_child

        f = request.data.get('fromDate')
        f_object = datetime.strptime(f, "%Y-%m-%d")
        fromDate = f_object.date()

        t = request.data.get('toDate')
        t_object = datetime.strptime(t, "%Y-%m-%d")
        toDate = t_object.date()

        timeStamp = request.data.get('timeStamp')
        ltype = request.data.get('type')
        leavetype = request.data.get('leavetype')

        workDelegatedId = request.data.get('workDelegated')
        workDelegated = None
        if workDelegatedId:
            try:
                workDelegated = Employee.objects.get(id=workDelegatedId)
            except Employee.DoesNotExist:
                workDelegated = None
        else:
            workDelegated = None
        comments = request.data.get('comments')
        reason = request.data.get('reason')

        try:
            attendance_policy = AttendancePolicy.objects.get(parent=child.parent, child=child)
            working_days = attendance_policy.get_workingDays()
        except AttendancePolicy.DoesNotExist:
            working_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

        holidays_in_range = Holidays.objects.filter(
            parent=child.parent,
            child=child,
            date__range=(fromDate, toDate)
        ).values_list('date', flat=True)

        current_date = fromDate
        duration = 0
        while current_date <= toDate:
            if current_date not in holidays_in_range and current_date.strftime('%A') in working_days:
                duration += 1
            current_date += timedelta(days=1)

        # Get the forwarding policy
        leaveforwardingpolicy_qs = LeaveApprovalFlow.objects.filter(parent=parent, child=child, days__lte=duration).order_by('-days')

        # initialize defaults to avoid UnboundLocalError
        approvingPerson = None
        level = 1
        leaveforwardingpolicy = None

        if leaveforwardingpolicy_qs.exists():
            leaveforwardingpolicy = leaveforwardingpolicy_qs.first()
            level = getattr(leaveforwardingpolicy, 'level', 1)

        # helper to normalize approver to a User instance
        def normalize_to_user(obj):
            if obj is None:
                return None
            if isinstance(obj, User):
                return obj
            if isinstance(obj, Employee):
                return getattr(obj, 'user', None)
            # if it's an id or other, try to fetch User
            try:
                return User.objects.get(id=obj)
            except Exception:
                return None

        # 1) If no forwarding policy -> prefer child's HR head
        if not leaveforwardingpolicy:
            hr = getattr(child, 'HrHead', None)
            approvingPerson = normalize_to_user(hr) if hr else None

        # 2) If policy explicitly requires HR approval
        elif getattr(leaveforwardingpolicy, 'approvingPerson', None) == 'HR':
            hr = getattr(child, 'HrHead', None)
            approvingPerson = normalize_to_user(hr) if hr else None

        # 3) Else follow reporting chain
        if not approvingPerson:
            reported_to_obj = getattr(empobj, 'reported_to', None)
            if reported_to_obj:
                approvingPerson = normalize_to_user(reported_to_obj)

                # Walk up 'level' times, stop if SUPER_USER or no further report
                for i in range(level):
                    if not approvingPerson:
                        break
                    # If this user has SUPER_USER role, stop walking
                    try:
                        roles_callable = getattr(approvingPerson, 'get_roles', None)
                        roles = roles_callable() if callable(roles_callable) else []
                    except Exception:
                        roles = []
                    if 'SUPER_USER' in roles:
                        break

                    # try to get the employee record for current approver and step up
                    try:
                        appobj = Employee.objects.get(user=approvingPerson)
                    except Employee.DoesNotExist:
                        break
                    if getattr(appobj, 'reported_to', None):
                        approvingPerson = normalize_to_user(appobj.reported_to)
                    else:
                        break

        # 4) fallback: try to find a SUPER_USER under parent
        if not approvingPerson:
            try:
                super_emp = Employee.objects.filter(parent=parent).select_related('user').first()
                if super_emp:
                    candidate_user = getattr(super_emp, 'user', None)
                    try:
                        roles_callable = getattr(candidate_user, 'get_roles', None)
                        roles = roles_callable() if callable(roles_callable) else []
                    except Exception:
                        roles = []
                    if 'SUPER_USER' in roles:
                        approvingPerson = candidate_user
            except Exception:
                approvingPerson = None

        # final guard: if still no approver found, return a helpful error
        if not approvingPerson:
            return Response({'error': 'No approving person found for this leave. Please contact HR/admin.'}, status=status.HTTP_400_BAD_REQUEST)

        # create the leave now that approvingPerson is set
        leaveobj = leaves.objects.create(
            parent = parent,
            leavetype = leavetype,
            child = child,
            reason = reason,
            employee = empobj,
            fromDate = fromDate,
            toDate = toDate,
            timeStamp = timeStamp,
            type = ltype,
            workDelegated = workDelegated,
            comments = comments,
            durationn = duration,
            approvingPerson = approvingPerson
        )

        if leaveobj:
            # Ensure approvingPerson has username/email attributes safely
            approver_username = getattr(approvingPerson, 'username', 'Approver')
            approver_email = getattr(approvingPerson, 'email', None)

            empmessage = (
                f"Dear {empobj.userName},\n"
                f"We would like to inform you about your recent leave request. "
                f"Your leave from {fromDate} to {toDate} has been sent to {approver_username}.\n"
                "If you have any questions or need further assistance regarding your leave request, please feel free to contact our HR department.\n"
                "Thank you for your attention.\nBest regards,\nGA Org Sync"
            )

            apmsg = (
                f"Dear {approver_username},\n"
                f" We are writing to inform you that {empobj.userName} has requested leave from {fromDate} to {toDate}. "
                "Please review and process this request at your earliest convenience.\n\n"
                "Thank you for your attention.\nBest regards,\nGA Org Sync"
            )

            try:
                Notification.objects.create(sender=user, receiver=approvingPerson, message=apmsg)
            except Exception:
                # Receiver might be a User or Employee object; try alternative forms if required
                try:
                    Notification.objects.create(sender=user, receiver=empobj, message=apmsg)
                except Exception:
                    pass

            try:
                sendemail('Leave Request', empmessage, [user.email])
            except Exception:
                pass

            if approver_email:
                try:
                    sendemail('Leave Request', apmsg, [approver_email])
                except Exception:
                    pass

            return Response({'message': 'Leave request sent successfully.'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'Leave request failed.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, **kwargs):
        user = request.user
        try:
            emp_obj = Employee.objects.get(user=user)
        except Employee.DoesNotExist:
            emp_obj = None

        leave_id = request.data.get('leave_id')
        stat = request.data.get('status')
        cancellation_date = request.data.get('cancellationDate')
        reason = None

        if stat in ["rejected", "cancelled"]:
            reason = request.data.get('reason')
            if not reason:
                return Response({'error': 'Please provide a reason.'}, status=status.HTTP_400_BAD_REQUEST)
        
            if cancellation_date:
                try:
                    cancellation_date = datetime.strptime(cancellation_date, '%Y-%m-%d').date()
                except ValueError:
                    return Response({'error': 'Invalid cancellation date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': 'Cancellation date is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        approvedTimestamp = datetime.now()
        
        try:
            lp = leaves.objects.get(id=leave_id)
            original_from_date = lp.fromDate
            original_to_date = lp.toDate

            if stat == "cancelled" and original_from_date <= cancellation_date <= original_to_date:
                if cancellation_date > original_from_date:
                    lp.toDate = cancellation_date
                    lp.save()

                    leaves.objects.create(
                        employee=lp.employee,
                        parent = lp.parent,
                        child=lp.child,
                        fromDate=cancellation_date + timedelta(days=1),
                        toDate=original_to_date,
                        status="cancelled",
                        reason=reason,
                        approvedTimestamp=approvedTimestamp
                    )
                else:
                    lp.status = stat
                    lp.approvedTimestamp = approvedTimestamp
                    lp.reason = reason
                    lp.save()
            else:
                lp.status = stat
                lp.approvedTimestamp = approvedTimestamp
                lp.reason = reason
                lp.save()
            
            if lp.fromDate < timezone.now().date():
                mark_attendance_as_leave(lp)

            if emp_obj == lp.employee and stat == "cancelled":
                message = (f"Dear {lp.approvingPerson.username},\nWe would like to inform you that the employee "
                        f"{lp.employee.userName} has cancelled the leave from {original_from_date} to {original_to_date} "
                        f"with reason {reason}.\nThank you for your attention.\nBest regards,\nGA Org Sync")
                sendemail(
                    'Leave Status',
                    message,
                    [lp.approvingPerson.email],
                )
                
                return Response({"message": "Leave status updated successfully."}, status=status.HTTP_201_CREATED)

            if stat in ["rejected", "cancelled"]:
                message = (f"Dear {lp.employee.userName},\nWe would like to inform you about the status of your recent "
                        f"leave request. Your leave from {original_from_date} to {original_to_date} has been {lp.status} "
                        f"by {user.username} with reason {reason}.\nIf you have any questions or need further assistance "
                        f"regarding your leave request, please feel free to contact our HR department.\nThank you for your attention.\n"
                        "Best regards,\nGA Org Sync")
            else:
                message = (f"Dear {lp.employee.userName},\nWe would like to inform you about the status of your recent "
                        f"leave request. Your leave from {original_from_date} to {original_to_date} has been {lp.status} "
                        f"by {user.username}.\nIf you have any questions or need further assistance regarding your leave request, "
                        f"please feel free to contact our HR department.\nThank you for your attention.\nBest regards,\nGA Org Sync")
            
            try:
                Notification.objects.create(sender=user, receiver=lp.approvingPerson, message=message)
                sendemail(
                    'Leave Status',
                    message,
                    [lp.employee.email],
                )
            except Exception as e:
                pass

            return Response({"message": "Leave status updated successfully."}, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(e)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class fetchLeaveApprovals(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, **kwargs):
        user = request.user
        my_serializer = None
        leaveobjs = leaves.objects.filter(approvingPerson = user).order_by('-timeStamp')
        serializer = LeavesSerializer(leaveobjs, many=True)
        if "SUPER_USER" not in user.get_roles():
            empobj = Employee.objects.get(user=user)
            my_leaveobjs = leaves.objects.filter(employee = empobj).order_by('-timeStamp')
            my_serializer = LeavesSerializer(my_leaveobjs, many=True)
            return Response({'data': serializer.data,'my_data':my_serializer.data}, status=status.HTTP_200_OK)
        return Response({'data': serializer.data,'my_data':[]}, status=status.HTTP_200_OK)


def leavesPerMonth(employee,month,year,child):
    month=int(month)
    year=int(year)
    startdate=datetime(year,month,1)
    parent=employee.parent
    child=child
    workingdays=MonthlyData.objects.get(parent=parent,child=child,month=month,year=year).no_of_working_days
    enddate=get_last_date_of_month(year,month)
    attendance=Attendance.objects.filter(employee=employee,logged_in = True,date__gte=startdate,date__lte=enddate).values('date').distinct()
    num_days_worked=attendance.count()
    val=int(num_days_worked)
    return workingdays-num_days_worked

class fetchLeaveBal(APIView):
    def get(self,request):
        user=request.user 
        employee=Employee.objects.get(user=user)
        leavebal=LeaveBalance.objects.get(employee=employee).leave_balance
        return Response({'leavebal':leavebal},status=status.HTTP_200_OK)

def get_employee_leaves(employee, month, year):
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    leaves_in_month = leaves.objects.filter(
        employee=employee,
        fromDate__lte=end_date, toDate__gte=start_date,status='approved'
    )
    return leaves_in_month




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



class uploadLeaveBalance(APIView):
    permission_classes = [IsAuthenticated]
    @transaction.atomic
    def post(self,request,**kwargs):
        user = request.user
        childid=request.data['childid']
        child = ChildAccount.objects.get(id = childid)
        parent=Employee.objects.get(user=user).parent
        file = request.FILES.get('file')
        parentid=parent.id
        if not file:
            return Response({"error": "No file provided in the request"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with file.open() as file:
                name_sheet_file = file.read().decode('utf-8')
                csv_reader = csv.reader(name_sheet_file.splitlines())
                next(csv_reader)
                for row in csv_reader:
                    employeeid,leavebal = row
                    try :
                        emp = Employee.objects.get(employeeid = employeeid)
                        try:
                            lbal=LeaveBalance.objects.get(employee = emp, parent = parent, child=child)
                            lbal.leave_balance=leavebal
                            lbal.save()
                        except:
                            LeaveBalance.objects.create(employee = emp, parent = parent, child=child,leave_balance=leavebal)
                    except Exception as e:
                        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
                return Response({"message": "Uploaded Leave Balance  successfully"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
