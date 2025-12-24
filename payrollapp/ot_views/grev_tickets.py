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



class GrievanceHrList(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        employee = Employee.objects.get(user = user)
        childid = request.data.get('childid')
        if childid:
            child = ChildAccount.objects.get(id = childid)
            grievances = Grievance.objects.filter(parent = employee.parent,child = child)
        else:
            grievances = Grievance.objects.filter(parent = employee.parent)
        serializer = GrievanceSerializer(grievances, many=True)
        return Response(serializer.data)

class GrievanceListCreate(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        grievances = Grievance.objects.filter(sender = user)
        serializer = GrievanceSerializer(grievances, many=True)
        return Response(serializer.data)
    def post(self, request):
        user = request.user
        employee = Employee.objects.get(user = user)
        parent = employee.parent
        childid = request.data.get('childid')
        if childid:
            child = ChildAccount.objects.get(id = childid)
            hr = Roles.objects.get(parent = parent,child = child,name = "HR_HEAD").user
        else:
            child = None
            hr = Roles.objects.get(parent = parent,name = "HR_HEAD").user
        title = request.data.get('title')
        description = request.data.get('description')
        is_anon = request.data.get('is_anon') or False
        sender = user
        try:
            Grievance.objects.create(parent = parent, child = child, title = title, description = description, sender = sender,is_anon=is_anon)
            message = f"Dear {hr.username},\nWe hope this message finds you well.\nWe are writing to notify you that a new grievance request has been received. Your attention and action are required to address this matter promptly.\nPlease log in to your account and navigate to the dashboard to review the details of the grievance request. Your timely response and resolution are highly appreciated.\nIf you have any questions or need assistance, feel free to reach out to our support team for guidance.\nThank you for your cooperation in maintaining a positive work environment.\nBest regards,\nGA Org Sync."
            Notification.objects.create(sender = user,receiver = hr,message=message)
            try:
                sendemail(
                    'New Grievance Request - Action Required',
                    message,
                    [hr.email],
                )
            except:
                pass
            return Response({'message': "Grivance submitted Successfully."}, status=status.HTTP_201_CREATED)
        except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class GrievanceDetail(APIView):
    def get(self, request, pk):
        try:
            grievance = Grievance.objects.get(pk=pk)
            serializer = GrievanceSerializer(grievance)
            return Response(serializer.data)
        except Grievance.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    def put(self, request, pk):
        try:
            grievance = Grievance.objects.get(pk=pk)
            serializer = GrievanceSerializer(grievance, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Grievance.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

class GrievanceCommentListCreate(APIView):
    def get(self, request, grievance_id):
        comments = GrievanceComment.objects.filter(grievance_id=grievance_id)
        serializer = GrievanceCommentSerializer(comments, many=True)
        return Response(serializer.data)
    def post(self, request, grievance_id):
        user = request.user
        grievance = Grievance.objects.get(id = grievance_id)
        sender = user
        comment = request.data.get("comment")
        try:
            GrievanceComment.objects.create(sender = sender,comment = comment,grievance=grievance)
            return Response({'message': "Grivance submitted Successfully."}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class GrievanceCommentDetail(APIView):
    def get(self, request, pk):
        user = request.user
        try:
            comment = GrievanceComment.objects.get(pk=pk)
            serializer = GrievanceCommentSerializer(comment)
            return Response(serializer.data)
        except GrievanceComment.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

class TicketListCreate(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        tickets= Ticket.objects.filter(sender = user)
        serializer =TicketSerializer(tickets, many=True)
        return Response(serializer.data)
    def post(self, request):
        user = request.user
        employee = Employee.objects.get(user = user)
        parent = employee.parent
        childid = request.data.get('childid')
        if childid:
            child = ChildAccount.objects.get(id = childid)
            hr = Roles.objects.get(parent = parent,child = child,name = "HR_HEAD").user
        else:
            child = None
            hr = Roles.objects.get(parent = parent,name = "HR_HEAD").user
        issue = request.data.get('issue')
        description = request.data.get('description')
        sender = user
        try:
            Ticket.objects.create(parent = parent, child = child, issue=issue, description = description, sender = sender)
            message = f"We are writing to inform you that a new ticket has been created. Please take the necessary action as soon as possible.\nPlease log in to your account and navigate to the ticketing system to view and address this ticket promptly."
            Notification.objects.create(sender = user,receiver = hr,message=message)
            try:
                sendemail(
                    'New Ticket Created - Action Required',
                    message,
                    [hr.email],
                )
            except:
                pass
            return Response({'message': "Tikcet submitted Successfully."}, status=status.HTTP_201_CREATED)
        except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class TicketHrList(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        employee = Employee.objects.get(user = user)
        childid = request.data.get('childid')
        if childid:
            child = ChildAccount.objects.get(id = childid)
            tickets = Ticket.objects.filter(parent = employee.parent,child = child)
        else:
            tickets = Ticket.objects.filter(parent = employee.parent)
        serializer = TicketSerializer(tickets, many=True)
        return Response(serializer.data)

class TicketCommentDetail(APIView):
    def get(self, request, pk):
        user = request.user
        try:
            comment = TicketComment.objects.get(pk=pk)
            serializer =TicketCommentSerializer(comment)
            return Response(serializer.data)
        except TicketComment.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

class TicketCommentListCreate(APIView):
    def get(self, request, ticket_id):
        comments = TicketComment.objects.filter(ticket_id=ticket_id)
        serializer = TicketCommentSerializer(comments, many=True)
        return Response(serializer.data)
    def post(self, request, ticket_id):
        user = request.user
        ticket = Ticket.objects.get(id = ticket_id)
        sender = user
        comment = request.data.get("comment")
        try:
            TicketComment.objects.create(sender = sender,comment = comment,ticket=ticket)
            return Response({'message': "Ticket submitted Successfully."}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class TicketDetail(APIView):
    def get(self, request, pk):
        try:
            ticket = Ticket.objects.get(pk=pk)
            serializer = TicketSerializer(ticket)
            return Response(serializer.data)
        except Ticket.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    def put(self, request, pk):
        try:
            ticket =Ticket.objects.get(pk=pk)
            serializer =TicketSerializer(ticket, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Grievance.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

