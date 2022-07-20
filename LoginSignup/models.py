from django.db import models

# Create your models here.

class Users(models.Model):
    username = models.CharField(max_length=20, primary_key=True)
    userEmail = models.EmailField(unique=True, null=False)
    password = models.CharField(max_length=80, null=False)
    fullName = models.CharField(max_length=100, default='', null=False)
    contact = models.CharField(max_length=10, null=False)
    walletBalance = models.FloatField(default=0)
    userProfileImage = models.ImageField(null=False, blank=False, upload_to="UserProfileImages/", default='UserProfileImages/noProfileImage.png')


class Address(models.Model):
    addressId = models.BigAutoField(primary_key=True)
    addressLine = models.CharField(max_length=200, null=False)
    city = models.CharField(max_length=20, null=False)
    state = models.CharField(max_length=20, null=False)
    zipCode = models.CharField(max_length=10, null=False)
    person = models.ForeignKey(Users, on_delete=models.CASCADE)