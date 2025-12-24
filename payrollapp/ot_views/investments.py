from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework import status
from ..models import *
from ..decorators import *
from ..serializers import *
from ..tasks import *
from rest_framework.views import APIView
from django.http import HttpResponse
from django.template.loader import render_to_string
from rest_framework.response import Response
from ..utils import *



class getUserForm12BBView(APIView):
    def get(self, request, form_id=None):
        user = request.user
        employee = Employee.objects.get(user=user)
        forms = Form12BB.objects.filter(employee=employee).order_by('-created_at')
        if forms:
            serializer = Form12BBSerializer(forms[0])
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "No form found"}, status=status.HTTP_404_NOT_FOUND)

class Form12BBAPIView(APIView):

    def get(self, request, form_id=None):
        if form_id:
            form = get_object_or_404(Form12BB, id=form_id)
            serializer = Form12BBSerializer(form)
            return Response(serializer.data, status=status.HTTP_200_OK)

        forms = Form12BB.objects.all()
        serializer = Form12BBSerializer(forms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        try:
            data = request.data
            user = request.user
            employee = Employee.objects.get(user=user)
            form_12bb = Form12BB.objects.create(
                employee = employee,
                employee_name=data.get('employee_name'),
                pan=data.get('pan'),
                financial_year=data.get('financial_year'),
                rent_paid=data.get('rent_paid'),
                landlord_name=data.get('landlord_name'),
                landlord_address=data.get('landlord_address'),
                landlord_pan=data.get('landlord_pan'),
                leave_travel_conesssions=data.get('leave_travel_concessions'),
                interest_paid=data.get('interest_paid'),
                lender_name=data.get('lender_name'),
                lender_address=data.get('lender_address'),
                lender_pan=data.get('lender_pan'),
                section_80c=data.get('section_80c'),
                section_80ccc=data.get('section_80ccc'),
                section_80ccd=data.get('section_80ccd'),
                section_80d=data.get('section_80d'),
                section_80e_interest_paid=data.get('section_80e_interest_paid'),
                section_80g_donation_amount=data.get('section_80g_donation_amount'),
                section_80tta_interest_earned=data.get('section_80tta_interest_earned'),
                place=data.get('place'),
                designation=employee.designation.name
            )
            return Response({"message": "Form12BB created successfully", "id": form_12bb.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, form_id):
        form = get_object_or_404(Form12BB, id=form_id)
        try:
            data = request.data
            form.employee_name = data.get('employee_name', form.employee_name)
            form.pan = data.get('pan', form.pan)
            form.financial_year = data.get('financial_year', form.financial_year)
            form.rent_paid = data.get('rent_paid', form.rent_paid)
            form.landlord_name = data.get('landlord_name', form.landlord_name)
            form.landlord_address = data.get('landlord_address', form.landlord_address)
            form.landlord_pan = data.get('landlord_pan', form.landlord_pan)
            form.leave_travel_conesssions = data.get('leave_travel_concessions', form.leave_travel_conesssions)
            form.interest_paid = data.get('interest_paid', form.interest_paid)
            form.lender_name = data.get('lender_name', form.lender_name)
            form.lender_address = data.get('lender_address', form.lender_address)
            form.lender_pan = data.get('lender_pan', form.lender_pan)
            form.section_80c = data.get('section_80c', form.section_80c)
            form.section_80ccc = data.get('section_80ccc', form.section_80ccc)
            form.section_80ccd = data.get('section_80ccd', form.section_80ccd)
            form.section_80d = data.get('section_80d', form.section_80d)
            form.section_80e_interest_paid = data.get('section_80e_interest_paid', form.section_80e_interest_paid)
            form.section_80g_donation_amount = data.get('section_80g_donation_amount', form.section_80g_donation_amount)
            form.section_80tta_interest_earned = data.get('section_80tta_interest_earned', form.section_80tta_interest_earned)
            form.place = data.get('place', form.place)
            form.designation = data.get('designation', form.designation)
            form.save()
            return Response({"message": "Form12BB updated successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class EvidenceAPIView(APIView):
    
    def get(self, request, form_id=None):
        if form_id:
            evidences = Evidence.objects.filter(form_12bb_id=form_id)
            serializer = EvidenceSerializer(evidences, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"error": "Form ID is required"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, form_id):
        form_12bb = get_object_or_404(Form12BB, id=form_id)
        try:
            evidence = Evidence.objects.create(
                form_12bb=form_12bb,
                employee=form_12bb.employee,
                hra=request.FILES.get('hra'),
                leave_travel_consession=request.FILES.get('leave_travel_consession'),
                interest_paid=request.FILES.get('interest_paid'),
                section_80c=request.FILES.get('section_80c'),
                section_80ccc=request.FILES.get('section_80ccc'),
                section_80ccd=request.FILES.get('section_80ccd'),
                section_80d=request.FILES.get('section_80d'),
                section_80e_interest_paid=request.FILES.get('section_80e_interest_paid'),
                section_80g_donation_amount=request.FILES.get('section_80g_donation_amount'),
                section_80tta_interest_earned=request.FILES.get('section_80tta_interest_earned'),
            )
            return Response({"message": "Evidence created successfully", "id": evidence.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

def form_12bb_html(request, form_id):
    try:
        form = Form12BB.objects.get(id=form_id)
        evidences = Evidence.objects.get(form_12bb=form)
    except Form12BB.DoesNotExist:
        return HttpResponse("Form not found", status=404)

    context = {
        'form': form,
        'evidences':evidences
    }
    html = render_to_string('form_12bb.html', context)
    return HttpResponse(html, content_type='text/html')
