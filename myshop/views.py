from datetime import datetime
from email import message
import django
from django import views
from django.db import reset_queries
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.urls import reverse
from LoginSignup.models import Address
from .models import Products, SearchHistory, Users, Cart, Orders, ProductTags
from django.contrib import messages
from django.db.models import Q, F
from .utils import isProductInTheCart, searchProductWithKeyword, getProductsCategoryWise


# Create your views here.


class Home(View):

    def get(self, request):
        allProducts = {}
        maxLength = 4
        for product in Products.objects.all().order_by('productCategory', '-recommendationAmount').values():
            product['productImageUrl'] = Products.objects.get(pk=product['productId']).productImage.url
            product['isInTheCart'] = isProductInTheCart(productId=product['productId'], username=request.COOKIES['username'])
            if product['productCategory'] in  allProducts:
                if allProducts[product['productCategory']][0] < maxLength:
                    allProducts[product['productCategory']][1].append(product)
                    allProducts[product['productCategory']][0] += 1
            else:
                allProducts[product['productCategory']] = [1,[product]]

        return render(request, 'myshop/home.html', context={'allProducts':allProducts})


class AddProduct(View):

    def get(self, request):
        return render(request, 'myshop/addProduct.html')
    

    def post(self, request):
        productInfo = dict()
        for key in request.POST:
            productInfo[key] = request.POST[key]
        
        user = Users.objects.get(pk=request.COOKIES['username'])
        productsFound = Products.objects.filter(productName = request.POST['productName']) # Product Name Validation #
        if len(request.FILES) == 0:
            messages.error(request, "Please upload the product image !!!")
        if len(productsFound) != 0:
            productInfo['productName'] = ""
            messages.error(request, "Product name already exists !!!")
        if 'isRecommended' in request.POST and user.walletBalance < float(productInfo['recommendationCharges']):
            productInfo['recommendationCharges'] = ""
            messages.error(request, "You don't have sufficient balance to sponsor this product.")
        else:
            newProduct = Products(
                productName = productInfo['productName'],
                productCategory = productInfo['productCategory'],
                productPrice = productInfo['productPrice'],
                warrantInMonths = productInfo['warranty'],
                productDescription = productInfo['description'],
                manufacturerDetails = productInfo['manufacturerNameAddress'],
                seller = Users.objects.get(username=request.COOKIES['username']),
                productImage = request.FILES['productImage'],
                isRecommended = 'isRecommended' in request.POST and request.POST['isRecommended'].lower() == "on",
                recommendationAmount = float(request.POST['recommendationCharges']) if 'isRecommended' in request.POST else 0
            )
            newProduct.save()

            # Adding tags to the product -- PAID #
            if 'isRecommended' in request.POST and request.POST['isRecommended'].lower() == "on":
                user.walletBalance = F('walletBalance') - float(request.POST['recommendationCharges'])
                user.save()
                user.refresh_from_db()
                for tag in request.POST['productTags'].split(','):
                    tag = tag.lower().strip()
                    if tag != "":
                        productTag, created = ProductTags.objects.get_or_create(tagName=tag, defaults={"tagName":tag})
                        newProduct.tags.add(productTag)
            
            # Adding default(UNPAID) tags to the product #
            # Making product name as a tag #
            for tag in productInfo['productName'].split(' '):
                productTag, created = ProductTags.objects.get_or_create(tagName=tag, defaults={"tagName":tag})
                newProduct.tags.add(productTag)
            
            # Making product category as a tag #
            for tag in productInfo['productCategory'].split(' '):
                productTag, created = ProductTags.objects.get_or_create(tagName=tag, defaults={"tagName":tag})
                newProduct.tags.add(productTag)

            messages.success(request, "Product Added Successfully !!!")
            productInfo = {}
        
        return render(request, 'myshop/addProduct.html', context=productInfo)




class ViewProducts(View):

    def get(self, request, searchKey):
        allProducts = getProductsCategoryWise(searchKey, request.COOKIES['username'])
        return render(request, 'myshop/viewProducts.html', context={'allProducts':allProducts, 'resultLen':len(allProducts)})



