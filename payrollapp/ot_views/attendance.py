from datetime import datetime,timedelta
from rest_framework import status
from ..models import *
from ..decorators import *
from ..serializers import *
from ..tasks import *
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from ..utils import *
from django.shortcuts import get_object_or_404
import csv




def gde(request):
    childs = ChildAccount.objects.exclude(name='Kritsnam')
    employees = Employee.objects.filter(main_child__in=childs)
    start_date = '2024-07-01'
    end_date = '2024-07-31'
    
    data = []
    
    for employee in employees:#Loop through each employee
        att_leaves = Attendance.objects.filter(employee=employee, date__range=[start_date, end_date], status='leave')#Count leaves
        
        att_absent = Attendance.objects.filter(employee=employee, date__range=[start_date, end_date], status='absent')
        
        e_data = {
            'employee': employee.userName,
            'leaves': att_leaves.count(),
            'absent': att_absent.count()
        }#Prepare a small dictionary for every employee
        
        data.append(e_data)#Add this employee’s summary into data list
    
    return render(request, 'gt.html', {'data': data})#Return a webpage

class AttendanceSummaryView(APIView):
    def get(self, request):
        user = request.user
        employee = Employee.objects.get(user=user)
        today = datetime.today().date()
        first_day_of_current_month = today.replace(day=1)

        summary = {
            'month_1': {
                'present': 0,
                'latelogin': 0,
                'halfday': 0,
                'absent': 0,
                'leave': 0,
                'holiday': 0
            },
            'month_2': {
                'present': 0,
                'latelogin': 0,
                'halfday': 0,
                'absent': 0,
                'leave': 0,
                'holiday': 0
            },
            'month_3': {
                'present': 0,
                'latelogin': 0,
                'halfday': 0,
                'absent': 0,
                'leave': 0,
                'holiday': 0
            }
        }

        for i in range(1,4):
            start_date = (first_day_of_current_month - timedelta(days=1)).replace(day=1)
            end_date = first_day_of_current_month - timedelta(days=1)
            first_day_of_current_month = start_date

            attendance_records = Attendance.objects.filter(
                employee=employee,
                date__range=[start_date, end_date]
            )#Fetch attendance for that month

            month_key = f'month_{i}'#Select which month to store results in
            summary[month_key]['present'] = attendance_records.filter(status='present').count()#counts specific attendance type status in db
            summary[month_key]['absent'] = attendance_records.filter(status='absent').count()
            summary[month_key]['latelogin'] = attendance_records.filter(status='latelogin').count()
            summary[month_key]['halfday'] = attendance_records.filter(status='halfday').count()
            summary[month_key]['leave'] = attendance_records.filter(status='leave').count()
            summary[month_key]['holiday'] = attendance_records.filter(status='holiday').count()

        return Response(summary, status=status.HTTP_200_OK)#Return JSON response

class FetchAttendanceRecords(APIView):
    def post(self,request):
        user=request.user
        childid=request.data['childid']
        child=ChildAccount.objects.get(id=childid)#Fetch ChildAccount
        if child.HrHead==user:# Check if logged-in user is HR Head
            empid=request.data['empid']
            month=request.data['month']
            year=request.data['year']
            employee=Employee.objects.get(id=empid)
            attendancerecords=Attendance.objects.filter(employee=employee,date__month=month,date__year=year).order_by('date')
            serializer=AttendenceSerializer(attendancerecords,many=True).data
            return  Response({'data':serializer}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'You are not authorized to view this record'}, status=status.HTTP_403_FORBIDDEN)

