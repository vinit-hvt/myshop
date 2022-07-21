from statistics import mode
from django.db import models
from LoginSignup.models import Address, Users
from datetime import datetime, timedelta


def getDeliveryDate():
    return (datetime.now() + timedelta(days=5))


# Create your models here.


class ProductTags(models.Model):
    tagName = models.CharField(max_length=40, null=False, primary_key=True)
    def __repr__(self) -> str:
        return f"Tag Name : {self.tagName}"


class Products(models.Model):
    productId = models.BigAutoField(primary_key=True)
    productName = models.CharField(max_length=30, null=False)
    productCategory = models.CharField(max_length=30, null=False)
    productPrice = models.IntegerField(null=False)
    warrantInMonths = models.IntegerField(null=False, default=0)
    manufacturerDetails = models.CharField(null=False, max_length=200)
    productDescription = models.TextField(null=False)
    productImage = models.ImageField(null=False, blank=False, upload_to="ProductImages/")
    seller = models.ForeignKey(Users, on_delete=models.CASCADE)
    tags = models.ManyToManyField(ProductTags, null=True)

    def __repr__(self) -> str:
        return f"{self.productName} costs Rs {self.productPrice}"



class Orders(models.Model):
    orderId = models.BigAutoField(primary_key=True)
    orderedOn = models.DateTimeField(default=datetime.now)
    totalBillAmount = models.FloatField(null = False)
    deliveryAddress = models.ForeignKey(Address, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    isOrderDelivered = models.BooleanField(default=False)
    estimatedDeliveryDate = models.DateTimeField(default=getDeliveryDate)

    def __repr__(self) -> str:
        return f"Order Id : {self.orderId}, Order of User : {self.user__username} on {self.orderedOn}"


class Cart(models.Model):
    cartId = models.BigAutoField(primary_key=True)
    person = models.ForeignKey(Users, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    productQty = models.IntegerField(default=1)
    addedToCartOn = models.DateTimeField(default=datetime.now)
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, null=True)

    def __repr__(self) -> str:
        return f"{self.product.productName} Added on {self.addedToCartOn}"