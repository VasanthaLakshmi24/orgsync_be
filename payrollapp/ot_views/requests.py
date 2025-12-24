from rest_framework import status
from ..models import *
from ..decorators import *
from ..serializers import *
from ..tasks import *
from ..utils import *
from rest_framework.response import Response
from rest_framework.views import APIView
from decimal import Decimal , ROUND_HALF_UP
from rest_framework.permissions import IsAuthenticated
# from payrollapp.views import RMLoginRequests



class AttendanceRequest(APIView):
    def post(self,request):
        user=request.user 
        reason=request.data['Description']
        childid=request.data['childid']
        date=request.data['Date']
        employee=Employee.objects.get(user=user)
        child=employee.main_child
        parent=employee.parent
        month=datetime.today().month
        no_of_attempts=AttendanceRequestPolicy.objects.get(parent=parent,child=child).no_of_requests
        print(no_of_attempts)
        requests=len(AttendanceRequestObject.objects.filter(employee=employee,Date__month=month))
        if no_of_attempts-requests>0:
            print("ok")
            AttendanceRequestObject.objects.create(employee=employee,reason=reason,parent=parent,child=child,status="underreview",Date=date)
            print("created")
            remainedattempts=no_of_attempts-requests-1
            return Response({'sucess':'Attendance Request Submitted successfully\n.You are still having {remainedattempts} more attendance requests in this month'},status=status.HTTP_200_OK)  
        else:
            return Response({'error':'Your limit exceeded for this month.You cant apply for an attendance request'},status=status.HTTP_400_BAD_REQUEST)
    def put(self,request):
        user=request.user
        id=request.data['id']
        attobj=AttendanceRequestObject.objects.get(id=id)
        reqstatus=request.data['status']
        reqemp=attobj.employee 
        date=attobj.Date
        child=attobj.child
        parent=attobj.parent
        emp=Employee.objects.get(user=user)
        if reqstatus=="approved":
            if child.HrHead==user:
                att = Attendance.objects.get(child=child,parent=parent,date=date,employee=reqemp)
                att.status = 'present'
                attobj.status="approved"
                attobj.save()
            return Response({'success':'Attendance Added Successfully'},status=status.HTTP_200_OK)
        else:
            if child.HrHead==user:
                attobj.status="rejected"
                attobj.save()
            return Response({'success':'Status Updated Successfully'},status=status.HTTP_200_OK)

class CompensationRequest(APIView):
    def post(self,request):
        user=request.user 
        reason=request.data['Description']
        childid=request.data['childid']
        date=request.data['Date']
        employee=Employee.objects.get(user=user)
        child=ChildAccount.objects.get(id=childid)
        parent=employee.parent
        CompOffRequestObject.objects.create(employee=employee,reason=reason,parent=parent,child=child,managerstatus="underreview",hrstatus="underreview",Date=date,approvedbyhr=child.HrHead,approvedbyrm=employee.reported_to)
        return Response({'sucess':'Compensation Off Request Submitted successfully'},status=status.HTTP_200_OK)  
    
    def put(self,request):
        user=request.user
        id=request.data['id']
        attobj=CompOffRequestObject.objects.get(id=id)
        
        reqemp=attobj.employee
        date=attobj.Date
        child=attobj.child
        parent=attobj.parent
        emp=Employee.objects.get(user=user)
        if user==attobj.employee.reported_to:
            managerstatus=request.data['managerstatus']
            if managerstatus=="approved":
                attobj.managerstatus="approved"
                print("approved")
                if user==attobj.employee.main_child.HrHead:
                    attobj.hrstatus="approved"
                    attobj.save()
                    try :
                        print("into")
                        object=LeaveBalance.objects.get(employee = reqemp, parent = parent, child=child)
                        print("object leave balance")
                        object.leave_balance+=1
                        object.save()
                    except:
                        print("getting an error")
                    pass
                    return Response({'success':'You  approved the request Successfully'},status=status.HTTP_200_OK)
                attobj.save()
                return Response({'success':'You  approved the request Successfully'},status=status.HTTP_200_OK)
            else:
                attobj.managerstatus="rejected"
                attobj.hrstatus="rejected"
                attobj.save()
                return Response({'success':'Status Updated Successfully'},status=status.HTTP_200_OK)

class HRCompensationRequest(APIView):
    def put(self,request):
        user=request.user
        id=request.data['id']
        attobj=CompOffRequestObject.objects.get(id=id)
        reqemp=attobj.employee
        date=attobj.Date
        child=attobj.child
        parent=attobj.parent
        emp=Employee.objects.get(user=user)
        if user==child.HrHead:
            hrstatus=request.data['hrstatus']
            print("entered into hr")
            if hrstatus=="approved":
                attobj.hrstatus="approved"
                print("approved")
                attobj.save()
                try :
                    print("into")
                    object=LeaveBalance.objects.get(employee = reqemp, parent = parent, child=child)
                    print("object leave balance")
                    object.leave_balance+=1
                    object.save()
                except:
                    print("getting an error")
                    pass
                return Response({'success':'You  approved the request Successfully'},status=status.HTTP_200_OK)
            else:
                attobj.hrstatus="rejected"
                attobj.save()
                return Response({'success':'Status Updated Successfully'},status=status.HTTP_200_OK)

class HRCompApprovals(APIView):
    def post(self,request):
        user=request.user
        employee=Employee.objects.get(user=user)
        childid=request.data['childid']
        parent=employee.parent
        child=ChildAccount.objects.get(id=childid)
        reqobj=CompOffRequestObject.objects.filter(employee=employee,parent=parent,child=child,managerstatus="approved",)
        data=CompOffRequestsSerializer(reqobj,many=True).data
        return Response({'data':data},status=status.HTTP_200_OK)