class SearchProducts(View):

    def get(self, request):
        searchKey = request.GET['searchKey'].lower()
        allProducts = searchProductWithKeyword(searchKey, request.COOKIES['username'])
        # Maintaining Search History #
        if searchKey != "all":
            search = SearchHistory.objects.filter(pk=searchKey)
            if search:
                search = search[0]
                search.frequency = F('frequency') + 1
                search.save()
                search.refresh_from_db()
                if not search.users.filter(username=request.COOKIES['username']):
                    search.users.add( Users.objects.get(pk=request.COOKIES['username']) )
                    search.save()
            else:
                search = SearchHistory(
                    searchKeyword = searchKey,
                )
                search.save()
                search.users.add( Users.objects.get(pk=request.COOKIES['username']))
                search.save()

        return render(request, 'myshop/viewProducts.html', context={'allProducts':allProducts, 'resultLen':len(allProducts), 'searchKey':request.GET['searchKey']})



class ViewProduct(View):

    def get(self, request, productId):
        selectedProduct = get_object_or_404(Products, pk=productId) # This is just for verification whether the products exits or not #
        selectedProduct = Products.objects.filter(pk=productId).values().first()
        selectedProduct['productImageUrl'] = Products.objects.get(pk=selectedProduct['productId']).productImage.url
        selectedProduct['isInTheCart'] = isProductInTheCart(productId=selectedProduct['productId'], username=request.COOKIES['username'])
        selectedProductDescription = list(map(lambda string: string.replace('\r', ''), selectedProduct['productDescription'].split('\n')))

        relatedProducts = list()
        for product in Products.objects.filter(productCategory = selectedProduct['productCategory']).order_by('-recommendationAmount').values():
            product['productImageUrl'] = Products.objects.get(pk=product['productId']).productImage.url
            product['isInTheCart'] = isProductInTheCart(productId=product['productId'], username=request.COOKIES['username'])
            relatedProducts.append(product)

        productCategory = selectedProduct['productCategory']
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




class BuyNow(View):

    def get(self, request, productId):
        product = Products.objects.get(pk=productId)
        userAddresses = Address.objects.filter(person__username = request.COOKIES['username'])
        return render(request, 'myshop/buyNow.html', context={
            'product' : product,
            'userAddresses' : userAddresses
        })
    

    def post(self, request, productId):
        products = Products.objects.filter(pk=request.POST['productId'])
        user = Users.objects.get(pk=request.COOKIES['username'])
        if products.count() <= 0:
            messages.error(request, "Product does not exists.")
        elif request.POST['address'].lower() == "defaulttext":
            messages.error(request, "Please select the delivery address.")
        elif int(request.POST['productQty']) <= 0:
            messages.error(request, "Product quantity should be greater than one.")
        elif (int(request.POST['productQty']) * products[0].productPrice) > user.walletBalance:
            messages.error(request, "Insufficient Wallet Balance.")
        else:
            productPurchased = products[0]
            newCart = Cart(
                person = user,
                product = productPurchased,
                productQty = int(request.POST['productQty'])
            )
            newCart.save()
            newOrder = Orders(
                totalBillAmount = (int(request.POST['productQty']) * productPurchased.productPrice),
                deliveryAddress = Address.objects.get(pk=request.POST['address']),
                user = user
            )
            newOrder.save()
            newCart.order = newOrder
            newCart.save()

            user.walletBalance = F('walletBalance') - (int(request.POST['productQty']) * productPurchased.productPrice)
            user.save()
            user.refresh_from_db()
            messages.success(request, "Order Placed Successfully.")
            return HttpResponseRedirect(reverse('myshop:myOrders'))
        
        return HttpResponseRedirect(reverse('myshop:buynow', kwargs={'productId':request.POST['productId']}))



class SuggestSearches(View):

    def get(self, request, searchKey):
        suggestions = SearchHistory.objects.filter(searchKeyword__icontains = searchKey)
        if not suggestions.count():
            suggestions = ProductTags.objects.filter(tagName__icontains = searchKey)
            suggestions = list(map(lambda tag: tag.tagName, suggestions))
        else:
            suggestions = list(map(lambda search: search.searchKeyword, suggestions))
        
        return JsonResponse({
            'searchSuggestions' : suggestions
        })



class Logout(View):

    def get(self, request):
        response = HttpResponseRedirect(reverse('LoginSignup:login'))
        del request.session[request.COOKIES['username']]
        response.delete_cookie(key='username')
        response.delete_cookie(key='sessionId')
        return response


