from django.urls import path
from . import views

app_name = "myshop"

urlpatterns = [
    path('home/', views.Home.as_view(), name='home'),
    path('addProduct/', views.AddProduct.as_view(), name='addProduct'),
    path('viewProducts/<searchKey>', views.ViewProducts.as_view(), name='viewProducts'),
    path('searchProducts/', views.SearchProducts.as_view(), name='searchProducts'),
    path('viewProduct/<int:productId>', views.ViewProduct.as_view(), name='viewProduct'),
    path('cart/addToCart', views.AddToCart.as_view(), name='addToCart'),
    path('cart/viewCart', views.UserCart.as_view(), name='viewCart'),
    path('cart/removeFromCart', views.RemoveFromCart.as_view(), name='removeFromCart'),
    path('cart/getCartItemsCount', views.GetCartItemsCount.as_view(), name='getCartItemsCount'),
    path('cart/changeCartItemQuanity/', views.ChangeCartItemQuanity.as_view(), name='changeCartItemQuanity'),
    path('cart/placeOrder/', views.PlaceOrder.as_view(), name='placeOrder'),
    path('myOrders/', views.MyOrders.as_view(), name='myOrders'),
    path('myOrders/cancelOrder/<int:orderId>', views.CancelOrder.as_view(), name='cancelOrder'),
    path('myOrders/orderDetails/products/<int:orderId>', views.OrderDetailsProducts.as_view(), name='orderDetailsProducts'),
    path('myOrders/orderDetails/bill/<int:orderId>', views.OrderDetailsBill.as_view(), name='orderDetailsBill'),
    path('logout/', views.Logout.as_view(), name='logout'),
]
