from rest_framework import status
from ..models import *
from ..decorators import *
from ..serializers import *
from ..tasks import *
from rest_framework.response import Response
from ..utils import *
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime
from payrollapp.models import Employee, ChildAccount, leaves
from payrollapp.serializers import LeavesSerializer


def has_child_permission(user, child):
    """
    Returns True if the logged-in user has permission
    to view data for the given child account.
    """

    try:
        employee = Employee.objects.get(user=user)
    except Employee.DoesNotExist:
        return False

    # Role-based access
    if employee.roles.filter(
        name__in=["HR", "HR_Admin", "HR_HEAD", "BUSINESS_OWNER"]
    ).exists():
        return True

    # Child access
    if employee.child.filter(id=child.id).exists():
        return True

    # Main child access
    if employee.main_child == child:
        return True

    return False


# ======================================================
# ATTENDANCE METRICS (COUNTS)
# ======================================================
class AttendanceMetricsAPIView(APIView):
    def post(self, request):
        user = request.user
        childid = request.data.get("childid")

        if not childid:
            return Response(
                {"error": "childid is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            child = ChildAccount.objects.get(id=childid)
        except ChildAccount.DoesNotExist:
            return Response(
                {"error": "Invalid child"},
                status=status.HTTP_404_NOT_FOUND
            )

        if not has_child_permission(user, child):
            return Response(
                {"error": "You are not authorized to view this record"},
                status=status.HTTP_403_FORBIDDEN
            )

        today = datetime.now().date()

        employees = Employee.objects.filter(main_child=child)
        attendances = Attendance.objects.filter(child=child, date=today)

        attendance_data = {
            "present": attendances.filter(status="present").count(),
            "notMarked": max(employees.count() - attendances.count(), 0),
            "latelogin": attendances.filter(status="latelogin").count(),
            "halfday": attendances.filter(status="halfday").count(),
            "leave": attendances.filter(status__iexact="leave").count(),
        }

        return Response({"data": attendance_data}, status=status.HTTP_200_OK)


# ======================================================
# ATTENDANCE LIST DATA
# ======================================================
class AttendanceDataAPIView(APIView):
    def post(self, request):
        user = request.user
        childid = request.data.get("childid")

        if not childid:
            return Response(
                {"error": "childid is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            child = ChildAccount.objects.get(id=childid)
        except ChildAccount.DoesNotExist:
            return Response(
                {"error": "Invalid child"},
                status=status.HTTP_404_NOT_FOUND
            )

        if not has_child_permission(user, child):
            return Response(
                {"error": "You are not authorized to view this record"},
                status=status.HTTP_403_FORBIDDEN
            )
        today = datetime.now().date()
        attendance = Attendance.objects.filter(child=child, date=today)

        serializer = AttendenceSerializer(attendance, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)


# ======================================================
# PENDING LEAVE REQUESTS (FOR APPROVER)
# ======================================================
class pendingRequests(APIView):
    def get(self, request):
        user = request.user

        leaveobjs = leaves.objects.filter(
            approvingPerson=user,
            status="pending"
        ).order_by("-timeStamp")

        serializer = LeavesSerializer(leaveobjs, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)


# ======================================================
# UPCOMING LEAVES
# ======================================================
class upComingLeaves(APIView):
    def post(self, request):
        user = request.user
        childid = request.data.get("childid")

        if not childid:
            return Response(
                {"error": "childid is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            child = ChildAccount.objects.get(id=childid)
        except ChildAccount.DoesNotExist:
            return Response(
                {"error": "Invalid child"},
                status=status.HTTP_404_NOT_FOUND
            )

        if not has_child_permission(user, child):
            return Response(
                {"error": "You are not authorized to view this record"},
                status=status.HTTP_403_FORBIDDEN
            )

        today = datetime.now().date()

        leaveobjs = (
            leaves.objects.filter(child=child, fromDate__gte=today)
            .order_by("fromDate")[:10]
        )

        serializer = LeavesSerializer(leaveobjs, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)