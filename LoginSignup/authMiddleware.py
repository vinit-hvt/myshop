from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse


class isUserAuthenticated():

    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if 'myshop' in request.path:
            if request.path == '/myshop/' or request.path == '/myshop/signup/':
                return self.get_response(request)
            elif self.isUserAuthorized(request):
                return self.get_response(request)
            else:
                return HttpResponseRedirect(reverse('LoginSignup:login'))
        else:
            return self.get_response(request)


    
    def isUserAuthorized(self, request):
        try:
            cookieUsername = request.COOKIES['username']
            cookieSessionId = request.COOKIES['sessionId']
            sessionSessionId = request.session[cookieUsername]
            return cookieSessionId == sessionSessionId
        except:
            return False