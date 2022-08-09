from email.policy import default
from django.db import models
from enum import Enum
from datetime import datetime


class UserType(Enum):
    REGULAR = "regular"
    PREMIUM = "premium"


class PremiumPlans(Enum):
    ONE_MONTH_PLAN = 'One Month Plan'
    THREE_MONTH_PLAN = 'Three Month Plan'
    ONE_YEAR_PLAN = 'One Year Plan'



# Create your models here.

class Users(models.Model):
    username = models.CharField(max_length=20, primary_key=True)
    userEmail = models.EmailField(unique=True, null=False)
    password = models.CharField(max_length=80, null=False)
    fullName = models.CharField(max_length=100, default='', null=False)
    contact = models.CharField(max_length=10, null=False)
    walletBalance = models.FloatField(default=0)
    userProfileImage = models.ImageField(null=False, blank=False, upload_to="UserProfileImages/", default='UserProfileImages/noProfileImage.png')
    userType = models.CharField(max_length=20, choices=[(usertype, usertype.value) for usertype in UserType], default=UserType.REGULAR)
    shopyCoins = models.IntegerField(default=0, null=False)


class PremiumUsers(models.Model):
    planName = models.CharField(max_length=20, choices=[(plan, plan.value) for plan in PremiumPlans], null=False)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    startDate = models.DateTimeField(default=datetime.now, null=False, blank=False)
    endDate = models.DateTimeField(null=False, blank=False)



class Address(models.Model):
    addressId = models.BigAutoField(primary_key=True)
    addressLine = models.CharField(max_length=200, null=False)
    city = models.CharField(max_length=20, null=False)
    state = models.CharField(max_length=20, null=False)
    zipCode = models.CharField(max_length=10, null=False)
    person = models.ForeignKey(Users, on_delete=models.CASCADE)