# class LateLoginRequest(APIView):
    def post(self,request):
        user=request.user
        reason=request.data['Description']
        date=request.data['Date']
        employee=Employee.objects.get(user=user)
        child=employee.main_child
        parent=employee.parent
        rm=employee.reported_to
        rm=Employee.objects.get(user=rm)
        month=datetime.today().month
        no_of_attempts=LateLoginPolicy.objects.get(parent=parent,child=child).no_of_late_logins
        requests=len(LateLoginRequestObject.objects.filter(employee=employee,Date__month=month))
        if no_of_attempts-requests>0:
            LateLoginRequestObject.objects.create(employee=employee,reason=reason,parent=parent,child=child,status="underreview",Date=date,reported_to=rm)
            remainedattempts=no_of_attempts-requests-1
            if remainedattempts==0:
                return Response({'sucess':f'Late Login Request Submitted successfully\n.with this your Late Login requests  limit completed for  this month!!'},status=status.HTTP_200_OK)
            return Response({'sucess':f'Late Login Request Submitted successfully\n.You are still having {remainedattempts} more Late Login requests in this month'},status=status.HTTP_200_OK)  
        else:
            return Response({'error':'Your limit exceeded for this month.You cant apply for an Late Login requests'},status=status.HTTP_400_BAD_REQUEST)
    def put(self,request):
        user=request.user
        id=request.data['id']
        attobj=LateLoginRequestObject.objects.get(id=id)
        reqemp=attobj.employee
        reqstatus=request.data['status']
        reqemp=attobj.employee
        if reqstatus=="approved":
            if reqemp.reported_to==user:
                attobj.status="approved"
                print("approved")
                attobj.save()
            return Response({'success':'Attendance Added Successfully'},status=status.HTTP_200_OK)
        else:
            attobj.status="rejected"
            attobj.save()
            return Response({'success':'Status Updated Successfully'},status=status.HTTP_200_OK)

class HRAttRequests(APIView):
    def post(self,request):
        user=request.user 
        employee=Employee.objects.get(user=user)
        childid=request.data['childid']
        parent=employee.parent
        child=ChildAccount.objects.get(id=childid)
        data=AttendanceRequestsSerializer(AttendanceRequestObject.objects.filter(parent=parent,child=child),many=True).data
        return Response({'data':data},status=status.HTTP_200_OK)

class RMLoginRequests(APIView):
    def post(self,request):
        user=request.user 
        employee=Employee.objects.get(user=user)
        childid=request.data['childid']
        parent=employee.parent
        child=ChildAccount.objects.get(id=childid)
        data=LateLoginRequestSerializer(LateLoginRequestObject.objects.filter(parent=parent,child=child,reported_to=employee),many=True).data
        return Response({'data':data},status=status.HTTP_200_OK)

class DisplayAttRequests(APIView):
    def post(self,request):
        user=request.user
        employee=Employee.objects.get(user=user)
        childid=request.data['childid']
        parent=employee.parent
        child=ChildAccount.objects.get(id=childid)
        reqobj=AttendanceRequestObject.objects.filter(employee=employee,parent=parent,child=child)
        data=AttendanceRequestsSerializer(reqobj,many=True).data
        return Response({'data':data},status=status.HTTP_200_OK)

class DisplayLoginRequests(APIView):
    def post(self,request):
        user=request.user
        employee=Employee.objects.get(user=user)
        childid=request.data['childid']
        parent=employee.parent
        child=ChildAccount.objects.get(id=childid)
        reqobj=LateLoginRequestObject.objects.filter(employee=employee,parent=parent,child=child)
        data=LateLoginRequestSerializer(reqobj,many=True).data
        return Response({'data':data},status=status.HTTP_200_OK)


class CompOffRequests(APIView):
    def post(self,request):
        user=request.user
        employee=Employee.objects.get(user=user)
        childid=request.data['childid']
        parent=employee.parent
        child=ChildAccount.objects.get(id=childid)
        reqobj=CompOffRequestObject.objects.filter(employee=employee,parent=parent,child=child,)
        mydata=CompOffRequestsSerializer(reqobj,many=True).data
        recobj=CompOffRequestObject.objects.filter(parent=parent,child=child,approvedbyrm=user)
        data=CompOffRequestsSerializer(recobj,many=True).data
        return Response({'data':data,'my_data':mydata},status=status.HTTP_200_OK)

class HRCompOffRequests(APIView):
    def post(self,request):
        user=request.user
        employee=Employee.objects.get(user=user)
        childid=request.data['childid']
        parent=employee.parent
        child=ChildAccount.objects.get(id=childid)
        reqobj=CompOffRequestObject.objects.filter(approvedbyhr=user,parent=parent,child=child,managerstatus="approved")
        data=CompOffRequestsSerializer(reqobj,many=True).data
        return Response({'data':data},status=status.HTTP_200_OK)


class fetchlaterequests(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        employee=Employee.objects.get(user=user)
        my_req = LateLoginRequestObject.objects.filter(employee = employee)
        req = LateLoginRequestObject.objects.filter(reported_to = employee)
        my_serializer = LateLoginRequestSerializer(my_req, many=True)
        req_serializer = LateLoginRequestSerializer(req, many=True)
        return Response({'my_req':my_serializer.data , 'req':req_serializer.data}, status=status.HTTP_200_OK)


