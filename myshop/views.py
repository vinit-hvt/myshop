from datetime import datetime
import django
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.urls import reverse
from LoginSignup.models import Address
from .models import Products, Users, Cart, Orders, ProductTags
from django.contrib import messages
from django.db.models import Q, F
from .utils import isProductInTheCart


# Create your views here.


class Home(View):

    def get(self, request):
        print("This is home")
        allProducts = {}
        maxLength = 4
        for product in Products.objects.all().values():
            product['productImageUrl'] = Products.objects.get(pk=product['productId']).productImage.url
            product['isInTheCart'] = isProductInTheCart(productId=product['productId'], username=request.COOKIES['username'])
            if product['productCategory'] in  allProducts:
                if len(allProducts[product['productCategory']]) < maxLength:
                    allProducts[product['productCategory']].append(product)
            else:
                allProducts[product['productCategory']] = [product]
        
        return render(request, 'myshop/home.html', context={'allProducts':allProducts})


class AddProduct(View):

    def get(self, request):
        return render(request, 'myshop/addProduct.html')
    

    def post(self, request):
        productInfo = dict()
        for key in request.POST:
            productInfo[key] = request.POST[key]
        
        productsFound = Products.objects.filter(productName = request.POST['productName']) # Product Name Validation #
        if len(request.FILES) == 0:
            messages.error(request, "Please upload the product image !!!")
        if len(productsFound) != 0:
            productInfo['productName'] = ""
            messages.error(request, "Product name already exists !!!")
        else:
            newProduct = Products(
                productName = productInfo['productName'],
                productCategory = productInfo['productCategory'],
                productPrice = productInfo['productPrice'],
                warrantInMonths = productInfo['warranty'],
                productDescription = productInfo['description'],
                manufacturerDetails = productInfo['manufacturerNameAddress'],
                seller = Users.objects.get(username=request.COOKIES['username']),
                productImage = request.FILES['productImage']
            )
            newProduct.save()
            for tag in request.POST['productTags'].split(','):
                tag = tag.lower().strip()
                if tag != "":
                    productTag, created = ProductTags.objects.get_or_create(tagName=tag, defaults={
                        "tagName":tag
                    })
                    newProduct.tags.add(productTag)

            messages.success(request, "Product Added Successfully !!!")
            productInfo = {}
        
        return render(request, 'myshop/addProduct.html', context=productInfo)




class ViewProducts(View):

    def get(self, request, searchKey):
        searchKey = "" if searchKey.lower() == "all" else searchKey
        queryResult = Products.objects.filter(Q(productName__icontains = searchKey) | Q(productCategory__icontains = searchKey) | Q(tags__tagName__contains = searchKey)).distinct()
        
        allProducts = {}
        for product in queryResult.values():
            product['productImageUrl'] = Products.objects.get(pk=product['productId']).productImage.url
            product['isInTheCart'] = isProductInTheCart(productId=product['productId'], username=request.COOKIES['username'])
            if product['productCategory'] in  allProducts:
                allProducts[product['productCategory']].append(product)
            else:
                allProducts[product['productCategory']] = [product]
        
        return render(request, 'myshop/viewProducts.html', context={'allProducts':allProducts})



class SearchProducts(View):

    def get(self, request):
        searchKey = "" if request.GET['searchKey'].lower() == "all" else request.GET['searchKey']
        queryResult = Products.objects.filter(Q(productName__icontains = searchKey) | Q(productCategory__icontains = searchKey) | Q(tags__tagName__icontains = searchKey)).distinct()
        allProducts = {}
        for product in queryResult.values():
            product['productImageUrl'] = Products.objects.get(pk=product['productId']).productImage.url
            product['isInTheCart'] = isProductInTheCart(productId=product['productId'], username=request.COOKIES['username'])
            if product['productCategory'] in  allProducts:
                allProducts[product['productCategory']].append(product)
            else:
                allProducts[product['productCategory']] = [product]
        
        return render(request, 'myshop/viewProducts.html', context={'allProducts':allProducts})



