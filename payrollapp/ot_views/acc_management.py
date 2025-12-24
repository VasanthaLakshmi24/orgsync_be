from datetime import timedelta,datetime
from django.contrib.auth import authenticate
from rest_framework import status
from ..models import *
from ..decorators import *
from ..serializers import *
from ..tasks import *
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import razorpay
import jwt
import uuid
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse,JsonResponse
from ..utils import *
from dotenv import load_dotenv


load_dotenv()
apiurl=os.environ.get('apiurl')
backendurl=os.environ.get('backendurl')



def verify_email(request, token):
    account = Accounts.objects.get(token=token)
    if account:
        account.is_verified = True
        account.save()        
        return HttpResponse({"Email verified successfully!"})
    else:
        return Response({'message':"Invalid or expired token."})

@api_view(['POST'])
def create_super_user(request):
    if request.method == 'POST':
        password = request.data.get('password')
        email = request.data.get('email')
        if not password or not email:
            return Response({'error': 'Password, and email are required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.create_superuser(email=email, password=password)
            return Response({'message': 'Superuser created successfully.'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AccountDetails(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        user = request.user
        account = Accounts.objects.get(email=user.email)
        data = {
            "features" : account.features,
            "noOfEmployees":account.noOfEmployees,
            "noOfChilds":account.noOfChilds,
            "duration":account.subscriptionDuration,
            "trail":account.hadFreeTrail,
            "amount":int(SubscriptionAmount(int(account.subscriptionDuration),account.noOfEmployees,account.noOfChilds,account.features))
        }
        return Response(data,status=status.HTTP_200_OK)



class AccountRegistrationView(APIView):
    def post(self, request):
        fullName = request.data.get("fullName")
        email = request.data.get("email")
        contactNo = request.data.get("contactNo")
        noOfEmployees = request.data.get("noOfEmployees")
        noOfChilds = request.data.get("noOfChilds")
        feature = request.data.get("feature")
        duration = 1
        password = generate_random_password()
        try:
            account= Accounts.objects.create(fullName=fullName, email=email, contactNo=contactNo,noOfEmployees=noOfEmployees,noOfChilds=noOfChilds,features=feature, subscriptionDuration = duration)
            account.save()
            new_user_name = fullName.replace(" ", "_")
            if(account):
                try:
                    user = User.objects.create_user(
                            username = new_user_name,email=email, password=password, roles='SUPER_USER'
                        )
                    token = str(uuid.uuid4())
                    account.token = token
                    account.save()
                    verification_url =  f"{backendurl}/verify/{token}"
                    context = {
                        'fullName': fullName,
                        'email':account.email,
                        'password':password,
                        'verification_url': verification_url,
                    }
                    sendemailTemplate(
                        'Verify Your Account - Complete Your Registration',
                        'emails/Verification.html',
                        context,
                        [account.email]
                    )
                except Exception as e:
                    user.delete()
                    print(e)
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"message": "Registration successful"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class TokenObtainPairView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request,email=username, password=password)
        is_supuser = False
        if user and user.roles=="SUPER_USER":
            account=Accounts.objects.get(email=user.email)
            is_supuser = True
            if account.is_verified==False:
                return Response({'error':'Account Not verifed.Please verify'},status=status.HTTP_400_BAD_REQUEST)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            message = f"Dear {user.username},\n We are writing to inform you that a successful login has been detected on your account. \n If this login was not authorized by you, please change your password immediately and notify our support team \n. If you have any questions or concerns regarding your account security, please don't hesitate to contact us.\n Best regards,\n GA Org Sync."
            return Response({'access_token': access_token,'issup':is_supuser}, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class VerifyTokenView(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"error": "Token not provided"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return Response({"valid": True, "decoded_token": decoded_token}, status=status.HTTP_200_OK)
        except jwt.ExpiredSignatureError:
            return Response({"error": "Token expired"}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

class create_payment_intent(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self,request):
        user = request.user
        account = Accounts.objects.get(email=user.email)
        amount = int(SubscriptionAmount(int(account.subscriptionDuration),account.noOfEmployees,account.noOfChilds,account.features))
        currency = request.data.get('currency', 'INR')
        client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))
        try:
            payment = client.order.create({'amount': amount, 'currency': currency})
            return JsonResponse({'orderId': payment['id'], 'paymentId': payment['id'], 'amount': payment['amount'], 'currency': payment['currency']})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class OnPaymentSuccess(APIView):
    def post(self,request):
        permission_classes = (IsAuthenticated,)
        user = request.user
        account = Accounts.objects.get(email=user.email)
        paymentId = request.data.get('payment_id')
        client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))
        try:
            payment = client.payment.fetch(paymentId)
            if payment['status'] == 'authorized':
                paymentobj = Payment.objects.create(Account=account,paymentId = paymentId,amount = payment['amount'])
                account.subscriptionStartDate = paymentobj.date
                account.subscriptionEndDate = account.subscriptionStartDate + timedelta(days = account.subscriptionDuration*30)
                account.isSubscribed = True
                account.save()
                return Response({'message':'Subscribtion added successfully'},status=status.HTTP_200_OK)
            else:
                return JsonResponse({'error': 'Invalid payment ID'}, status=status.HTTP_501_NOT_IMPLEMENTED)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class TokenRefreshView(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self, request):
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        return Response({'access_token': access_token}, status=status.HTTP_200_OK)

class GetUserDetails(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        user = request.user
        if 'SUPER_USER' in user.get_roles():
            return Response({'role':["SUPER_USER"]},status=status.HTTP_200_OK)
        roles=[]
        childid=request.data['childid']
        child=ChildAccount.objects.get(id=childid)
        rolesobj=Roles.objects.filter(child=child,user=user)
        for i in rolesobj:
            roles.append(i.name)
        return Response({'role':roles},status=status.HTTP_200_OK)

class IsOrgCreated(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        user = request.user
        accholder = Accounts.objects.get(email=user.email)
        data={}
        if accholder.addedOrganization:
            org = Organization.objects.get(regUser = user)
            data = {
                    'orgname' : org.orgName,
                    'type' : org.type,
                    'regNo' : org.regNo,
                    'companyRegistrationDate' : org.companyRegistrationDate,
                    'contactPerson' : org.contactPerson,
                    'contactNo' : org.contactNo,
                    'email' : org.email,
                    'designation' : org.designation,
                    'companyGstRegNo' : org.companyGstRegNo,
                    'companyPanNo' : org.companyPanNo,
                    'companyTanNo' : org.companyTanNo,
            }
        return Response({'status':accholder.addedOrganization,'data':data},status=status.HTTP_200_OK)

class IsSubscribed(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        user = request.user
        account = Accounts.objects.get(email=user.email)
        return Response({'status':account.isSubscribed,'trail':account.hadFreeTrail,'plan':account.features,'childs':account.noOfChilds,'employees':account.noOfEmployees},status=status.HTTP_200_OK)

class freeTrail(APIView):
    def get(self,request):
        permission_classes = (IsAuthenticated,)
        user = request.user
        account = Accounts.objects.get(email=user.email)
        if account.hadFreeTrail:
            return Response({'error':'Already Taken Free Trail'},status=status.HTTP_400_BAD_REQUEST)
        account.subscriptionStartDate = datetime.now().date()
        account.subscriptionEndDate = account.subscriptionStartDate + timedelta(days = account.subscriptionDuration*30)
        account.isSubscribed = True
        account.hadFreeTrail = True
        account.save()
        return Response({'message':'Subscribtion added successfully'},status=status.HTTP_200_OK)