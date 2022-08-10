import string
import random
from .models import PremiumUsers

def generateRandomString(length=30):
    generatedString = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    return generatedString


def isNumberValid(number, numberLenReq=None):
    number = str(number)
    if numberLenReq is not None and len(number) != numberLenReq:
        return False
    for digit in number:
        if not (digit >= '0' and digit <= '9'):
            return False
    return True


def setCrownSymbol(request, user):
    premiumAccount = PremiumUsers.objects.filter(user__username=user.username)
    request.session['User_Crown_Symbol'] = ''
    if premiumAccount.count() and user.userType == 'UserType.PREMIUM':
        premiumAccount = premiumAccount[0]
        if premiumAccount.planName == 'PremiumPlans.ONE_MONTH_PLAN':
            request.session['User_Crown_Symbol'] = '♕'
        elif premiumAccount.planName == 'PremiumPlans.THREE_MONTH_PLAN':
            request.session['User_Crown_Symbol'] = '♚'
        elif premiumAccount.planName == 'PremiumPlans.ONE_YEAR_PLAN':
            request.session['User_Crown_Symbol'] = '👑'
    

