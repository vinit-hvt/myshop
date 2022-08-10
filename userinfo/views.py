from django import views
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views import View
from LoginSignup.models import UserType, Users, Address, PremiumPlans, PremiumUsers
from django.contrib import messages
from LoginSignup.utils import isNumberValid
from django.urls import reverse
from datetime import datetime, timedelta
from django.db.models import F, Sum
from LoginSignup.utils import setCrownSymbol
from myshop.models import Orders

# Create your views here.



class ProfileDetails(View):

    def get(self, request):
        username = request.COOKIES['username']
        userDetails = Users.objects.get(pk=username)
        setCrownSymbol(request, userDetails)

        cashbackRewarded = Orders.objects.filter(user = userDetails, isOrderDelivered = True).aggregate(sum = Sum('cashbackRewarded'))['sum']
        cashbackRewarded = float(format(cashbackRewarded, '.2f'))
        walletBalance = float(format(userDetails.walletBalance, '.2f'))
        return render(request, 'userinfo/viewProfile.html', context={'userDetails':userDetails, 'cashbackRewarded' : cashbackRewarded, 'walletBalance' : walletBalance})
    
    def post(self, request):
        username = request.COOKIES['username']
        userDetails = Users.objects.get(pk=username)

        if (userDetails.userEmail != request.POST['email'] and len(Users.objects.filter(userEmail = request.POST['email']))):
            messages.error(request, "Email already in use, Try different one.")
        
        elif not isNumberValid(request.POST['contact'], numberLenReq=10):
            messages.error(request, "Contact Number is not valid.")

        else:
            userDetails.fullName = request.POST['fullName']
            userDetails.userEmail = request.POST['email']
            userDetails.contact = request.POST['contact']
            if len(request.FILES):
                userDetails.userProfileImage.delete()
                userDetails.userProfileImage = request.FILES['userProfilePhoto']
            userDetails.save()
            messages.success(request, "Profile Updated Successfully !!!")

        return HttpResponseRedirect(reverse('userinfo:profile'))
    

class MyAddress(View):

    def get(self, request):
        username = request.COOKIES['username']
        addresses = Address.objects.filter(person__username = username)
        return render(request, 'userinfo/myAddress.html', context={
            'addresses':addresses
        })


class AddNewAddress(View):

    def get(self, request):
        return render(request, 'userinfo/addNewAddress.html')
    

    def post(self, request):

        contactDetails = {}
        for key in request.POST:
            contactDetails[key] = request.POST[key]
        
        if not isNumberValid(request.POST['zipCode']):
            messages.error(request, "Zip Code is not valid.")
        elif self.__isAddressAlreadyExists(request):
            messages.error(request, "You've already registered this contact.")
        else:
            newAddress = Address(
                addressLine = request.POST['addressLine'],
                state = request.POST['state'],
                city = request.POST['city'],
                zipCode = request.POST['zipCode'],
                person = Users.objects.get(pk=request.COOKIES['username'])
            )
            newAddress.save()
            messages.success(request, "Address Added Successfully !!!")
            return HttpResponseRedirect(reverse('userinfo:myAddress'))
        
        return render(request, 'userinfo/addNewAddress.html', context=contactDetails)


    def __isAddressAlreadyExists(self, request):
        return len( Address.objects.filter(addressLine = request.POST['addressLine'], city = request.POST['city'], state = request.POST
        ['state'], zipCode = request.POST['zipCode'], person__username = request.COOKIES['username']) )        



class RemoveAddress(View):

    def get(self, request, addressId):
        address = get_object_or_404(Address, pk=addressId)
        address.delete()
        messages.success(request, "Address removed Successfully !!!")
        return HttpResponseRedirect(reverse('userinfo:myAddress'))



class WalletBalance(View):

    def get(self, request):
        return render(request, 'userinfo/walletBalance.html')

    def post(self, request):

        details = {}
        for key in request.POST:
            details[key] = request.POST[key]
        
        # 2022-07-14T15:57
        if not isNumberValid(request.POST['cardNumber'], numberLenReq=12):
            messages.error(request, "Please enter a valid 12-digit Card Number")
            details['cardNumber'] = ''
        elif not isNumberValid(request.POST['cvvCode'], numberLenReq=3):
            messages.error(request, "Please enter a valid 3-digit CVV Code")
            details['cvvCode'] = ''
        elif datetime.now() >= datetime.strptime(request.POST['expiryDate'], '%Y-%m'):
            messages.error(request, "Your card has expired.")
        elif float(request.POST['amount']) <= 0:
            messages.error(request, "Please enter a valid positive amount to add in the wallet.")
            details['amount'] = 0
        else:
            user = Users.objects.get(pk=request.COOKIES['username'])
            user.walletBalance += float(request.POST['amount'])
            user.save()
            messages.success(request, f"Amount Rs {request.POST['amount']} has successfully added in your wallet.")
            return HttpResponseRedirect(reverse('userinfo:profile'))
        
        return render(request, 'userinfo/walletBalance.html', context = details)


class PremiumPlan(View):
    def get(self, request):
        return render(request, 'userinfo/premiumPlans.html')


class BuyPlan(View):
    def get(self, request, planName):
        user = Users.objects.get(pk=request.COOKIES['username'])
        planName = planName.lower()

        if planName == "basic":
            planSelected, planCost, planValidity = PremiumPlans.ONE_MONTH_PLAN, 299, 30
        elif planName == "standard":
            planSelected, planCost, planValidity = PremiumPlans.THREE_MONTH_PLAN, 699, 90
        elif planName == "special":
            planSelected, planCost, planValidity = PremiumPlans.ONE_YEAR_PLAN, 1899, 365
        else:
            messages.error(request, f"Please select a valid plan.")
            return HttpResponseRedirect(reverse('userinfo:premiumPlan'))
            
        if user.userType == 'UserType.PREMIUM':
            planEnrolled = PremiumUsers.objects.get(user = user).planName
            messages.error(request, f"You're already enrolled in a Premium Plan")
            return HttpResponseRedirect(reverse('userinfo:premiumPlan'))
        elif user.walletBalance < planCost:
            messages.error(request, "You don't have sufficient wallent balance to buy this plan")
            return HttpResponseRedirect(reverse('userinfo:premiumPlan'))
        else:
            user.userType = UserType.PREMIUM
            user.walletBalance = user.walletBalance - planCost
            newPremiumUser = PremiumUsers(
                planName = planSelected,
                user = user,
                endDate = datetime.now() + timedelta(days=planValidity)
            )
            newPremiumUser.save()
            user.save()
            setCrownSymbol(request, user)
            messages.success(request, "Now you're a MyShop's Premium User")
            return HttpResponseRedirect(reverse('userinfo:profile'))


class RedeemShopyCoins(View):
    One_Shoppy_Coin_In_RS = 0.1
    def get(self, request):
        user = Users.objects.get(pk=request.COOKIES['username'])
        if user.userType != 'UserType.PREMIUM':
            messages.error(request, "You need to have a Premium Account to redeem the Shopy Coins")
        elif user.shopyCoins <= 0:
            messages.error(request, "You have zero Shopy Coins")
        else:
            user.walletBalance = F('walletBalance') + (self.One_Shoppy_Coin_In_RS * F('shopyCoins'))
            user.shopyCoins = 0
            user.save()
            user.refresh_from_db()
            messages.success(request, "You have successfully redeemed Shopy Coins, (1 Shopy Coin = 0.1 Rs)")
        return HttpResponseRedirect(reverse('userinfo:profile'))