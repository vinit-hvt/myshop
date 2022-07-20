from django.urls import path
from . import views

app_name = "userinfo"

urlpatterns = [
    path('profile/', views.ProfileDetails.as_view(), name='profile'),
    path('profile/myAddress', views.MyAddress.as_view(), name='myAddress'),
    path('profile/myAddress/addNewAddress', views.AddNewAddress.as_view(), name='addNewAddress'),
    path('profile/myAddress/removeAddress/<int:addressId>', views.RemoveAddress.as_view(), name='removeAddress'),
    path('profile/walletBalance', views.WalletBalance.as_view(), name='walletBalance'),

]