class ViewProduct(View):

    def get(self, request, productId):
        selectedProduct = get_object_or_404(Products, pk=productId) # This is just for verification whether the products exits or not #
        selectedProduct = Products.objects.filter(pk=productId).values().first()
        selectedProduct['productImageUrl'] = Products.objects.get(pk=selectedProduct['productId']).productImage.url
        selectedProduct['isInTheCart'] = isProductInTheCart(productId=selectedProduct['productId'], username=request.COOKIES['username'])
        selectedProductDescription = list(map(lambda string: string.replace('\r', ''), selectedProduct['productDescription'].split('\n')))

        relatedProducts = list()
        for product in Products.objects.filter(productCategory = selectedProduct['productCategory']).values():
            product['productImageUrl'] = Products.objects.get(pk=product['productId']).productImage.url
            product['isInTheCart'] = isProductInTheCart(productId=product['productId'], username=request.COOKIES['username'])
            relatedProducts.append(product)

        productCategory = selectedProduct['productCategory']
        # print(relatedProducts)
        # print(selectedProductDescription)
        return render(request, 'myshop/viewProduct.html', context={
            'selectedProduct' : selectedProduct,
            'relatedProducts' : relatedProducts,
            'selectedProductDescription' : selectedProductDescription,
            'productCategory' : productCategory
        })



class UserCart(View):

    def get(self, request):
        
        cartItems = Cart.objects.filter(person__username = request.COOKIES['username'], order__isnull = True)
        return render(request, 'myshop/viewCart.html', context={
            'cartItems' : cartItems,
            'cartItemsCount' : cartItems.count()
        })


class AddToCart(View):
    def get(self, request):
        username = request.COOKIES['username']
        productId = request.GET['productId']
        if not Cart.objects.filter(person__username = username, product__productId = productId, order__isnull = True).count():
            newCartItem = Cart(
                person = Users.objects.get(pk=username),
                product = Products.objects.get(pk=productId)
            )
            newCartItem.save()
        
        return JsonResponse({
            'message' : 'Product added to the Cart.',
            'itemsInCart' : Cart.objects.filter(person__username = username, order__isnull = True).count()
        })



class RemoveFromCart(View):
    def get(self, request):
        username = request.COOKIES['username']
        productId = request.GET['productId']
        if Cart.objects.filter(person__username = username, product__productId = productId, order__isnull = True).count():
            cartItem = Cart.objects.get(person__username = username, product__productId = productId, order__isnull = True)
            cartItem.delete()
        
        return JsonResponse({
            'message' : 'Product removed from the Cart.',
            'itemsInCart' : Cart.objects.filter(person__username = username, order__isnull = True).count()
        })


class ChangeCartItemQuanity(View):

    def get(self, request):
        productId, incrementBy = request.GET['productId'], request.GET['incrementBy']
        print(f"\n\n ProductId : {productId}, Increment by : {incrementBy}")
        try:
            cartItem = Cart.objects.get(person__username = request.COOKIES['username'], product__productId = productId, order__isnull = True)
            cartItem.productQty = F('productQty') + incrementBy
            cartItem.save()
            cartItem.refresh_from_db()
            return JsonResponse({
                'message' : 'Quantity Updated Successfully !!!',
                'productQty' : cartItem.productQty,
            })
        except Exception as e:
            print("Error in ChangeCartItemQuanity -- ", e)
            return JsonResponse({
                'message' : e,
                'productQty' : 0
            })



class GetCartItemsCount(View):
    def get(Self, request):
        return JsonResponse({
            'itemsInCart' : Cart.objects.filter(person__username = request.COOKIES['username'], order__isnull = True).count(),
        })


class PlaceOrder(View):

    def get(self, request):
        cartItems = Cart.objects.filter(person__username = request.COOKIES['username'], order__isnull = True).values()
        userAddresses = Address.objects.filter(person__username = request.COOKIES['username']).values()
        index, totalUnits, sumOfIndividualPrice, totalBillAmount = 1, 0, 0, 0
        print(cartItems)
        for item in cartItems:
            product = Products.objects.get(pk=item['product_id'])
            item['index'] = index
            item['total'] = (item['productQty'] * product.productPrice) 
            item['product'] = product 
            totalUnits += item['productQty']
            sumOfIndividualPrice += product.productPrice
            totalBillAmount += item['total']
            index += 1

        if index == 1:
            messages.error(request, "Please add a product to the cart.")
            return HttpResponseRedirect(reverse('myshop:home'))

        return render(request, 'myshop/placeOrder.html', context={
            'cartItems' : cartItems,
            'userAddresses' : userAddresses,
            'cartItemsCount' : cartItems.count,
            'totalUnits' : totalUnits,
            'sumOfIndividualPrice' : sumOfIndividualPrice,
            'totalBillAmount' : totalBillAmount
        })
    

    def post(self, request):

        del request.session['helper'], request.session['helperName']
        user = Users.objects.get(pk=request.COOKIES['username'])
        totalBillAmount = float(request.POST['totalBillAmount'])
        if totalBillAmount > user.walletBalance:
            messages.error(request, "Insufficient Wallet Balance.")
            request.session['helper'] = reverse('userinfo:walletBalance')
            request.session['helperName'] = "Add Money"
        elif request.POST['address'].lower() == "defaulttext" or len(Address.objects.filter(pk=request.POST['address'])) == 0:
            messages.error(request, "Please select the delivery address.")
        else:
            newOrder = Orders(
                totalBillAmount = totalBillAmount,
                user = user,
                deliveryAddress = Address.objects.get(pk=request.POST['address'])
            )
            newOrder.save()
            Cart.objects.filter(person__username = user.username, order__isnull = True).update(order = newOrder)
            user.walletBalance = F('walletBalance') - totalBillAmount
            user.save()
            user.refresh_from_db()
            messages.success(request, "Order Placed Successfully.")
            return HttpResponseRedirect(reverse('myshop:myOrders'))

        
        return HttpResponseRedirect(reverse('myshop:placeOrder'))



