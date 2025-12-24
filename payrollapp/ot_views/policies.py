from django.shortcuts import get_object_or_404
from rest_framework import status
from ..models import *
from ..decorators import *
from ..serializers import *
from ..tasks import *
from rest_framework.views import APIView
from rest_framework.response import Response
from ..utils import *
from rest_framework.permissions import IsAuthenticated


class LeaveApprovalFlowView(APIView):
    def get(self,request):
        try:
            user = request.user
            child_id = request.GET.get('child_id')
            child = ChildAccount.objects.get(id=child_id)
            leaveapprovals = LeaveApprovalFlow.objects.filter(parent = child.parent,child=child)
            serializer = LeaveApprovalFlowSerializer(leaveapprovals, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def post(self,request):
        try:
            user = request.user
            child_id = request.data.get('child_id')
            child = ChildAccount.objects.get(id=child_id)
            days = request.data.get('days')
            level = request.data.get('level')
            approvingPerson = request.data.get('approvingPerson')
            LeaveApprovalFlow.objects.create(parent = child.parent,child=child,days = days,level = level,approvingPerson = approvingPerson)
            return Response({"message": "Leave approval flow added successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def put(self,request):
        try:
            user = request.user
            laf_id = request.data.get('laf_id')
            days = request.data.get('days')
            level = request.data.get('level')
            approvingPerson = request.data.get('approvingPerson')
            laf = LeaveApprovalFlow.objects.get(id=laf_id)
            laf.days = days
            laf.level = level
            laf.approvingPerson = approvingPerson
            laf.save()
            return Response({"message": "Leave approval flow updated successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self,request):
        try:
            user = request.user
            laf_id = request.data.get('laf_id')
            laf = LeaveApprovalFlow.objects.get(id=laf_id)
            laf.delete()
            return Response({"message": "Leave approval flow deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FetchAttendancePolicy(APIView):
    def post(self, request):
        childid = request.data.get('childid')
        child = ChildAccount.objects.get(id=childid)
        try:
            policy = AttendancePolicy.objects.get(child=child)
            serializer = AttendancePolicySerializer(policy)
            return Response({'data': serializer.data}, status=status.HTTP_200_OK)
        except AttendancePolicy.DoesNotExist:
            return Response({'error': 'Policy not found'}, status=status.HTTP_404_NOT_FOUND)

class CreatePolicyView(APIView):
    def post(self, request):
        user=request.user
        employee=Employee.objects.get(user=user)
        parent=employee.parent
        childid = request.data.get('childid')
        child=ChildAccount.objects.get(id=childid)
        officeEndTime=request.data['officeEndTime']
        officeStartTime=request.data['officeStartTime']
        workingDays=request.data['workingDays']
        try:
            obj=AttendancePolicy.objects.create(parent=parent, child=child, officeEndTime=officeEndTime, officeStartTime=officeStartTime)
            obj.set_workingDays(workingDays)
            obj.save()
            return Response({'success': 'Policy created successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    def put(self, request):
        id = request.data.get('id')
        officeEndTime=request.data['officeEndTime']
        officeStartTime=request.data['officeStartTime']
        workingDays=request.data['workingDays']
        try:
            obj = AttendancePolicy.objects.get(id = id)
            obj.officeEndTime = officeEndTime
            obj.officeStartTime = officeStartTime
            obj.set_workingDays(workingDays)
            obj.save()
            return Response({'success': 'Policy updated successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class FetchAttendanceReqPolicy(APIView):
    def post(self, request):
        childid = request.data.get('childid')
        child = ChildAccount.objects.get(id=childid)
        try:
            policy = AttendanceRequestPolicy.objects.get(child=child)
            serializer = AttendanceRequestSerializer(policy)
            return Response({'data': serializer.data}, status=status.HTTP_200_OK)
        except AttendancePolicy.DoesNotExist:
            return Response({'error': 'Policy not found'}, status=status.HTTP_404_NOT_FOUND)

class AttendanceRequestPolicyView(APIView):
    def post(self, request):
        user=request.user
        employee=Employee.objects.get(user=user)
        parent=employee.parent
        childid = request.data.get('childid')
        child=ChildAccount.objects.get(id=childid)
        no_of_requests=request.data['no_of_requests']
        try:
            AttendanceRequestPolicy.objects.create(parent=parent,child=child,no_of_requests=no_of_requests)
            return Response({'success': 'Attendance Request Policy created successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    def put(self,request):
        id = request.data.get('id')
        no_of_requests=request.data['no_of_requests']
        try:
            att = AttendanceRequestPolicy.objects.get(id = id)
            att.no_of_requests = no_of_requests
            att.save()
            return Response({'success': 'Attendance Request Policy updated successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class FetchLateLoginPolicy(APIView):
    def post(self, request):
        childid = request.data.get('childid')
        child = ChildAccount.objects.get(id=childid)
        try:
            policy = LateLoginPolicy.objects.get(child=child)
            serializer = LateLoginPolicySerializer(policy)
            return Response({'data': serializer.data}, status=status.HTTP_200_OK)
        except LateLoginPolicy.DoesNotExist:
            return Response({'error': 'LateLogin Policy not found'}, status=status.HTTP_404_NOT_FOUND)

class CreateLateLoginPolicy(APIView):
    def post(self, request):
        user=request.user
        employee=Employee.objects.get(user=user)
        parent=employee.parent
        childid = request.data.get('childid')
        child=ChildAccount.objects.get(id=childid)
        no_of_late_logins=request.data['no_of_late_logins']
        no_of_hour=request.data['no_of_hour']
        try:
            obj=LateLoginPolicy.objects.create(parent=parent, child=child,no_of_late_logins=no_of_late_logins,no_of_hour=no_of_hour)
            return Response({'success': 'Late Login Policy created successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PfSlabsListCreateView(APIView):
    def get(self, request, child_id=None):
        user = request.user
        child = ChildAccount.objects.get(id = child_id)
        parent = child.parent
        if child_id:
            slabs = PfSlabs.objects.filter(parent=parent, child=child)
        else:
            slabs = PfSlabs.objects.filter(parent=parent)
        serializer = PfSlabsSerializer(slabs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, child_id=None):
        start_amount = request.data.get('start_amount')
        end_amount = request.data.get('end_amount')
        pf_amount = request.data.get('pf_amount')
        unit = request.data.get('unit')
        child = ChildAccount.objects.get(id = child_id)
        parent = child.parent
        obj = PfSlabs.objects.create(child=child,parent=parent,start_amount = start_amount,end_amount = end_amount,pf_amount = pf_amount,unit = unit)
        return Response({"message":'Successfully Created'}, status=status.HTTP_201_CREATED)

class PfSlabsDetailView(APIView):
    
    def get(self, request, pk):
        pfslab = get_object_or_404(PfSlabs,pk=pk)
        serializer = PfSlabsSerializer(pfslab)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        pfslab = get_object_or_404(PfSlabs,pk=pk)
        serializer = PfSlabsSerializer(pfslab, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        pfslab = get_object_or_404(PfSlabs,pk=pk)
        pfslab.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class LeavePolicies1(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, **kwargs):
        user = request.user
        empobj = Employee.objects.get(user=user)
        parent = empobj.parent
        childid=request.data['childid']
        child=ChildAccount.objects.get(id = childid)
        attobjs = LeavePolicy.objects.get(parent=parent, child=child)
        serializer = LeavePolicySerializer(attobjs, many=False)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

class payrollpolicies(APIView):
    def get(self, request, **kwargs):
        user = request.user
        empobj = Employee.objects.get(user=user)
        parent = empobj.parent
        childid=request.GET.get('childid')
        child=ChildAccount.objects.get(id = childid)
        attobjs = PayrollPolicy.objects.get(parent=parent, child=child)
        serializer = PayrollPolicySerializer(attobjs, many=False)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

    def post(self,request):
        childid=request.data['childid']
        child=ChildAccount.objects.get(id=childid)
        parent=child.parent
        payslipHeaderCompany=request.data['payslipHeaderCompany']
        payslipHeadertagline=request.data['payslipHeadertagline']
        payslipHeaderAddress=request.data['pf_percentage']
        payslipHeaderlogo = request.FILES.get('logo')
        PayrollPolicy.objects.create(payslipHeaderCompany=payslipHeaderCompany,payslipHeadertagline=payslipHeadertagline,payslipHeaderAddress=payslipHeaderAddress,child=child,parent=parent,payslipHeaderlogo=payslipHeaderlogo)
        return Response({'success':"Payroll Policy Created Successfully"},status=status.HTTP_200_OK)
    def put(self,request):
        obj_id = request.data.get('obj_id')
        payslipHeaderCompany=request.data['payslipHeaderCompany']
        payslipHeadertagline=request.data['payslipHeadertagline']
        payslipHeaderAddress=request.data['payslipHeaderAddress']
        payslipHeaderlogo = request.FILES.get('logo')
        payrollobj=PayrollPolicy.objects.get(id=obj_id)
        if payslipHeaderlogo:
            payrollobj.payslipHeaderlogo = payslipHeaderlogo
        payrollobj.payslipHeaderCompany=payslipHeaderCompany
        payrollobj.payslipHeadertagline=payslipHeadertagline
        payrollobj.payslipHeaderAddress=payslipHeaderAddress
        payrollobj.save()
        return Response({'success':"Payroll Policy Updated Successfully"},status=status.HTTP_200_OK)

class LeavePolicies(APIView):
    def post(self, request, **kwargs):
        user = request.user
        empobj = Employee.objects.get(user=user)
        parent = empobj.parent
        childid=request.data['childid']
        child=ChildAccount.objects.get(id = childid)
        sickLeaves = int(request.data.get('sickLeaves'))
        casualLeaves = int(request.data.get('casualLeaves'))
        maternityLeaves = int(request.data.get('maternityLeaves'))
        leaves_per_year = int(request.data.get('leaves_per_year'))
        privilege_leaves = int(request.data.get('privilege_leaves'))
        paternity_leaves = int(request.data.get('paternity_leaves'))
        bereavement_leaves = int(request.data.get('bereavement_leaves'))
        leaveForwardingUpto = request.data.get('leaveForwardingUpto')
        leaveForwardAfter = request.data.get('leaveForwardAfter')
        if leaveForwardAfter:
            leaveForwardAfter = int(leaveForwardAfter)
        else:
            leaveForwardAfter = None
        autoApprovalBefore = request.data.get('autoApprovalBefore')
        if autoApprovalBefore:
            autoApproval = True
        else:
            autoApproval = False
            autoApprovalBefore = None
        if leaveForwardingUpto and leaveForwardAfter:
            leaveForwarding = True
        else:
            leaveForwarding = False
        try:
            lp = LeavePolicy.objects.get(parent=parent, child=child)
            if (lp):
                return Response({"error": "Policy Already Exists"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            LeavePolicy.objects.create(parent=parent, child=child, sickLeaves = sickLeaves, casualLeaves = casualLeaves, maternityLeaves = maternityLeaves,paternity_leaves = paternity_leaves,privilege_leaves=privilege_leaves,bereavement_leaves=bereavement_leaves,leaves_per_year=leaves_per_year, framedBy = user,leaveForwarding = leaveForwarding,leaveForwardAfter=leaveForwardAfter,leaveForwardingUpto=leaveForwardingUpto,autoApproval=autoApproval,autoApprovalBefore = autoApprovalBefore)
            return Response({'message': 'Leave policy created successfully.'}, status=status.HTTP_201_CREATED)
    def put(self,request,**kwargs):
        user = request.user
        sickLeaves = request.data.get('sickLeaves')
        casualLeaves = request.data.get('casualLeaves')
        maternityLeaves = request.data.get('maternityLeaves')
        leavesWithoutPay = request.data.get('leavesWithoutPay')
        leaves_per_year = request.data.get('leaves_per_year')
        leaveForwardingUpto = request.data.get('leaveForwardingUpto')
        leaveForwardAfter = request.data.get('leaveForwardAfter')
        autoApprovalBefore = request.data.get('autoApprovalBefore')
        if leaveForwardingUpto and leaveForwardAfter:
            leaveForwarding = True
        else:
            leaveForwarding = False
        if autoApprovalBefore:
            autoApproval = True
        else:
            autoApproval = False
            autoApprovalBefore = None
        lp_id = request.data.get('lp_id')
        try:
            lp = LeavePolicy.objects.get(id=lp_id)
            lp.sickLeaves = sickLeaves
            lp.casualLeaves = casualLeaves
            lp.maternityLeaves = maternityLeaves
            lp.leaves_per_year = leaves_per_year 
            lp.leavesWithoutPay = leavesWithoutPay
            lp.leaveForwardingUpto = leaveForwardingUpto
            lp.leaveForwardAfter = leaveForwardAfter
            lp.leaveForwarding = leaveForwarding
            lp.autoApproval = autoApproval
            lp.autoApprovalBefore = autoApprovalBefore
            lp.framedBy = user
            lp.save()
            return Response({"message": "Policy Updated successfully."}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AllowanceView(APIView):
    def get(self,request):
        user=request.user
        child_id = request.GET.get('child_id')
        if child_id:
            child=ChildAccount.objects.get(id=child_id)
            parent = child.parent
        else:
            emp = Employee.objects.get(user=user)
            parent = emp.parent
            child = None
        allowances = Allowance.objects.filter(child=child,parent=parent)
        serializer = AllowanceSerializer(allowances,many=True)
        return  Response({'data':serializer.data}, status=status.HTTP_200_OK)
    def post(self,request):
        user=request.user
        child_id = request.data.get('child_id')
        if child_id:
            child=ChildAccount.objects.get(id=child_id)
            parent = child.parent
        else:
            emp = Employee.objects.get(user=user)
            parent = emp.parent
            child = None
        parent = child.parent
        name = request.data.get('name')
        amount = request.data.get('amount')
        Allowance.objects.create(child=child,parent=parent,name=name,min_value=amount)
        return Response({'success':'Allowance Created Successfully'},status=status.HTTP_200_OK)
    def put(self,request):
        user = request.user
        if not user:
            return Response({'error':'User not found'},status=status.HTTP_400_BAD_REQUEST)
        all_id = request.data.get('all_id')
        name = request.data.get('name')
        amount = request.data.get('amount')
        allo = Allowance.objects.get(id=all_id)
        allo.name = name
        allo.min_value = amount
        allo.save()
        return Response({'success':'Allowance Updated Successfully'},status=status.HTTP_200_OK)
    def delete(self,request):
        user = request.user
        if not user:
            return Response({'error':'User not found'},status=status.HTTP_400_BAD_REQUEST)
        all_id = request.data.get('all_id')
        allo = Allowance.objects.get(id=all_id)
        allo.delete()
        return Response({'success':'Allowance Deleted Successfully'},status=status.HTTP_200_OK)
    
class ProductionAllowanceView(APIView):
    def get(self,request):
        user=request.user
        child_id = request.GET.get('child_id')
        if child_id:
            child=ChildAccount.objects.get(id=child_id)
            parent = child.parent
        else:
            emp = Employee.objects.get(user=user)
            parent = emp.parent
            child = None
        allowances = ProductionAllowance.objects.filter(child=child,parent=parent)
        serializer = ProdAllowanceSerializer(allowances,many=True)
        return  Response({'data':serializer.data}, status=status.HTTP_200_OK)
    def post(self,request):
        user=request.user
        child_id = request.data.get('child_id')
        if child_id:
            child=ChildAccount.objects.get(id=child_id)
            parent = child.parent
        else:
            emp = Employee.objects.get(user=user)
            parent = emp.parent
            child = None
        parent = child.parent
        name = request.data.get('name')
        min_value = request.data.get('min_value')
        max_value = request.data.get('max_value')
        type = request.data.get('type')
        ProductionAllowance.objects.create(child=child,parent=parent,name=name,min_value=min_value,max_value=max_value,type=type)
        return Response({'success':'Allowance Created Successfully'},status=status.HTTP_200_OK)
    def put(self,request):
        user = request.user
        if not user:
            return Response({'error':'User not found'},status=status.HTTP_400_BAD_REQUEST)
        all_id = request.data.get('all_id')
        name = request.data.get('name')
        min_value = request.data.get('min_value')
        max_value = request.data.get('max_value')
        type = request.data.get('type')
        allo = ProductionAllowance.objects.get(id=all_id)
        allo.name = name
        allo.min_value = min_value
        allo.type = type
        allo.max_value = max_value
        allo.save()
        return Response({'success':'Allowance Updated Successfully'},status=status.HTTP_200_OK)
    def delete(self,request):
        user = request.user
        if not user:
            return Response({'error':'User not found'},status=status.HTTP_400_BAD_REQUEST)
        all_id = request.data.get('all_id')
        allo = ProductionAllowance.objects.get(id=all_id)
        allo.delete()
        return Response({'success':'Allowance Deleted Successfully'},status=status.HTTP_200_OK)