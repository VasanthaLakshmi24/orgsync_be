from django.dispatch import receiver
from django.db import models
from .manager import *
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager,Permission,Group
from django.db import models
from django.db.models.signals import post_delete, post_save , pre_save
from datetime import datetime
import calendar
from django.utils.text import slugify
from cryptography.fernet import Fernet
from django.conf import settings
import string 
import random
from zoneinfo import ZoneInfo
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import base64
import os
from django.utils import timezone

 

class CustomUserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    roles = models.CharField(max_length=200,blank=True, null=True, default='EMPLOYEE')
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        related_name='custom_user_permissions', 
    )
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        related_name='custom_user_groups',
    )
    objects = CustomUserManager()

    def set_roles(self, roles):
        self.roles = ','.join(roles)

    def get_roles(self):
        if self.roles:
            return self.roles.split(',')[0]
        else:
            return []

    def __str__(self):
        return self.email

class Accounts(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fullName = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    contactNo = models.CharField(max_length=12)
    noOfEmployees = models.IntegerField()
    noOfChilds = models.IntegerField()
    features = models.CharField(max_length=20)
    addedOrganization = models.BooleanField(default=False)
    isSubscribed = models.BooleanField(default=False)
    hadFreeTrail = models.BooleanField(default=False)
    token=models.CharField(max_length=100, null=True, blank=True)
    is_verified=models.BooleanField(default=False)
    subscriptionStartDate = models.DateField(null=True, blank=True)
    subscriptionDuration = models.IntegerField(null=True, blank=True)
    subscriptionEndDate = models.DateField(null=True, blank=True)
    subscriptionStatus = models.CharField(max_length=20, choices=[('active', 'Active'), ('inactive', 'Inactive')], default='inactive')
    def save(self, *args, **kwargs):
        if self.subscriptionEndDate and self.subscriptionEndDate >= datetime.now(tz=ZoneInfo("Asia/Kolkata")).date():
            self.subscriptionStatus = 'active'
        else:
            self.subscriptionStatus = 'inactive'
        super().save(*args, **kwargs)
    def __str__(self):
        return self.fullName

class Payment(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    Account = models.ForeignKey(Accounts,on_delete = models.SET_NULL,null=True,blank=True)
    paymentId = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)

class Organization(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    orgName = models.CharField(max_length=50)
    logo = models.ImageField(upload_to='OrgLogos', null=True, blank=True)
    Account = models.ForeignKey(Accounts,on_delete= models.CASCADE)
    regUser = models.ForeignKey(User,on_delete=models.CASCADE)
    address=models.CharField(max_length=200)
    type = models.CharField(max_length=20,choices=(
        ('proprietorship','Proprietorship'),
        ('partnershipFirm','Partnership Firm'),
        ('llc','LLC'),
        ('Pvt.Ltdcompany','Pvt. Ltd company'),
    ))
    regNo = models.CharField(max_length=25)
    companyRegistrationDate = models.DateField()
    contactPerson = models.CharField(max_length=50)
    contactNo = models.CharField(max_length=12)
    email = models.CharField(max_length = 50)
    designation = models.CharField(max_length=20)
    companyGstRegNo = models.CharField(max_length=15)
    companyPanNo = models.CharField(max_length = 10)
    companyTanNo = models.CharField(max_length = 10)
    timestamp = models.DateTimeField(auto_now_add=True)
    quote=models.TextField(max_length=50000000,null=True, blank=True)
    def __str__(self):
        return self.orgName

    def save(self, *args, **kwargs):
        try:
            this = Organization.objects.get(id=self.id)
            if this.image != self.image:
                this.image.delete(save=False)
        except:
            pass
        super(Organization, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.image.delete(save=False)
        super(Organization, self).delete(*args, **kwargs)

class ChildAccount(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    parent=models.ForeignKey(Organization,on_delete=models.CASCADE)
    name=models.CharField(max_length=30)
    regNo=models.CharField(max_length=25)
    contactPerson=models.CharField(max_length=30)
    designation=models.CharField(max_length=30)
    contactNo=models.CharField(max_length=12)
    email=models.CharField(max_length=40)
    companyGstRegNo = models.CharField(max_length=20,null=True,blank=True)
    companyPanNo = models.CharField(max_length = 10,null=True,blank=True)
    companyTanNo = models.CharField(max_length = 10,null=True,blank=True)
    bussinessOwner = models.ForeignKey(User,on_delete= models.SET_NULL,null=True,blank=True,related_name="BUSINESS_OWNER")
    HrHead = models.ForeignKey(User,on_delete= models.SET_NULL,null=True,blank=True,related_name="hr_head")
    attendanceType = models.CharField(max_length=15, choices=(
        ('bulkupload', 'Bulk Upload'),
        ('punch', 'Punch In and Out'),
    ),default = 'punch')
    PFType = models.CharField(max_length=15, choices=(
        ('fixed', 'Fixed'),
        ('slab', 'Slab'),
    ),default = 'fixed')
    acc_type = models.CharField(max_length=15, choices=(
        ('In House', 'In House'),
        ('Third Party', 'Third Party'),
    ),default = 'In House')
    iprestriction=models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Roles(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(
        ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(User,on_delete = models.SET_NULL, blank=True, null=True,related_name = "assigned_user")
    def __str__(self):
        return self.name

class RoleRequests(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(User, on_delete = models.CASCADE,related_name='role_sender')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE,related_name='role_receiver')
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    role = models.CharField(max_length = 50)
    user = models.ForeignKey(User,on_delete = models.SET_NULL, blank=True, null=True,related_name = "role_user")
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=(
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('underreview', 'Under Review'),
    ),default = 'underreview')

class OrgStructureApprovals(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(User, on_delete = models.CASCADE,related_name='org_sender')
    
    receiver = models.ForeignKey(User, on_delete=models.CASCADE,related_name='org_receiver')
    type = models.CharField(max_length=15, choices=(
        ('roles', 'Roles'),
        ('departments', 'Departments'),
        ('designations', 'Designations'),
    ))
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    roles = models.TextField(blank=True, null=True)
    departments = models.TextField(blank=True, null=True)
    designations = models.TextField(blank=True, null=True)
    
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=(
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('underreview', 'Under Review'),
    ),default = 'underreview')

    def get_roles(self):
        if self.roles:
            return self.roles.split(',')
        else:
            return []
    def set_roles(self, roles):
        self.roles = ','.join(roles)

    def get_departments(self):
        if self.departments:
            return self.departments.split(',')
        else:
            return []
    def set_departments(self, departments):
        self.departments = ','.join(departments)

    def get_designations(self):
        if self.designations:
            return self.designations.split(',')
        else:
            return []
    def set_designations(self, designations):
        self.designations = ','.join(designations)

class Employee(models.Model):
    employeeid=models.CharField(null=True,blank=True,max_length=15)
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User,on_delete=models.SET_NULL,blank=True,null=True)
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ManyToManyField(ChildAccount,blank=True,null=True,related_name="child")
    main_child = models.ForeignKey(ChildAccount,blank=True,null=True,on_delete=models.CASCADE,related_name="main_child")
    roles=models.ManyToManyField(Roles,blank=True, related_name="employees")

    dateOfBirth=models.DateField(null=True,blank=True)
    designation = models.ForeignKey(
        'Designation', on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(
        'Department', on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=15, choices=(
        ('part_time', 'Part Time'),
        ('full_time', 'Full Time'),
        ('contract', 'Contract'),
        ('other', 'Other'),
    ))
    emp_type = models.CharField(max_length=15, choices=(
        ('Blue-Collar', 'Blue-Collar'), 
        ('White-Collar', 'White-Collar'),
        ),default='White-Collar')
    labour_category = models.CharField(max_length=15,null=True,blank=True)
    gender = models.CharField(max_length=6, choices=(
        ('male', 'Male'), 
        ('female', 'Female'),
        ('other', 'Other'),))
    userName=models.CharField(max_length=50)
    email=models.CharField(max_length=50,unique=True,null=True,blank=True)
    phoneNumber=models.CharField(max_length=12,null=True,blank=True)
    status = models.CharField(max_length=15, choices=(
        ('onroll', 'Onroll'), 
        ('exit', 'exit'),
        ('prejoining', 'prejoining'),
        ),default='onroll')
    reported_to = models.ForeignKey(User,on_delete= models.SET_NULL,null=True,blank=True,related_name="REPORTING_MANAGER")
    dateOfJoining=models.DateField(null=True,blank=True)
    ctc=models.DecimalField(max_digits=15, decimal_places=2,null=True,blank=True)
    jobdescription=models.TextField(max_length=50000,null=True, blank=True)
    kras=models.TextField(max_length=50000,null=True, blank=True)
    careerpath=models.TextField(max_length=50000,null=True, blank=True)

    def __str__(self):
        return self.userName

class Allowance(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount,blank=True,null=True,related_name="allo_child",on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    min_value = models.DecimalField(max_digits=4,decimal_places=2,null=True,blank=True,default=0)

    def __str__(self):
        return self.name

class EmployeeAllowance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="employee_allowances")
    allowance = models.ForeignKey(Allowance, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.allowance.name} - {self.amount}"

class ProductionAllowance(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount,blank=True,null=True,related_name="proallo_chi",on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    min_value = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)
    max_value = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)
    type = models.CharField(max_length=25,choices=[('allowance', 'Allowance'), ('deduction', 'Deduction')])

    def __str__(self):
        return self.name

class EmployeeProdAllowance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="prod_employee_allowances")
    allowance = models.ForeignKey(ProductionAllowance, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.allowance.name} - {self.amount}"


class EmployeePay(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="employee_pays")
    ctc=models.DecimalField(max_digits=15, decimal_places=2)
    gross=models.DecimalField(max_digits=15, decimal_places=2)
    basic=models.DecimalField(max_digits=15, decimal_places=2)
    employer_pf = models.DecimalField(max_digits=15,decimal_places=2)
    employer_esi = models.DecimalField(max_digits=15,decimal_places=2)

    def __str__(self):
        return self.employee.userName

class ProdEmployeePay(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="prod_employee_pays")
    per_day_wage = models.DecimalField(max_digits=15, decimal_places=2)
    employer_pf = models.DecimalField(max_digits=15,decimal_places=2)
    employee_pf = models.DecimalField(max_digits=15,decimal_places=2)
    employer_esi = models.DecimalField(max_digits=15,decimal_places=2)
    employee_esi = models.DecimalField(max_digits=15,decimal_places=2)

    def __str__(self):
        return self.employee.userName

class IPExceptions(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL,null=True,blank=True)
    addedby = models.ForeignKey(User, on_delete = models.SET_NULL,null = True,blank = True)
    timestamp = models.DateTimeField(auto_now_add=True)

@receiver(post_delete, sender='payrollapp.Employee')
def delete_employee_user(sender, instance, **kwargs):
    try:
        user = User.objects.get(email=instance.email)
        user.delete()
    except User.DoesNotExist:
        pass

@receiver(pre_save, sender='payrollapp.Employee')
def update_user(sender, instance, **kwargs):
    if instance.status == 'exit':
        user_instance.delete()
    if instance.user:
        user_instance = instance.user
        user_instance.email = instance.email  
        user_instance.save()
    else:
        pass

class Notification(models.Model):
    sender = models.ForeignKey(User, on_delete = models.CASCADE,related_name='sender')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE,related_name='receiver')
    message = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

class Department(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    child=models.ForeignKey(ChildAccount,on_delete=models.CASCADE,blank=True,null=True)
    parent=models.ForeignKey(Organization,on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Designation(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    child=models.ForeignKey(ChildAccount,on_delete=models.CASCADE,blank=True,null=True,related_name = 'des_child')
    parent=models.ForeignKey(Organization,on_delete=models.CASCADE,related_name = 'des_parent')
    
    def __str__(self):
        return self.name

class Log(models.Model):
    loginby = models.ForeignKey(Employee, on_delete=models.SET_NULL,null=True,blank=True,related_name="LoginBy")
    log_in = models.DateTimeField()
    log_out = models.DateTimeField()
    employee_Id_on_whom_modification_done = models.ForeignKey(Employee, on_delete=models.SET_NULL,null=True,blank=True)
    Child_ID = models.ForeignKey(ChildAccount, on_delete=models.SET_NULL,null=True,blank=True)
    reason = models.CharField(max_length=50)
    modification_before = models.TextField()
    modification_after = models.TextField()
    Parent_ID = models.ForeignKey(Organization, on_delete=models.CASCADE)

class Policy(models.Model):
    Policy_name = models.CharField(max_length=50)
    Policy_sub_title = models.CharField(max_length=50)
    overview = models.TextField(null=True,blank=True)
    No_of_days_per_month = models.IntegerField()
    no_of_sick_levaes = models.IntegerField()
    no_of_maternity_leaves = models.IntegerField()
    no_of_paternity_leaves = models.IntegerField()
    no_of_bereavement_leaves = models.IntegerField()
    no_of_privilege_leaves = models.IntegerField()
    no_of_casual_leaves = models.IntegerField()
    actual_sign_in_time = models.TimeField()
    compensation_off = models.IntegerField()
    number_of_work_hours_per_week = models.IntegerField()
    overtime_pay = models.IntegerField()
    No_of_work_days_per_week = models.IntegerField()
    total_no_of_leaves = models.IntegerField()
    Parent_ID = models.ForeignKey(Organization, on_delete=models.CASCADE)
    Child_ID=models.ForeignKey(ChildAccount,on_delete=models.CASCADE,blank=True,null=True)

class Holidays(models.Model):
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=255)
    date = models.DateField()

class OptionalHolidays(models.Model):
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=255)
    date = models.DateField()

class OptionalHolidaysPolicy(models.Model):
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    opt_holidays_allowed=models.IntegerField(default=0)

class EmployeeOptHoliday(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    holiday = models.ForeignKey(OptionalHolidays, on_delete=models.CASCADE,null=True,blank=True)
    workDelegated = models.ForeignKey(Employee, on_delete=models.SET_NULL,null=True, blank=True,related_name='workDelegated')
    comments = models.TextField(null=True, blank=True)
    reason=models.TextField(null = True, blank = True)
    timestamp=models.DateField(auto_now_add=True)

class AssetsOwnedByOrganisation(models.Model):
    ParentID = models.ForeignKey(Organization, on_delete=models.CASCADE)
    Child_ID=models.ForeignKey(ChildAccount,on_delete=models.CASCADE,blank=True,null=True)
    asset_type = models.CharField(max_length=20)
    asset_serial_number = models.CharField(max_length=20)
    
    def __str__(self):
        return self.asset_type

class EmployeeBasicDetails(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    firstName=models.CharField(max_length=100,null=True,blank=True)
    lastName=models.CharField(max_length=100,null=True,blank=True)
    middleName=models.CharField(max_length=100,null=True,blank=True)
    contactNumber = models.CharField(max_length=20, null=True, blank=True)             
    emergencyContactNumber = models.CharField(max_length=20, null=True, blank=True)    
    communicationAddress=models.TextField(null=True,blank=True)
    permanentAddress=models.TextField(null=True,blank=True)
    aadharNumber=models.CharField(max_length = 12,null=True,blank=True)
    panCardNumber=models.CharField(max_length = 10,null=True,blank=True)
    bloodGroup=models.CharField(max_length=10,null=True,blank=True)
    healthIssues=models.TextField(null=True,blank=True)
    pfAccountNumber=models.CharField(max_length=22,null=True,blank=True)
    gratuityNumber=models.CharField(max_length=22,null=True,blank=True)
    esiAccountNumber=models.CharField(max_length=17,null=True,blank=True)
    healthInsuranceNumber=models.CharField(max_length=14,null=True,blank=True)
    is_editable = models.BooleanField(default=False)

class EmployeeBankDetails(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    bankName=models.CharField(max_length=100,null=True,blank=True)
    ifsc=models.CharField(max_length=100,null=True,blank=True)
    bankAcNo=models.CharField(max_length=100,null=True,blank=True)
class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    profile = models.ImageField(upload_to='Profiles', null=True, blank=True)
    aadhar = models.FileField(upload_to='Aadhaars', null=True, blank=True)
    panCard = models.FileField(upload_to='PanCards', null=True, blank=True)
    offerLetter = models.FileField(upload_to='OfferLetters', null=True, blank=True)
    pfdeclaration = models.FileField(upload_to='pfDeclaration', null=True, blank=True)
    esi_card = models.FileField(upload_to='esi_cards/', null=True, blank=True)  # NEW FIELD
    # document_name = models.CharField(max_length=100)


    def __str__(self):
        return f"Document for {self.employee}"

    def save(self, *args, **kwargs):
        try:
            this = Document.objects.get(id=self.id)

            if this.profile != self.profile:
                this.profile.delete(save=False)

            if this.aadhar != self.aadhar:
                this.aadhar.delete(save=False)

            if this.panCard != self.panCard:
                this.panCard.delete(save=False)

            if this.offerLetter != self.offerLetter:
                this.offerLetter.delete(save=False)

            if this.pfdeclaration != self.pfdeclaration:
                this.pfdeclaration.delete(save=False)

            if this.esi_card != self.esi_card:      # NEW CLEANUP
                this.esi_card.delete(save=False)

        except Document.DoesNotExist:
            pass

        super(Document, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.profile.delete(save=False)
        self.aadhar.delete(save=False)
        self.panCard.delete(save=False)
        self.offerLetter.delete(save=False)
        self.pfdeclaration.delete(save=False)
        self.esi_card.delete(save=False)           
        super(Document, self).delete(*args, **kwargs)

class EmployeeRelation(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    relationName = models.CharField(max_length=100,null=True,blank=True)
    relationType = models.CharField(max_length=20,null=True,blank=True)
    relationAge = models.CharField(max_length=3,null=True,blank=True)
    relationContact = models.CharField(max_length=15,null=True,blank=True)
    relationAadhar = models.CharField(max_length=15,null=True,blank=True)
    is_editable = models.BooleanField(default=False)
class EmployeeEducationDetails(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)    
    institution = models.CharField(max_length=100)
    degree = models.CharField(max_length=20)
    field_of_study = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    # education_proof = models.ImageField(upload_to='EducationProof', null=True, blank=True)
    education_proof = models.FileField(upload_to='education/', null=True, blank=True)

    is_editable = models.BooleanField(default=False)
    

    def __str__(self):
        return f"{self.degree} in {self.field_of_study} from {self.institution}"
    def save(self, *args, **kwargs):
        try:
            this = EmployeeEducationDetails.objects.get(id=self.id)
            if this.education_proof != self.education_proof:
                this.education_proof.delete(save=False)
        except:
            pass
        super(EmployeeEducationDetails, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.education_proof.delete(save=False)
        super(EmployeeEducationDetails, self).delete(*args, **kwargs)


class EmployeeExperience(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey("Employee", on_delete=models.CASCADE)

    # Main Experience Fields
    worked_from = models.DateField(null=True, blank=True)
    worked_to = models.DateField(null=True, blank=True)
    designation = models.CharField(max_length=100, null=True, blank=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    organization = models.CharField(max_length=50, null=True, blank=True)

    # New fields (requested by you)
    previous_positions = models.TextField(blank=True, null=True)
    promotions = models.TextField(blank=True, null=True)
    transfers = models.TextField(blank=True, null=True)
    role_changes = models.TextField(blank=True, null=True)

    # Documents
    relieving_letter = models.ImageField(upload_to='RelievingLetterImages', null=True, blank=True)
    payslip_1 = models.ImageField(upload_to='Payslips', null=True, blank=True)
    payslip_2 = models.ImageField(upload_to='Payslips', null=True, blank=True)
    payslip_3 = models.ImageField(upload_to='Payslips', null=True, blank=True)

    # Other fields
    reason_for_resign = models.CharField(max_length=100, null=True, blank=True)
    is_editable = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)


    # ------- File Handling Logic -------
    def save(self, *args, **kwargs):
        try:
            old_obj = EmployeeExperience.objects.get(id=self.id)

            # Delete replaced files
            if old_obj.relieving_letter and old_obj.relieving_letter != self.relieving_letter:
                old_obj.relieving_letter.delete(save=False)
            if old_obj.payslip_1 and old_obj.payslip_1 != self.payslip_1:
                old_obj.payslip_1.delete(save=False)
            if old_obj.payslip_2 and old_obj.payslip_2 != self.payslip_2:
                old_obj.payslip_2.delete(save=False)
            if old_obj.payslip_3 and old_obj.payslip_3 != self.payslip_3:
                old_obj.payslip_3.delete(save=False)

        except EmployeeExperience.DoesNotExist:
            pass

        super(EmployeeExperience, self).save(*args, **kwargs)

    # Delete all files on deletion
    def delete(self, *args, **kwargs):
        if self.relieving_letter:
            self.relieving_letter.delete(save=False)
        if self.payslip_1:
            self.payslip_1.delete(save=False)
        if self.payslip_2:
            self.payslip_2.delete(save=False)
        if self.payslip_3:
            self.payslip_3.delete(save=False)

        super(EmployeeExperience, self).delete(*args, **kwargs)

    def __str__(self):
        return f"{self.organization} - {self.designation}"
        

class EmployeeReference(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    Organization_name = models.CharField(max_length=20,null=True,blank=True)
    Designation = models.CharField(max_length=20,null=True,blank=True)
    Department_name = models.CharField(max_length=20,null=True,blank=True)
    Contact_no = models.IntegerField(null=True,blank=True)
    Emial_ID = models.CharField(max_length=50,null=True,blank=True)
    is_editable = models.BooleanField(default=False)


class Attendance(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    child=models.ForeignKey(ChildAccount,on_delete=models.CASCADE,blank=True,null=True)
    parent=models.ForeignKey(Organization,on_delete=models.CASCADE,blank=True,null=True)
    date = models.DateField()
    time_in = models.TimeField(null=True,blank=True)
    time_out = models.TimeField(null=True,blank=True)
    net_time_in =  models.CharField(max_length=10,null=True,blank=True)
    logged_in = models.BooleanField(default=True)
    net_break = models.CharField(max_length=10,null=True,blank=True)
    is_editable = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=[(
        'present', 'Present'), ('latelogin', 'Late Login'),('halfday','Half Day'),('absent','Absent'),('leave','Leave'),('holiday','Holiday')],default='present')

@receiver(post_save,sender='payrollapp.Employee')
def create_null_objects(sender,instance,created,**kwargs):
    if created:
        EmployeeBasicDetails.objects.create(employee =instance)
        EmployeeReference.objects.create(employee = instance)
        Document.objects.create(employee = instance)
        EmployeeBankDetails.objects.create(employee=instance)

class leaves(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE , related_name='employee')
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    fromDate = models.DateField()
    toDate = models.DateField()
    timeStamp = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=20)
    workDelegated =  models.ForeignKey(Employee, on_delete=models.SET_NULL,null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[(
        'pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'),('cancelled', 'Cancelled')],default='pending')
    commentsonstatuschange = models.TextField(null = True,blank= True)
    durationn = models.DecimalField(decimal_places=2, default=0, max_digits=4)
    leavetype= models.CharField(max_length=20, choices=[(
        'halfday', 'Halfday'), ('fullday', 'Fullday'), ],default='fullday')

    approvingPerson = models.ForeignKey(User, on_delete=models.SET_NULL,null=True, blank=True)
    approvedTimestamp = models.DateField(null = True, blank = True)
    reason=models.TextField(null = True, blank = True)

class LeavePolicy(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    sickLeaves = models.IntegerField()
    casualLeaves = models.IntegerField()
    maternityLeaves = models.IntegerField()
    leaves_per_year = models.IntegerField()
    privilege_leaves = models.IntegerField()
    paternity_leaves = models.IntegerField()
    bereavement_leaves = models.IntegerField()
    framedBy = models.ForeignKey(User,on_delete = models.SET_NULL, blank=True, null=True)
    leaveForwarding = models.BooleanField(default=False)
    autoApproval = models.BooleanField(default=False)
    autoApprovalBefore = models.IntegerField(null=True,blank=True)
    leaveForwardAfter = models.IntegerField(null=True,blank=True)
    leaveForwardingUpto = models.CharField(max_length=20,choices=(
        ('HR', 'HR'),
        ('Business Owner', 'Business Owner'),
        ('Reporting Manager', 'Reporting Manager'),
    ),null=True,blank=True)

class LeaveApprovalFlow(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    days = models.IntegerField()
    level = models.IntegerField()
    approvingPerson = models.CharField(max_length=20,choices=(
        ('HR', 'HR'),
        ('Reporting Manager', 'Reporting Manager'),
    ),default = 'HR')


class LeaveBalance(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE , related_name='employee_lb')
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    carry_forwarded_leave_balance = models.DecimalField(max_digits=4, decimal_places=2,default=0)
    current_leave_balance = models.DecimalField(max_digits=4, decimal_places=2,default=0)
    month=models.IntegerField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    advance=models.IntegerField(default=0)
    bonus=models.IntegerField(default=0)
    lop=models.IntegerField(default=0)

class PayrollPolicy(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    payslipHeaderCompany = models.CharField(max_length=255)
    payslipHeadertagline = models.CharField(max_length=255,null=True,blank=True)
    payslipHeaderAddress = models.CharField(max_length=255)
    payslipHeaderlogo = models.ImageField(upload_to='payslipheaderlogo', null=True, blank=True)
    
    def save(self, *args, **kwargs):
        try:
            this = PayrollPolicy.objects.get(id=self.id)
            if this.payslipHeaderlogo != self.payslipHeaderlogo:
                this.payslipHeaderlogo.delete(save=False)
        except:
            pass
        super(PayrollPolicy, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.payslipHeaderlogo.delete(save=False)
        super(PayrollPolicy, self).delete(*args, **kwargs)

class PfSlabs(models.Model):
    UNIT_CHOICES = (
        ('percent', 'Percentage'),
        ('amount', 'Amount'),
    )
    id=models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    start_amount = models.DecimalField(max_digits=10,decimal_places=2)
    end_amount = models.DecimalField(max_digits=10,decimal_places=2)
    pf_amount = models.DecimalField(max_digits=10,decimal_places=2)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)

class EmployeePayroll(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE , related_name='employee_pay')
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    month = models.IntegerField()
    year = models.IntegerField()
    gross = models.DecimalField(max_digits=15, decimal_places=2)
    lop = models.DecimalField(max_digits=10, decimal_places=2)
    present = models.DecimalField(max_digits=4, decimal_places=2,null=True,blank=True)
    no_leaves = models.DecimalField(max_digits=4, decimal_places=2)
    esi_deduction = models.DecimalField(max_digits=15, decimal_places=2)
    basic_salary = models.DecimalField(max_digits=15, decimal_places=2)
    allowances = models.JSONField(null=True,blank=True)
    deductions = models.JSONField(null=True,blank=True)
    employer_esi = models.DecimalField(max_digits=15, decimal_places=2)
    employer_pf = models.DecimalField(max_digits=15, decimal_places=2)
    pf_deduction = models.DecimalField(max_digits=15, decimal_places=2)
    net_salary = models.DecimalField(max_digits=15, decimal_places=2)
    tax_deduction = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=55, choices=(
        ('Preview', 'Preview'),
        ('Approved', 'Approved'),
        ('Processed', 'Processed'),
    ),default = 'Preview')


class PayrollAllowance(models.Model):
    payroll = models.ForeignKey(EmployeePayroll, on_delete=models.CASCADE, related_name="payroll_allowances")
    allowance = models.ForeignKey(Allowance, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.allowance.name} - {self.amount} in payroll"


class Assets(models.Model):
    department = models.ForeignKey(Department,on_delete=models.SET_NULL,null=True,blank=True)
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.name}"

class AssetDetails(models.Model):
    asset = models.ForeignKey(Assets, on_delete=models.SET_NULL,null=True,blank=True)
    serial_number = models.CharField(max_length=100)
    configuration = models.TextField()
    def __str__(self):
        return f"{self.asset.name} - {self.serial_number}"

class EmployeeAssetForm(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    timestamp = models.DateField(auto_now_add=True)
    assetdetails = models.ForeignKey(AssetDetails,on_delete=models.SET_NULL,null=True,blank=True)
    is_issued = models.BooleanField(default=False)
    issuedBy = models.ForeignKey(Employee, on_delete=models.CASCADE,related_name='asset_issued_by')

class RaiseTicket(models.Model):
    employeeID = models.ForeignKey(Employee, on_delete=models.CASCADE)
    Ticket_to_Department = models.ForeignKey(Department,on_delete=models.SET_NULL,null=True,blank=True)
    Issue = models.CharField(max_length=50)
    Comments_Or_Cause_of_issue = models.CharField(max_length = 100)
    approved = models.BooleanField(default=False)

class File(models.Model):
    file=models.FileField(upload_to='files')



class Grievance(models.Model):
    STATUS_CHOICES = (
        ('submitted', 'Submitted'),
        ('reviewing', 'Reviewing'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    sender = models.ForeignKey(User, related_name='grievances', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_anon = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class GrievanceComment(models.Model):
    grievance = models.ForeignKey(Grievance, related_name='comments', on_delete=models.CASCADE)
    comment = models.TextField()
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.sender.username} on {self.grievance.title}"

class Ticket(models.Model):
    STATUS_CHOICES = (
        ('submitted', 'Submitted'),
        ('reviewing', 'Reviewing'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )
    DEPARTMENT = (
        ('humanresource', 'Human Resource'),
        ('finance', 'Finance'),
        ('administration', 'Administration'),
        ('itnetwork', 'IT Network'),
    )
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    issue= models.CharField(max_length=255)
    description = models.TextField()
    sender = models.ForeignKey(User, related_name='tickets', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.issue

class TicketComment(models.Model):
    ticket = models.ForeignKey(Ticket, related_name='comments', on_delete=models.CASCADE)
    comment = models.TextField()
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.sender.username} on {self.ticket.issue}"

class MonthlyData(models.Model):
    year=models.IntegerField()
    month=models.IntegerField()
    no_of_working_days=models.IntegerField()
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)

class EmployeeLeaves(models.Model):
    month=models.IntegerField()
    year = models.IntegerField()
    leaves=models.DecimalField(max_digits=4, decimal_places=2,default=0.0)
    employee=models.ForeignKey(Employee, on_delete=models.CASCADE)
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    lop=models.DecimalField(max_digits=10, decimal_places=2)
    advance=models.IntegerField(default=0)
    bonus=models.IntegerField(default=0)

class IPAddr(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=20)

    def __str__(self):
        return self.name

class IPData(models.Model):
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    ipaddresses = models.ManyToManyField(IPAddr, related_name='ip_data')

    def set_ipaddresses(self, ipaddresses):
        self.ipaddresses.set(ipaddresses)

    def get_ipaddresses(self):
        return [ip.address for ip in self.ipaddresses.all()]

    def __str__(self):
        return f"{self.parent} - {self.child}"

class ActivityLog(models.Model):
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    data =  models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    reason = models.TextField(null=True,blank=True)

class AttendanceRequestObject(models.Model):
    employee=models.ForeignKey(Employee,on_delete=models.CASCADE)
    reason=models.CharField(max_length=250)
    Date=models.DateField(default='2024-05-10')
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    status = models.CharField(max_length=15, choices=(
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('underreview', 'Under Review'),
    ),default = 'underreview')

class CompOffRequestObject(models.Model):
    employee=models.ForeignKey(Employee,on_delete=models.CASCADE)
    reason=models.CharField(max_length=250)
    Date=models.DateField(default='2024-05-10')
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    managerstatus = models.CharField(max_length=15, choices=(
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('underreview', 'Under Review'),
    ),default = 'underreview')
    hrstatus = models.CharField(max_length=15, choices=(
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('underreview', 'Under Review'),
    ),default = 'underreview')
    approvedbyrm = models.ForeignKey(User, on_delete=models.SET_NULL,null=True, blank=True,related_name='approvedbyrm')
    approvedbyhr = models.ForeignKey(User, on_delete=models.SET_NULL,null=True, blank=True,related_name='approvedbyhr')

class LateLoginRequestObject(models.Model):
    employee=models.ForeignKey(Employee,on_delete=models.CASCADE,related_name="sender")
    reason=models.CharField(max_length=250)
    Date=models.DateField(default='2024-05-10')
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    status = models.CharField(max_length=15, choices=(
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('underreview', 'Under Review'),
    ),default = 'underreview')
    reported_to=models.ForeignKey(Employee,on_delete=models.CASCADE,related_name="reciever")

class EmployeeOccasions(models.Model):
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    employee=models.ForeignKey(Employee,on_delete=models.CASCADE)
    type = models.CharField(max_length=25, choices=(
        ('birthday', 'Birthday'),
        ('marriageday', 'Marriage Day'),
    ))
    date = models.DateField()


class BreakTime(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    child=models.ForeignKey(ChildAccount,on_delete=models.CASCADE,blank=True,null=True)
    parent=models.ForeignKey(Organization,on_delete=models.CASCADE,blank=True,null=True)
    date = models.DateField()
    reason = models.TextField()
    time_in = models.TimeField(null=True,blank=True)
    time_out = models.TimeField(null=True,blank=True)
    net_time_in =  models.CharField(max_length=10,null=True,blank=True)

class AttendancePolicy(models.Model):
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    officeStartTime = models.TimeField(null=True,blank=True)
    officeEndTime = models.TimeField(null=True,blank=True)
    min_working_for_full_day = models.DecimalField(null=True,blank=True,default=4.5,max_digits=4, decimal_places=1)
    workingDays = models.CharField(max_length=200,blank=True, null=True)
    def set_workingDays(self, roles):
        self.workingDays = ','.join(roles)

    def get_workingDays(self):
        if self.workingDays:
            return self.workingDays.split(',')
        else:
            return []
    def getworkingDays(self):
        if self.workingDays:
            return self.workingDays.split(',')
        else:
            return []

class AttendanceRequestPolicy(models.Model):
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    no_of_requests=models.IntegerField(default=0)

class LateLoginPolicy(models.Model):
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    no_of_late_logins=models.IntegerField(default=0)
    no_of_hours=models.CharField(null=True, max_length=2,blank=True)

class Quotes(models.Model):
    quote=models.TextField(null=True,blank=True)

class IPRequest(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    ip=models.CharField(null=True,blank=True,max_length=50)
    status = models.CharField(max_length=15, choices=(
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('underreview', 'Under Review'),
    ),default = 'underreview')

def get_day_of_week(year, month, day):
    date_obj = datetime(year, month, day)
    return date_obj.strftime('%A')

@receiver(post_save, sender=Holidays)
def update_monthly_data(sender, instance, created, **kwargs):
    if created:
        year = instance.date.year
        month = instance.date.month
        parent = instance.parent
        child = instance.child
        if MonthlyData.objects.filter(parent=parent,child=child,year=year).count() < 12:
            for i in range(1,13):
                MonthlyData.objects.get_or_create(
                    year=year,
                    month=i,
                    parent=parent,
                    child=child,
                    defaults={'no_of_working_days': 0}  
                )
        monthly_data, _ = MonthlyData.objects.get_or_create(
            year=year,
            month=month,
            parent=parent,
            child=child,
            defaults={'no_of_working_days': 0}  
        )

        total_days = calendar.monthrange(year, month)[1]

        try:
            attendance_policy = AttendancePolicy.objects.get(parent=parent, child=child)
            working_days = attendance_policy.get_workingDays()
        except AttendancePolicy.DoesNotExist:
            working_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']  


        all_days = set(range(1, total_days + 1))
        working_days_set = {day for day in all_days if get_day_of_week(year, month, day) in working_days}

        holidays_in_month = Holidays.objects.filter(
            parent=parent,
            child=child,
            date__year=year,
            date__month=month
        ).count()
        actual_working_days = len(working_days_set) - holidays_in_month
        monthly_data.no_of_working_days = actual_working_days
        monthly_data.save()

class Form12BB(models.Model):
    # Employee details
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    employee_name = models.CharField(max_length=255)
    employee_address = models.TextField()
    pan = models.CharField(max_length=10)
    financial_year = models.CharField(max_length=9)

    # House Rent Allowance (HRA)
    rent_paid = models.DecimalField(max_digits=10, decimal_places=2)
    landlord_name = models.CharField(max_length=255)
    landlord_address = models.TextField()
    landlord_pan = models.CharField(max_length=10, blank=True, null=True)

    # Leave travel concessions or assistance
    leave_travel_conesssions = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Deduction of interest on borrowing
    interest_paid = models.DecimalField(max_digits=10, decimal_places=2)
    lender_name = models.CharField(max_length=255)
    lender_address = models.TextField()
    lender_pan = models.CharField(max_length=10, blank=True, null=True)

    # Deduction under various sections
    section_80c = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    section_80ccc = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    section_80ccd = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # Other deductions
    section_80d = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    section_80e_interest_paid = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    section_80g_donation_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    section_80tta_interest_earned = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # Timestamps
    place = models.CharField(max_length=255)
    designation = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee_name} ({self.financial_year}) - Form 12BB"

def evidence_upload_path(instance, filename):
    employee_name_slug = slugify(instance.form_12bb.employee_name)
    year_slug = slugify(instance.form_12bb.financial_year)
    return f'investmentproofs/{employee_name_slug}/{year_slug}/{filename}'

class Evidence(models.Model):
    form_12bb = models.ForeignKey(Form12BB, on_delete=models.CASCADE, related_name="evidences")
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    hra = models.FileField(upload_to=evidence_upload_path,null=True,blank=True)
    leave_travel_consession = models.FileField(upload_to=evidence_upload_path,null=True,blank=True)
    interest_paid = models.FileField(upload_to=evidence_upload_path,null=True,blank=True)
    section_80c = models.FileField(upload_to=evidence_upload_path,null=True,blank=True)
    section_80ccc = models.FileField(upload_to=evidence_upload_path,null=True,blank=True)
    section_80ccd = models.FileField(upload_to=evidence_upload_path,null=True,blank=True)
    section_80d = models.FileField(upload_to=evidence_upload_path,null=True,blank=True)
    section_80e_interest_paid = models.FileField(upload_to=evidence_upload_path,null=True,blank=True)
    section_80g_donation_amount = models.FileField(upload_to=evidence_upload_path,null=True,blank=True)
    section_80tta_interest_earned = models.FileField(upload_to=evidence_upload_path,null=True,blank=True)

    def __str__(self):
        return f"{self.form_12bb.employee_name} ({self.form_12bb.financial_year})"

def generate_key():
    return Fernet.generate_key()

class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_seen = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        participants = self.participants.all()
        if participants.count() == 2:
            return f"Conversation between {participants[0].employee.userName} and {participants[1].employee.userName}"
        return "Conversation with insufficient participants"

    def is_valid_participant(self, employee):
        return self.participants.filter(employee=employee).exists()

    def has_two_participants(self):
        return self.participants.count() == 2

class Participant(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE)
    conversation = models.ForeignKey(Conversation, related_name='participants', on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.userName} in {self.conversation.id}"

class EncryptedTextField(models.TextField):
    def __init__(self, *args, **kwargs):
        self.key = settings.ENCRYPTION_KEY
        if len(self.key) != 32:
            raise ValueError("Encryption key must be 32 bytes long for AES-256.")
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value):
        if value:
            return self.encrypt_message(value)
        return value

    def from_db_value(self, value, expression, connection, context=None):
        # Decrypt the value when fetched from the database, but not for the admin
        if value:
            return self.decrypt_message(value)
        return value

    def encrypt_message(self, message: str) -> str:
        key = self.key
        iv = os.urandom(16)

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(message.encode()) + padder.finalize()

        encrypted_message = encryptor.update(padded_data) + encryptor.finalize()
        
        return base64.b64encode(iv + encrypted_message).decode('utf-8')

    def decrypt_message(self, encrypted_message: str) -> str:
        key = self.key
        encrypted_message_bytes = base64.b64decode(encrypted_message)
        iv = encrypted_message_bytes[:16]  # Extract IV
        encrypted_message_bytes = encrypted_message_bytes[16:]

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        padded_data = decryptor.update(encrypted_message_bytes) + decryptor.finalize()

        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        decrypted_message = unpadder.update(padded_data) + unpadder.finalize()

        return decrypted_message.decode('utf-8')

    def get_formatted_value(self, value):
        return value if value else 'No data'

    def value_from_object(self, obj):
        # Instead of returning decrypted value for admin form display, return a placeholder or the encrypted value
        value = getattr(obj, self.attname)
        if value:
            return '[ENCRYPTED DATA]'
        return 'No data'

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey('Employee', on_delete=models.CASCADE)
    receiver = models.ForeignKey('Employee', on_delete=models.CASCADE,related_name='receiver_msg',null=True,blank=True)
    content = EncryptedTextField()
    timestampp = models.DateTimeField()

    def __str__(self):
        return f"Message from {self.sender.userName} in {self.conversation.id} at {self.timestampp}"

class Resignation(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    reason = models.TextField()
    noticeperiodtill = models.DateField()
    handoverings = models.TextField()
    status = models.CharField(max_length=10,choices=[('accepted', 'Accepted'), ('rejected', 'Rejected'),('pending','Pending')],default = 'pending')
    rm = models.ForeignKey('User', on_delete=models.CASCADE,related_name='rm',blank=True,null=True)
    hr = models.ForeignKey('User', on_delete=models.CASCADE,related_name='hr',blank=True,null=True)
    bo = models.ForeignKey('User', on_delete=models.CASCADE,related_name='bo',blank=True,null=True)
    rm_comments = models.TextField(blank=True,null=True)
    hr_comments = models.TextField(blank=True,null=True)
    bo_comments = models.TextField(blank=True,null=True)

    def __str__(self):
        return f"{self.employee.userName} at {self.timestamp}"


class BroadcastCommunications(models.Model):
    parent = models.ForeignKey(Organization, on_delete=models.CASCADE)
    child = models.ForeignKey(ChildAccount, on_delete=models.CASCADE, blank=True, null=True)
    sender = models.ForeignKey('Employee', on_delete=models.CASCADE)
    content = EncryptedTextField()
    timestampp = models.DateTimeField()

    def __str__(self):
        return f"Message from {self.sender.userName} in {self.child.name} at {self.timestampp}"
# certification&skills


class EmployeeCertifications(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="certifications")
    name = models.CharField(max_length=150)
    certificate_number = models.CharField(max_length=100, blank=True, null=True)
    issue_date = models.DateField()
    expiry_date = models.DateField(blank=True, null=True)
    issuing_authority = models.CharField(max_length=100, blank=True, null=True)
    certificate_file = models.FileField(upload_to="certificates/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notified_30_days = models.BooleanField(default=False)
    notified_on_expiry = models.BooleanField(default=False)
    notified_after_expiry = models.BooleanField(default=False)
    notified_7_days = models.BooleanField(default=False)
    notified_1_day = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class EmployeeSkills(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="skills")

    skill_name = models.CharField(max_length=100)
    level = models.CharField(
        max_length=50,
        choices=[
            ("Beginner", "Beginner"),
            ("Intermediate", "Intermediate"),
            ("Advanced", "Advanced"),
            ("Expert", "Expert"),
        ],
    )
    years_of_experience = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.skill_name


class DocumentAccessRule(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    role=models.CharField(max_length=100)

    parent = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="document_access_rules"
    )

    target_employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="document_access_rules",
        help_text="If set, rule applies only to this employee"
    )

    function = models.CharField(
        max_length=200,
        default="Document Verification"
    )

    specific_action = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )

    access = models.CharField(
        max_length=50,
        choices=(('Access', 'Access'), ('Deny', 'Deny')),
        default='Access'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_doc_access_rules"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        target = self.target_employee.userName if self.target_employee else "ALL EMPLOYEES"
        return f"{self.role} → {target}"
class DocumentVerification(models.Model):
    """
    Each verification event for a single document.
    Keeps full audit history.
    """

    STATUS_CHOICES = (
        ('PENDING', 'PENDING'),
        ('ACCEPTED', 'ACCEPTED'),
        ('REJECTED', 'REJECTED'),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='doc_verifications'
    )

    document_type = models.CharField(
        max_length=60
    )  # aadhaar, pan, profile, offerLetter, etc.

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    comment = models.TextField(
        null=True,
        blank=True
    )

    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    verified_at = models.DateTimeField(
        null=True,
        blank=True
    )

    assigned_role = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Role that performed verification"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
         ordering = ['-created_at']
    constraints = [
        models.UniqueConstraint(
            fields=['employee', 'document_type', 'assigned_role', 'status'],
            name='unique_pending_document_verification'
        )
    ]

    def mark_accepted(self, user):
        self.status = 'ACCEPTED'
        self.verified_by = user
        self.verified_at = timezone.now()
        self.comment = None
        self.save()

    def mark_rejected(self, user, comment):
        self.status = 'REJECTED'
        self.comment = (comment or '').strip()
        self.verified_by = user
        self.verified_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.employee.userName} - {self.document_type} - {self.status}"