class MyOrders(View):

    def get(self, request):
        today = datetime.now()
        Orders.objects.filter(user__username = request.COOKIES['username'], estimatedDeliveryDate__lte = today).update(isOrderDelivered = True)
        allOrders = Orders.objects.filter(user__username = request.COOKIES['username']).values()
        print("\n\n", allOrders, "\n")
        for order in allOrders:
            order['deliveryAddress'] = Address.objects.get(pk=order['deliveryAddress_id'])
            order['orderedOn'] = order['orderedOn'].strftime("%a %d %B, %Y")
            order['estimatedDeliveryDate'] = order['estimatedDeliveryDate'].strftime("%a %d %B, %Y")


        return render(request, 'myshop/myOrders.html', context={
            'allOrders' : allOrders,
            'ordersCount' : allOrders.count()
        })



class CancelOrder(View):

    def get(self, request, orderId):
        try:
            orderDetails = Orders.objects.get(pk = orderId, user__username = request.COOKIES['username'])

            # If order is already delivered #
            if orderDetails.isOrderDelivered:
                messages.error(request, "Order is already delivered.")
            else:
                # Steps to cancel the order #
                Cart.objects.filter(order__orderId = orderDetails.orderId).delete() # Remove the products from the Cart Table #
                Users.objects.filter(pk = request.COOKIES['username']).update(walletBalance = F('walletBalance') + orderDetails.totalBillAmount) # Refunding the order's bill amount to the user's account #
                orderDetails.delete() # Deleting order details from the Orders Table #

                messages.success(request, "Order is Cancelled. Bill amount is refunded to your account.")
             
        except Exception as e:
            print("Exception occured while cancelling the order => ", e)
            messages.error(request, "Order Not Found.")

        return HttpResponseRedirect(reverse('myshop:myOrders'))



class OrderDetailsProducts(View):

    def get(self, request, orderId):
        orderDetails = Cart.objects.filter(order__orderId = orderId)
        return render(request, 'myshop/orderDetailsProducts.html', context={
            'orderDetails' : orderDetails,
            'productCount' : orderDetails.count(),
            'orderId' : orderId
        })
            


class OrderDetailsBill(View):

    def get(self, request, orderId):
        cartItems = Cart.objects.filter(order__orderId = orderId, person__username = request.COOKIES['username']).values()
        index, totalUnits, sumOfIndividualPrice, totalBillAmount = 1, 0, 0, 0

        for item in cartItems:
            product = Products.objects.get(pk=item['product_id'])
            item['index'] = index
            item['total'] = (item['productQty'] * product.productPrice) 
            item['product'] = product 
            totalUnits += item['productQty']
            sumOfIndividualPrice += product.productPrice
            totalBillAmount += item['total']
            index += 1

        if index == 1:
            messages.error(request, "Please place an order first.")
            return HttpResponseRedirect(reverse('myshop:home'))

        return render(request, 'myshop/orderDetailsBill.html', context={
            'orderDetails' : cartItems,
            'totalUnits' : totalUnits,
            'sumOfIndividualPrice' : sumOfIndividualPrice,
            'totalBillAmount' : totalBillAmount,
            'orderId' : orderId
        })





class Logout(View):

    def get(self, request):
        response = HttpResponseRedirect(reverse('LoginSignup:login'))
        del request.session[request.COOKIES['username']]
        response.delete_cookie(key='username')
        response.delete_cookie(key='sessionId')
        return response


