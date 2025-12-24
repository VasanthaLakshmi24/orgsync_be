# payrollapp/ot_views/resignation.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from ..models import Resignation, Employee, ChildAccount
from ..serializers import ResignationSerializer
from ..tasks import *
from ..utils import *
from django.shortcuts import get_object_or_404



def safe_email(user_obj):
    """Return user email safely without crashing."""
    if user_obj and hasattr(user_obj, "email") and user_obj.email:
        return user_obj.email
    return None


# ---------------------------------------------------------
# 1. EMPLOYEE SUBMIT RESIGNATION
# ---------------------------------------------------------
class ResignationView(APIView):
    """
    Employees submit resignations here.
    NOTE: Resignation.rm / hr / bo are ForeignKey to User (not Employee).
    """

    def get(self, request):
        try:
            # Return resignations submitted by the logged-in employee
            employee = Employee.objects.get(user=request.user)
            resignation_qs = Resignation.objects.filter(employee=employee).order_by("-timestamp")
            serializer = ResignationSerializer(resignation_qs, many=True)
            return Response(serializer.data)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            employee = Employee.objects.get(user=request.user)

            # reported_to on Employee is a User (per your models)
            rm_user = employee.reported_to  # may be None or a User

            # main_child.bussinessOwner and main_child.HrHead in models are User (not Employee)
            bo_user = None
            hr_user = None
            if employee.main_child:
                # ChildAccount.bussinessOwner is a User FK (or None)
                bo_user = getattr(employee.main_child, "bussinessOwner", None)
                hr_user = getattr(employee.main_child, "HrHead", None)

            resignation = Resignation.objects.create(
                employee=employee,
                reason=request.data.get("reason"),
                noticeperiodtill=request.data.get("noticeperiodtill"),
                handoverings=request.data.get("handoverings"),
                rm=rm_user,
                bo=bo_user,
                hr=hr_user,
            )

            # build recipients from User objects' emails
            recipients = list(filter(None, [
                safe_email(rm_user),
                safe_email(bo_user),
                safe_email(hr_user),
            ]))

            if recipients:
                sendemail(
                    "New Resignation Request",
                    f"{employee.userName} submitted a resignation.",
                    recipients
                )

            # Notify the employee who submitted
            if employee.user and safe_email(employee.user):
                try:
                    sendemail(
                        "Resignation Submitted",
                        "Your resignation has been submitted.",
                        [employee.user.email]
                    )
                except:
                    # swallow email errors silently (optional: log)
                    pass

            return Response({"message": "Resignation submitted successfully"}, status=status.HTTP_201_CREATED)

        except Employee.DoesNotExist:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------
# 2. MANAGER / HR / BO VIEW RESIGNATION LIST
# ---------------------------------------------------------
class ResignationManagerView(APIView):
    """
    Return list of resignations relevant to the logged-in manager / HR / BO.
    Important: Resignation.rm/hr/bo are User FKs, so compare with request.user (User),
    or with employee.user if comparing an Employee instance.
    """

    def get(self, request):
        try:
            # logged-in user (User instance)
            user = request.user

            # Query resignations where rm/hr/bo equals the logged-in User
            resignation_qs = Resignation.objects.filter(
                Q(rm=user) | Q(hr=user) | Q(bo=user)
            ).order_by("-timestamp")

            serializer = ResignationSerializer(resignation_qs, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------
# 3. HR UPDATES STATUS
# ---------------------------------------------------------
class UpdateResStatusView(APIView):
    """
    HR-only endpoints to fetch and update resignation statuses.
    """

    def get(self, request):
        try:
            # Only show resignations where the logged-in User is HR (Resignation.hr)
            user = request.user
            resignation_qs = Resignation.objects.filter(hr=user).order_by("-timestamp")
            serializer = ResignationSerializer(resignation_qs, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        try:
            user = request.user  # logged-in User
            # if you want to ensure only Employees with HR role can update, check roles here
            resignation_id = request.data.get("id")
            status_value = request.data.get("status")

            if not resignation_id:
                return Response({"error": "id is required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                resignation = Resignation.objects.get(id=resignation_id)
            except Resignation.DoesNotExist:
                return Response({"error": "Resignation not found"}, status=status.HTTP_404_NOT_FOUND)

            # Only HR user assigned to the resignation can update
            # resignation.hr is a User instance; compare with request.user
            if resignation.hr != user:
                return Response({"error": "Not authorized"}, status=status.HTTP_401_UNAUTHORIZED)

            resignation.status = status_value
            # optional: validate status_value is one of allowed choices
            resignation.save()

            # Build recipients directly using User objects (no .user)
            recipients_emails = list(filter(None, [
                safe_email(resignation.rm),
                safe_email(resignation.bo),
                safe_email(resignation.hr),
            ]))

            if recipients_emails:
                sendemail(
                    "Resignation Status Updated",
                    f"Resignation of {resignation.employee.userName} updated to {status_value}",
                    recipients_emails
                )

            # Notify employee (resignation.employee is Employee)
            if resignation.employee and resignation.employee.user and safe_email(resignation.employee.user):
                sendemail(
                    "Resignation Status Updated",
                    f"Your resignation status is updated to: {status_value}",
                    [resignation.employee.user.email]
                )

            return Response({"message": "Status updated successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ResignationDetailView(APIView):
    """
    GET: Retrieve a resignation (optional)
    PUT: Edit resignation by the employee
    DELETE: Delete resignation by the employee
    """
    def get(self, request, pk):
        resignation = get_object_or_404(Resignation, pk=pk)
        # Only the employee who submitted can view
        if resignation.employee.user != request.user:
            return Response({"error": "Not authorized"}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = ResignationSerializer(resignation)
        return Response(serializer.data)

    def put(self, request, pk):
        resignation = get_object_or_404(Resignation, pk=pk)
        # Only employee who submitted can edit
        if resignation.employee.user != request.user:
            return Response({"error": "Not authorized"}, status=status.HTTP_401_UNAUTHORIZED)

        # Allow updating reason, noticeperiodtill, handoverings
        resignation.reason = request.data.get("reason", resignation.reason)
        resignation.noticeperiodtill = request.data.get("noticeperiodtill", resignation.noticeperiodtill)
        resignation.handoverings = request.data.get("handoverings", resignation.handoverings)
        resignation.save()
        serializer = ResignationSerializer(resignation)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        resignation = get_object_or_404(Resignation, pk=pk)
        # Only employee who submitted can delete
        if resignation.employee.user != request.user:
            return Response({"error": "Not authorized"}, status=status.HTTP_401_UNAUTHORIZED)
        resignation.delete()
        return Response({"message": "Resignation deleted successfully"}, status=status.HTTP_200_OK)