class UpdateAttendanceRecord(APIView):#HR Head can manually update attendance of any employee.
    def post(self,request):
        user=request.user
        childid=request.data['childid']
        child=ChildAccount.objects.get(id=childid)
        if child.HrHead==user:
            id=request.data['id']
            statusvalue=request.data['status']
            time_in=request.data['time_in']
            time_out=request.data['time_out']
            time_format = "%H:%M"
            if time_in:
                time_in = datetime.strptime(time_in, time_format).time()
            else:
                time_in = None
            if time_out:
                time_out = datetime.strptime(time_out, time_format).time()
            else:
                time_out = None
            attendancerecord=Attendance.objects.get(id=id)#Fetch attendance record
            attendancerecord.status=statusvalue
            attendancerecord.time_in=time_in
            attendancerecord.time_out=time_out
            attendancerecord.save()
            if time_in and time_out:#Recalculate net working hours (if both times exist)
                fhours,fminutes =map(int,subtract_times(time_out,time_in).split(':'))
                net = f"{fhours}:{fminutes}"
            else:
                net = "0:0"    
            attendancerecord.net_time_in=net
            attendancerecord.save()
            return Response({'success': 'Attendance record updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'You are not authorized to update this record'}, status=status.HTTP_403_FORBIDDEN)


class IPDetails(APIView):#who is requesting.
    def post(self, request):
        user = request.user
        childid = request.data.get('childid')

        try:
            child = ChildAccount.objects.get(id=childid)
            ip_data = IPData.objects.filter(child=child, parent=child.parent).first()
            ip_addresses = ip_data.get_ipaddresses().values('name', 'address')#Get the actual IP address list
            return Response({'data': list(ip_addresses)}, status=status.HTTP_200_OK)
        except ChildAccount.DoesNotExist:
            return Response({'error': 'Child account not found'}, status=status.HTTP_404_NOT_FOUND)
        except IPData.DoesNotExist:
            return Response({'data': []}, status=status.HTTP_200_OK)

class AddIPDetails(APIView):
    def post(self, request):
        user = request.user
        childid = request.data.get('childid')
        ipaddr = request.data.get('ip')
        name = request.data.get('name')

        if not ipaddr or not name:
            return Response({'error': 'IP address and name are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            child = ChildAccount.objects.get(id=childid)
        except ChildAccount.DoesNotExist:
            return Response({'error': 'Child account not found'}, status=status.HTTP_404_NOT_FOUND)

        ip_data, created = IPData.objects.get_or_create(child=child, parent=child.parent)
        
        if not IPAddr.objects.filter(address=ipaddr, name=name, ip_data=ip_data).exists():#Check duplicate IP entry
            ip_address_obj, _ = IPAddr.objects.get_or_create(address=ipaddr, name=name)

            ip_data.ipaddresses.add(ip_address_obj)
            ip_data.save()
            return Response({'message': "IP added successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({'message': "IP address with this name already exists"}, status=status.HTTP_200_OK)

def calculate_attendance(employee):
    print("calc_att entered")
    today =  datetime.now().date()
    brobj = BreakTime.objects.filter(date=today,employee=employee)#brobj is a list of all breaks (break-in & break-out pairs) for this employee.
    attobj=Attendance.objects.get(employee=employee,date=datetime.now().date())
    attpolicy = AttendancePolicy.objects.get(parent=employee.parent,child=employee.main_child)#working hours rules
    half_day_time = attpolicy.min_working_for_full_day
    total_hours = 0
    total_minutes = 0
    fhours,fminutes =map(int,subtract_times(attobj.time_out,attobj.time_in).split(':'))#Calculate total punch-in → punch-out duration
    
    
    net = f"{fhours}:{fminutes}"
    attobj.net_break = "0:0"
    if len(brobj)>0:
        for i in brobj:#Adds all break hours + break minutes.
            hours, minutes = map(int, i.net_time_in.split(':'))
            total_hours += hours
            print(total_hours,hours,i)
            total_minutes += minutes
        total_hours += total_minutes // 60#Convert extra minutes into hours
        total_minutes %= 60
        fhours=fhours-total_hours
        if fminutes>=total_minutes:#Subtract break minutes from total work minutes
            fminutes=fminutes-total_minutes
        else:
            fhours=fhours-1
            fminutes+=60
            fminutes=fminutes-total_minutes
        time1 = str(fhours)+':'+str(fminutes) 
        time2 = str(total_hours)+':'+str(total_minutes) 
        attobj.net_break = time2
        time1 = datetime.strptime(time1, '%H:%M')
        time2 = datetime.strptime(time2, '%H:%M')
        time_difference = time1 - time2
        hours = time_difference.seconds // 3600
        minutes = (time_difference.seconds % 3600) // 60
        net=f"{fhours}:{fminutes}"
    if fhours+(fminutes/60) < half_day_time:
        attobj.status = "halfday"
        message = f'Dear {employee.userName},\n We are please to inform you that on {today} your attendance is marked as half day as your net work time ({fhours+(fminutes/60)}) is less than {half_day_time}'#Send email notification
        sendemail(
            'Attendance Status',
            message,
            [employee.email],
        )
        #Save final calculated working hours
    attobj.net_time_in =net
    attobj.save()

class CheckTimeOut(APIView):
    def get(self,request):
        try:
            user = request.user
            employee=Employee.objects.get(user=user)
            date=datetime.today()
            attendance_record = Attendance.objects.get(employee=employee, date=date)
            if attendance_record.time_in:#Check if employee has already punched-in
                punchedin=True
            else:
                punchedin=False
            if attendance_record.time_out:#Check if employee has punched-out
                punchedout=True
            else:
                punchedout=False
            return Response({'punchedout': punchedout,'punchedin':punchedin}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)
        except Attendance.DoesNotExist:
            return Response({'error': 'Attendance record not found for the specified user and date'}, status=status.HTTP_404_NOT_FOUND)

class AddAttendance(APIView):
    def get(self,request):
        user=request.user 
        employee=Employee.objects.get(user=user)
        date=datetime.today()
        attendance=Attendance.objects.get(employee=employee,date=date)
        serializer=AttendenceSerializer(attendance).data
        return Response({'attendance':serializer},status=status.HTTP_200_OK)
    def post(self,request):
        user=request.user
        currentip = request.data['ip']
        employee=Employee.objects.get(user=user)
        type=request.data['type']
        child = employee.main_child
        iprestriction=child.iprestriction

        if type=="PUNCHIN":
            child = employee.main_child
            try:
                ips = IPData.objects.get(parent=child.parent,child=child)
                if iprestriction and ips.get_ipaddresses!=None and currentip not in ips.get_ipaddresses() and not IPExceptions.objects.filter(employee=employee).exists():
                    return Response({'error':'Your ip is restricted'},status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({'error':str(e)},status=status.HTTP_401_UNAUTHORIZED)
            punch_in_time = datetime.now()
            punch_in_time=datetime.strftime(punch_in_time,'%H:%M:%S')
            try:
                policy = AttendancePolicy.objects.get(parent=child.parent, child=child)
                office_start_time = policy.officeStartTime.strftime('%H:%M:%S')
                if punch_in_time <= office_start_time:
                    punchstatus = 'present'
                else:
                    punchstatus = 'latelogin'
            except AttendancePolicy.DoesNotExist:
                punchstatus = 'present'
            if(Attendance.objects.filter(employee=employee,date=datetime.today(),time_in__isnull=False).exists()):#Prevent double punch-in
                return Response({'error':'You have already punched in today'},status=status.HTTP_400_BAD_REQUEST)
            Attendance.objects.create(parent=child.parent,status=punchstatus,child=child,employee=employee,date=datetime.today(),time_in=datetime.now())
            return Response({'sucess':'Punched in Successfully'})
        if type=="PUNCHOUT":
            id=request.data['id']
            attendance=Attendance.objects.get(id=id)
            employee=attendance.employee
            date=datetime.today().date()
            breakobj=BreakTime.objects.filter(employee=employee,date=date)
            if len(breakobj)>0:
                if not breakobj[len(breakobj)-1].time_out:
                    return Response({'error':'Please Break Out First Inorder to Punch Out'},status=status.HTTP_400_BAD_REQUEST)
            attendance.time_out=datetime.now()#Save punch-out time
            attendance.save()
            calculate_attendance(employee)#Calculate all attendance logic
            return Response({'sucess':'Punched out Successfully'})

class IPExceptionView(APIView):#Used to add employees who can punch-in from any IP.
    def post(self, request):
        user = request.user
        employeeid = request.data.get('empid')   
        employee = get_object_or_404(Employee, id=employeeid)
        if not IPExceptions.objects.filter(employee=employee).exists():
            exceptionobj = IPExceptions.objects.create(employee=employee, addedby=user)
            return Response({'message': 'Successfully Added.'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Employee Already Exists.'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user = request.user
        id = request.data.get('id')
        ip_exception = get_object_or_404(IPExceptions, id=id)
        ip_exception.delete()
        return Response({'message': 'Deleted Successfully.'}, status=status.HTTP_200_OK)

class GetIPExceptionUsers(APIView):#Returns list of employees who have IP exception.
    def post(self, request):
        childid = request.data.get('childid')
        child = get_object_or_404(ChildAccount, id=childid)
        employees = IPExceptions.objects.filter(employee__child=child)
        serializer = IPExceptionsSerializer(employees, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

class GetDateBreaks(APIView):#Used in admin panel — shows break list for a selected attendance record.
    def post(self,request):
        user=request.user
        id = request.data.get('id')
        attobj = Attendance.objects.get(id = id)
        breakobj=BreakTime.objects.filter(employee=attobj.employee,date=attobj.date)
        serializer=BreakTimeSerializer(breakobj,many=True).data
        return Response({'data':serializer},status=status.HTTP_200_OK)

class AddBreak(APIView):
    def get(self,request):
        user=request.user 
        employee=Employee.objects.get(user=user)
        date=datetime.today()
        breakobj=BreakTime.objects.filter(employee=employee,date=date)
        serializer=BreakTimeSerializer(breakobj,many=True).data #Serialize all break entries to JSON.
        return Response({'break':serializer},status=status.HTTP_200_OK)
    def post(self,request):
        user=request.user
        employee=Employee.objects.get(user=user)
        type=request.data['type']
        if type=="BREAKIN":
            reason = request.data.get('reason')
            child = employee.main_child
            BreakTime.objects.create(parent=child.parent,child=child,employee=employee,date=datetime.today(),time_in=datetime.now(),reason=reason)
            return Response({'sucess':'Break in Success'})
        if type=="BREAKOUT":
            id=request.data['id']
            attendance=BreakTime.objects.get(id=id)
            attendance.time_out=datetime.now()
            attendance.net_time_in = subtract_times(attendance.time_out , attendance.time_in)
            attendance.save()
            return Response({'sucess':'Break out Success'})

class getAttendance(APIView):#Returns full attendance list for a particular child company.
    permission_classes = [IsAuthenticated]
    def post(self, request, **kwargs):
        user = request.user
        empobj = Employee.objects.get(user=user)
        parent = empobj.parent
        childid=request.data['childid']
        child = ChildAccount.objects.get(id = childid)
        attobjs = Attendance.objects.filter(parent=parent, child=child).order_by('-date', 'parent', 'child', 'employee')
        serializer = AttendenceSerializer(attobjs, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)#Send final attendance data to frontend.

class userAttendance(APIView):#Fetches last 7 days attendance of logged-in user.
    permission_classes = [IsAuthenticated]
    def get(self, request, **kwargs):
        user = request.user
        empobj = Employee.objects.get(user=user)
        attobjs = Attendance.objects.filter(employee = empobj).order_by('-date')[:7]#Last 7 attendance entries (sorted by date descending).
        serializer = AttendenceSerializer(attobjs, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

class AttendanceListView(APIView):#Employee selects from_date and to_date → Backend returns all attendance records within that date range.
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        employee = Employee.objects.get(user=user)
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        
        if not from_date or not to_date:
            return Response({'error': 'from_date and to_date are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)
        
        attendances = Attendance.objects.filter(employee=employee, date__range=[from_date, to_date]).order_by('date')
        serializer = AttendenceSerializer(attendances, many=True)
        
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

class UploadAttendance(APIView):#HR/Admin uploads a CSV file containing attendance for whole month.
    def post(self, request):
        user = request.user
        childid=request.data['childid']
        month=request.data['month']
        year=request.data['year']
        workingdays=int(request.data['workingDays'])
        child = ChildAccount.objects.get(id = childid)
        parent=Employee.objects.get(user=user).parent
        file = request.FILES.get('file')
        parentid=parent.id
        try:#Replace old MonthlyData
            mobj = MonthlyData.objects.get(parent=parent,child=child,month=int(month),year=int(year))
            mobj.delete()
        except:
            pass
        MonthlyData.objects.create(parent=parent,child=child,no_of_working_days=workingdays,month=int(month),year=int(year))
        if 'file' not in request.FILES:
            return Response({"error": "No file uploaded"}, status=400)
        file = request.FILES['file']
        if not file.name.endswith('.csv'):
            return Response({"error": "File format not supported. Please upload a CSV file"}, status=400)
        try:#Decode CSV
            decoded_file = file.read().decode('utf-8-sig').splitlines()
            csv_data = csv.DictReader(decoded_file)
            dates = list(csv_data.fieldnames)[1:]#Extract date columns
            for row in csv_data:
                print("row",row)
                employee_email = row['employeeemail']
                employee = Employee.objects.get(email=employee_email)
                for date_str in dates:#Loop each date and store attendance
                    if date_str=="":
                        break;
                    attendance_status = row[date_str]
                    date_value = datetime.strptime(date_str,'%m/%d/%Y')
                    try:#Delete old attendance if exists
                        atobj = Attendance.objects.get(
                            employee=employee,
                            date=date_value,
                            parent=parent,
                            child=child
                        )
                        atobj.delete()
                    except:
                        pass
                    if attendance_status=="P" or attendance_status=="p" :
                        Attendance.objects.create(
                            employee=employee,
                            date=date_value,
                            parent=parent,
                            child=child,
                            logged_in=True,
                            status="present",
                            is_editable=False
                        )
                    if attendance_status=="AB" or attendance_status=="ab" :
                        Attendance.objects.create(
                            employee=employee,
                            date=date_value,
                            parent=parent,
                            child=child,
                            logged_in=False,
                            status="leave",
                            is_editable=False
                        )
                    if attendance_status=="H" or attendance_status=="h":
                        Attendance.objects.create(
                            employee=employee,
                            date=date_value,
                            parent=parent,
                            child=child,
                            logged_in=True,
                            status="holiday",
                            
                            is_editable=False
                        )
            return Response({"message": "Attendance data uploaded successfully"}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class AttendanceRequestSerializer1(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, **kwargs):
        user = request.user
        empobj = Employee.objects.get(user=user)
        parent = empobj.parent
        childid=request.data['childid']
        child=ChildAccount.objects.get(id = childid)
        attobjs = AttendanceRequestPolicy.objects.get(parent=parent, child=child)
        serializer = AttendanceRequestSerializer(attobjs, many=False)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)




class AttendanceInfo(APIView):
    def post(self, request):
        user = request.user
        employee = Employee.objects.get(user=user)
        parent = employee.parent
        child = employee.main_child
        current_date = datetime.today()
        def get_monthly_data(target_date):#calculates all attendance details for one month.
            target_date = target_date.date()#Convert given target_date → Year, Month
            month = target_date.month
            year = target_date.year
            month_name = calendar.month_name[month][:3]
            holidays = Holidays.objects.filter(
                parent=parent, 
                child=child, 
                date__year=year, 
                date__month=month
            ).values_list('date', flat=True)
            holiday_days = {holiday.day for holiday in holidays}
            pres = Attendance.objects.filter(#Count Presents
                date__month=month, 
                date__year=year, 
                parent=parent,
                logged_in = True, 
                child=child, 
                employee=employee
            ).count()
            working_days = MonthlyData.objects.get(
                month=month, 
                year=year, 
                parent=parent, 
                child=child
            ).no_of_working_days
            abse = working_days - pres
            late = Attendance.objects.filter(#Count late login days
                date__month=month, 
                date__year=year, 
                parent=parent,
                logged_in = True, 
                status='latelogin',
                child=child, 
                employee=employee
            ).count()
            try:#6. Working Days Policy (Mon–Fri or custom)
                attendance_policy = AttendancePolicy.objects.get(
                    parent=parent, 
                    child=child
                )
                working_days_ap = set(attendance_policy.get_workingDays())

            except AttendancePolicy.DoesNotExist:
                working_days_ap = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']  
            absent_days = set()
            present_days = Attendance.objects.filter(
                date__month=month, 
                date__year=year, 
                parent=parent, 
                logged_in = True, 
                child=child, 
                employee=employee
            ).values_list('date', flat=True)
            #calculation of ABSENT days
            if month == datetime.today().month:#Find all days in the month
                all_days = set(range(1,datetime.today().day))
            else:
                all_days = set(range(1, calendar.monthrange(year, month)[1] + 1))
            working_days_set = {day for day in all_days if get_day_of_week(year, month, day) in working_days_ap}
            present_days_set = {day.day for day in present_days}
            working_days_set = working_days_set - holiday_days
            absent_days = working_days_set - present_days_set#Calculate absent days
            leave_days = set()
            #Get all approved leaves
            leaves_queryset = leaves.objects.filter(
                employee=employee,
                parent=parent,
                child=child,
                fromDate__lte=target_date.replace(day=calendar.monthrange(year, month)[1]),
                toDate__gte=target_date.replace(day=1),
                status = "approved"
            )
            for leave in leaves_queryset:
                leave_start = max(leave.fromDate, target_date.replace(day=1))
                leave_end = min(leave.toDate, target_date.replace(day=calendar.monthrange(year, month)[1]))
                leave_range = set(range(leave_start.day, leave_end.day + 1))
                leave_days.update(leave_range)
            absences = [
                {'date': f"{day}-{month}-{year}", 'type': 'leave' if day in leave_days else 'absent'}
                for day in absent_days
            ]
            return {
                'pres': pres,
                'abse': len(absences),
                'wor': working_days,
                'name': month_name,
                'late':late,
                'year': year,
                'absences': absences,
            }
              #Fetch 3 months data
        current_month_date = (current_date.replace(day=1)- timedelta(days=1)).replace(day=1)
        current_month_data = get_monthly_data(current_month_date)
        previous_month_date = (current_month_date.replace(day=1) - timedelta(days=1)).replace(day=1)
        previous_month_data = get_monthly_data(previous_month_date)
        prev_previous_month_date = (previous_month_date - timedelta(days=1)).replace(day=1)
        prev_previous_month_data = get_monthly_data(prev_previous_month_date)
        response_data = {
            'current': current_month_data,
            'previous': previous_month_data,
            'prev_previous': prev_previous_month_data,
        }
        return Response({'data': response_data}, status=status.HTTP_200_OK)


class CurrentMonthMetrics(APIView):#Quick summary for UI dashboard
    def get(self,request):
        user = request.user
        employee = Employee.objects.get(user=user)
        parent = employee.parent
        child = employee.main_child
        current_date = datetime.today()
        target_date = current_date.date()
        month = target_date.month
        year = target_date.year
        working_days = MonthlyData.objects.get(
                month=month, 
                year=year, 
                parent=parent, 
                child=child
            ).no_of_working_days
        late = Attendance.objects.filter(
                date__month=month, 
                date__year=year, 
                parent=parent,
                logged_in = True, 
                status='latelogin',
                child=child, 
                employee=employee
            ).values_list('date', flat=True)
        present_days = Attendance.objects.filter(
                date__month=month, 
                date__year=year, 
                parent=parent, 
                logged_in = True, 
                child=child, 
                employee=employee,
                status='present'
            ).values_list('date', flat=True)
        absent_days = Attendance.objects.filter(
                date__month=month, 
                date__year=year, 
                parent=parent, 
                child=child, 
                employee=employee,
                status='absent'
            ).values_list()
        leave_days = Attendance.objects.filter(
                date__month=month, 
                date__year=year, 
                parent=parent, 
                child=child, 
                employee=employee,
                status='leave'
            ).values_list()
        return Response({'present': present_days,'absent':absent_days,'late':late,'working':working_days,'leave':leave_days}, status=status.HTTP_200_OK)

class getPresentAbsentMonth(APIView):#Simple monthly summary
    def get(self, request):
        user = request.user
        employee = Employee.objects.get(user = user)
        current_month = datetime.now().month
        current_year = datetime.now().year
        present_days = Attendance.objects.filter(employee=employee,date__month = current_month,date__year = current_year,logged_in=True).count()
        absent_days = Attendance.objects.filter(employee=employee,date__month = current_month,date__year = current_year,logged_in=False).count()
        working_days = MonthlyData.objects.filter(parent = employee.parent,child=employee.main_child,month = current_month,year=current_year).count()
        return Response({'present':present_days,'absent':absent_days,'working':working_days},status=status.HTTP_200_OK)



class AddAttendanceView(APIView):#Bulk attendance upload (JSON)
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            attendances = data.get("attendances", [])

            for entry in attendances:
                emp_id = entry.get("empId")
                month = entry.get("month")
                year = entry.get("year")
                absent_days = set(entry.get("absentDays", []))
                
                employee = get_object_or_404(Employee, id=emp_id)
                parent = employee.parent
                child = employee.main_child

                total_days = calendar.monthrange(year, month)[1]
                #Create attendance for each day
                for day in range(1, total_days + 1):
                    attendance_date = date(year, month, day)
                    stats = "leave" if day in absent_days else "present"
                    #Save attendance
                    Attendance.objects.create(
                        employee=employee,
                        parent=parent,
                        child=child,
                        date=attendance_date,
                        status=stats
                    )

            return Response({"message": "Attendance recorded successfully"}, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)