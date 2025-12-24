import random
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.shortcuts import get_object_or_404
from datetime import datetime,timedelta
from rest_framework.decorators import api_view
from django.http import JsonResponse,HttpResponse
from django.contrib.auth import authenticate
from rest_framework import status
from ..models import *
from ..decorators import *
from ..serializers import *
from ..tasks import *
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
import pytz
from django.db.models import Max,Value
from django.db.models.functions import Coalesce
import uuid
from rest_framework.response import Response
from django.db.models import Sum
from django.shortcuts import render
from django.db.models import Q
from io import BytesIO
from ..utils import *




class CreateConversationView(APIView):
    """API View to create a new one-to-one conversation"""
    permission_classes = [IsAuthenticated]  

    def post(self, request):
        user = request.user
        employee = Employee.objects.get(user = user)
        participant_2_id = request.data.get('participant_2')

        if employee.id == participant_2_id:
            return Response({"error": "A conversation cannot be created between the same participant."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee_1 = employee
            employee_2 = get_object_or_404(Employee, id=participant_2_id)

            
            existing_conversation = Conversation.objects.filter(
                participants__employee=employee_1
            ).filter(participants__employee=employee_2).first()

            if existing_conversation:
                return Response({'conversation_id': existing_conversation.id, 'status': 'exists'})

            
            conversation = Conversation.objects.create()

            
            Participant.objects.create(conversation=conversation, employee=employee_1)
            Participant.objects.create(conversation=conversation, employee=employee_2)

            return Response({'id': conversation.id, 'status': 'created'}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RecentConversationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            employee = Employee.objects.get(user=user)

            participant_conversations = Participant.objects.filter(employee=employee).values('conversation')
            fallback_datetime = timezone.datetime(1970, 1, 1)
            conversations = (
                Conversation.objects.filter(id__in=participant_conversations)  
                .prefetch_related('participants')  
                .annotate(
                    latest_message_time=Coalesce(Max('messages__timestampp'), Value(fallback_datetime))
                )
                .order_by('-latest_message_time')  
            )
            conversations_list = list(conversations)
            
            
            

            
            

            conversations = conversations_list

            response_data = []

            for conversation in conversations:
                participants = conversation.participants.exclude(employee=employee)
                participant_data = [
                    {'id': p.employee.id, 'userName': p.employee.userName}
                    for p in participants
                ]
                
                

                latest_message = Message.objects.filter(conversation=conversation).order_by('-timestampp').first()
                
                if latest_message:
                    if employee == latest_message.sender:
                        is_seen = True
                    else:
                        is_seen = conversation.is_seen
                else:
                    is_seen = True

                response_data.append({
                    'id': conversation.id,
                    'is_seen':is_seen,
                    'participants': participant_data,  
                    'last_message': latest_message.content if latest_message else None,
                    'last_message_time': latest_message.timestampp if latest_message else None,
                })

            return Response(response_data, status=200)

        except Employee.DoesNotExist:
            return Response({"error": "Employee not found for the current user."}, status=404)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

class SendMessageView(APIView):
    """API View to send a message in a one-to-one conversation"""
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        message_content = request.data.get('message')

        try:
            conversation = get_object_or_404(Conversation, id=conversation_id)
            user = request.user
            sender = Employee.objects.get(user = user)

            ist = pytz.timezone('Asia/Kolkata')
            now_utc = timezone.now()

            if not conversation.is_valid_participant(sender):
                return Response({"error": "You are not a participant in this conversation."}, status=status.HTTP_403_FORBIDDEN)

            message = Message.objects.create(
                conversation=conversation,
                sender=sender,
                content=message_content,
                timestampp = now_utc.astimezone(ist)
            )
            
            print(conversation.is_seen)
            
            conversation.is_seen = False
            conversation.save()
            
            print(conversation.is_seen)

            participants = conversation.participants.exclude(id=sender.id)
            subject = 'New Message Notification'
            for recipient in participants:
                mail_msg = f'Hi { recipient.employee.userName },\n\nYou have received a new message from { sender.userName }.\nPlease Visit Chat in orgsync to view more.'


            return Response({'message_id': message.id, 'status': 'sent'}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetConversationMessagesView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, conversation_id):
        try:
            conversation = get_object_or_404(Conversation, id=conversation_id)
            user = request.user
            employee = Employee.objects.get(user=user)

            if not conversation.is_valid_participant(employee):
                return Response({"error": "You are not authorized to view messages in this conversation."}, status=status.HTTP_403_FORBIDDEN)
            messages = conversation.messages.all().order_by('timestampp')
            lastmsg = conversation.messages.all().order_by('-timestampp').first()
            if lastmsg.sender != employee:
                conversation.is_seen = True
                conversation.save()
            response_data = []
            for message in messages:
                response_data.append({
                    'sender': message.sender.userName,
                    'content': message.content,
                    'timestamp': message.timestampp
                })
                
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UnreadConversationsCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            employee = Employee.objects.get(user=user)

            participant_conversations = Participant.objects.filter(employee=employee).values('conversation')

            conversations = (
                Conversation.objects.filter(id__in=participant_conversations)  
                .prefetch_related('participants')  
                .annotate(latest_message_time=Max('messages__timestampp'))  
                .order_by('latest_message_time')  
            )
            conversations_list = list(conversations)

            if len(conversations_list) > 2:
                conversations_list[0], conversations_list[1] = conversations_list[1], conversations_list[0]

            conversations = conversations_list
            is_seen_count = 0

            for conversation in conversations:
                latest_message = Message.objects.filter(conversation=conversation).order_by('-timestampp').first()
                
                if latest_message:
                    if employee != latest_message.sender:
                        if not conversation.is_seen:
                            is_seen_count += 1
            return Response({'count' : is_seen_count}, status=200)

        except Employee.DoesNotExist:
            return Response({"error": "Employee not found for the current user."}, status=404)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

