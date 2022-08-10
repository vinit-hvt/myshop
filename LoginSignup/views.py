from django.shortcuts import render
from django.views import View
from django.http import HttpResponseRedirect
from django.urls import reverse
from .validations import validator
from .models import Users, Address
import bcrypt
from django.db.models import Q
from django.contrib import messages
from .utils import generateRandomString, setCrownSymbol


# Create your views here.


class Login(View):

    templateName = "LoginSignup/login.html"
    sessionIdLength = 30

    def get(self, request):
        return render(request, self.templateName, context={})

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        user = Users.objects.filter(Q(username=username) | Q(userEmail=username))
        
        if len(user) and bcrypt.checkpw(password.encode('utf-8'), user[0].password.encode('utf-8')):
            sessionId = generateRandomString(length=self.sessionIdLength)
            response =  HttpResponseRedirect(reverse('myshop:home'))
            response.set_cookie(key='username', value=username)
            response.set_cookie(key='sessionId', value=sessionId)
            request.session[username] = sessionId
            setCrownSymbol(request, user[0])
            return response

        context = {
            'username' : request.POST['username'],
        }
        messages.error(request, "Invalid Username or Password")
        return render(request, 'LoginSignup/login.html', context=context)



class Signup(View):

    templateName = "LoginSignup/signup.html"
    def get(self, request):
        return render(request, self.templateName, context={})

    def post(self, request):
        formValidator = validator(request.POST)
        formValidator.validateSignupForm()
        if formValidator.isFormValid:
            newUser = Users(
                username = request.POST['username'],
                userEmail = request.POST['email'],
                password = bcrypt.hashpw(request.POST['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                contact = request.POST['contact'],
            )
            newUser.save()
            newAddress = Address(
                addressLine = request.POST['address'],
                city = request.POST['city'],
                state = request.POST['state'],
                zipCode = request.POST['zipCode'],
                person = newUser,
            )
            newAddress.save()
            messages.success(request, "Sign Up Successfull, Now Login")
            return HttpResponseRedirect(reverse('LoginSignup:login'))
        else:
            context = dict()
            for key in request.POST:
                context[key] = "" if key == formValidator.faultyKey else request.POST[key]
            
            messages.error(request, formValidator.errorMessage)
            return render(request, 'LoginSignup/signup.html', context=context)


def home(request):
    print("home")
    return render(request, 'LoginSignup/home.html', context={'username':request.COOKIES['username']})    