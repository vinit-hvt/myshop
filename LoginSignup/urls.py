from django.urls import path
from . import views

app_name = "LoginSignup"

urlpatterns = [
    path('', views.Login.as_view(), name='login'),
    path('signup/', views.Signup.as_view(), name='signup'),
    # path('home/', views.home, name='home'),
]
