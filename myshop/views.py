from datetime import datetime
from math import ceil
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.urls import reverse
from LoginSignup.models import Address, PremiumUsers, UserType
from .models import MyShopCenters, Products, SearchHistory, Users, Cart, Orders, ProductTags
from django.contrib import messages
from django.db.models import Q, F
from .utils import getCashbackAndShopyCoinsRewarded, getEstimatedDeliveryDate, isProductInTheCart, searchProductWithKeyword, getProductsCategoryWise, isManufacturerAddressValid, getNearestMyShopCenter, initializeCacheIfNot
from LoginSignup.utils import setCrownSymbol
from django.core.cache import cache

# Create your views here.


class Home(View):

    def get(self, request):
        user = Users.objects.get(pk=request.COOKIES['username'])
        setCrownSymbol(request, user)
        if user.userType == 'UserType.PREMIUM':
            if PremiumUsers.objects.filter(user=user, endDate__lte=datetime.now()).count():
                premiumAccount = PremiumUsers.objects.get(user=user)
                premiumAccount.delete()
                user.userType = UserType.REGULAR
                user.save()
                if 'planEndWarning' not in request.session:
                    request.session['planEndWarning'] = True
                    messages.error(request, "Your Premium Plan has ended.")

        if cache.get("homePage"):
            print("----- Data From Cache -----")
            allProducts = cache.get("homePage")
        else:
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

            cache.set('homePage', allProducts, 60*10)
            
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
        if not isManufacturerAddressValid(request.POST['manufacturerNameAddress']):
            productInfo['manufacturerNameAddress'] = ''
            messages.error(request, "Invalid manufacturer address. Example : Manufacturer Name, City-Pincode, State, Country.")
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
        # Initializing the viewProduct in the cache if not initialized yet. #
        initializeCacheIfNot("viewProducts")

        if f"viewProducts_{searchKey}" in cache.get("viewProducts"):
            print("----- Data From Cache -----")
            context = cache.get("viewProducts")[f"viewProducts_{searchKey}"]
        else:
            allProducts = getProductsCategoryWise(searchKey, request.COOKIES['username'])
            context = {
                'allProducts':allProducts,
                'resultLen':len(allProducts)
            }
            cache.set("viewProducts", cache.get('viewProducts') | {f"viewProducts_{searchKey}":context})

        return render(request, 'myshop/viewProducts.html', context=context)



class SearchProducts(View):

    MINIMUM_FREQUENCY_TO_CACHE_SEARCH = 5

    def get(self, request):
        searchKey = request.GET['searchKey'].lower()

        # Initializing the viewProduct in the cache if not initialized yet. #
        initializeCacheIfNot("searchProducts", 60*30)

        if f"searchProducts_{searchKey}" in cache.get("searchProducts"):
            print("----- Data From Cache -----")
            allProducts = cache.get("searchProducts")[f"searchProducts_{searchKey}"]
            isSearchResultSavedInCache = True
        else:
            allProducts = searchProductWithKeyword(searchKey, request.COOKIES['username'])
            isSearchResultSavedInCache = False

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
            if search.frequency > self.MINIMUM_FREQUENCY_TO_CACHE_SEARCH and not isSearchResultSavedInCache:
                cache.set("searchProducts", cache.get('searchProducts') | {f"searchProducts_{searchKey}":allProducts})

        return render(request, 'myshop/viewProducts.html', context={'allProducts':allProducts, 'resultLen':len(allProducts), 'searchKey':request.GET['searchKey']})



class ViewProduct(View):

    def get(self, request, productId):
        
        # Initializing the viewProduct in the cache if not initialized yet. #
        initializeCacheIfNot("viewProduct")

        if f"viewProduct_{productId}" in cache.get("viewProduct"):
            print("----- Data From Cache -----")
            context = cache.get("viewProduct")[f"viewProduct_{productId}"]
        else:
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
            context = {
                'selectedProduct' : selectedProduct,
                'relatedProducts' : relatedProducts,
                'selectedProductDescription' : selectedProductDescription,
                'productCategory' : productCategory
            }
            cache.set("viewProduct", cache.get('viewProduct') | {f"viewProduct_{productId}":context})

        return render(request, 'myshop/viewProduct.html', context=context)



class UserCart(View):

    def get(self, request):

        setCrownSymbol(request, Users.objects.get(pk=request.COOKIES['username']))
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
        setCrownSymbol(request, Users.objects.get(pk=request.COOKIES['username']))
        cartItems = Cart.objects.filter(person__username = request.COOKIES['username'], order__isnull = True).values()
        userAddresses = Address.objects.filter(person__username = request.COOKIES['username']).values()
        premiumAccount = PremiumUsers.objects.filter(user__username = request.COOKIES['username'])
        planEnrolledIn = premiumAccount[0].planName.split('.')[1].lower() if premiumAccount.count() else "regular"
            
        index, totalUnits, sumOfIndividualPrice, totalBillAmount = 1, 0, 0, 0
        # print(cartItems)
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
            'totalBillAmount' : totalBillAmount,
            "planEnrolledIn" : planEnrolledIn
        })
    

    def post(self, request):

        if 'helper' in request.session and 'helperName' in request.session:
            del request.session['helper'], request.session['helperName']

        user = Users.objects.get(pk=request.COOKIES['username'])
        totalBillAmount = float(request.POST['totalBillAmount'])
        remainingAmount = totalBillAmount - user.walletBalance

        if remainingAmount > 0:
            messages.error(request, f"Insufficient Wallet Balance. Available Wallet Balance is Rs. {format(user.walletBalance, '.2f')}")
            request.session['helper'] = reverse('userinfo:addMoney', args=[format(remainingAmount, '.2f')])
            request.session['helperName'] = f"Add Money (Rs. {format(remainingAmount, '.2f')})"
        elif request.POST['address'].lower() == "defaulttext" or Address.objects.filter(pk=request.POST['address']).count == 0:
            messages.error(request, "Please select the delivery address.")
        else:
            response = getCashbackAndShopyCoinsRewarded(user, totalBillAmount)
            shopyCoins = response['shopyCoins']
            cashback = response['cashback']

            newOrder = Orders(
                totalBillAmount = float(format(totalBillAmount, '.2f')),
                user = user,
                deliveryAddress = Address.objects.get(pk=request.POST['address']),
                deliveryCharges = float(request.POST['deliveryCharges']),
                orderDiscount = float(request.POST['orderDiscountInput']),
                deliveryDiscount = float(request.POST['deliveryDiscountInput']),
                crownSymbol = request.POST['crownSymbol'],
                cashbackRewarded = cashback,
                shopyCoinsRewarded = shopyCoins
            )
            newOrder.save()
            
            Cart.objects.filter(person__username = user.username, order__isnull = True).update(order = newOrder)
            user.walletBalance = F('walletBalance') - totalBillAmount
            user.shopyCoins = F('shopyCoins') + shopyCoins
            user.save()
            user.refresh_from_db()

            nearestMyShopCenter = MyShopCenters.objects.get(pk=request.POST['centerId'])
            newOrder.estimatedDeliveryDate = getEstimatedDeliveryDate(newOrder, nearestMyShopCenter, user.userType.split('.')[1].lower())
            newOrder.save()
            if user.userType == 'UserType.PREMIUM':
                if cashback > 0:
                    messages.success(request, f"Order Placed Successfully. Hurrah you've recieved a cashback of Rs. {cashback} and {shopyCoins} Shopy Coins. Cashback will be credited after order delivery.")
                else:
                    messages.success(request, f"Order Placed Successfully. Hurrah you've recieved {shopyCoins} Shopy Coins.")
            else:
                messages.success(request, f"Order Placed Successfully.")
            return HttpResponseRedirect(reverse('myshop:myOrders'))
        
        return HttpResponseRedirect(reverse('myshop:placeOrder'))


class MyOrders(View):

    def get(self, request):
        today = datetime.now()
        user = Users.objects.get(pk=request.COOKIES['username'])
        setCrownSymbol(request, user)

        for order in Orders.objects.filter(user=user, estimatedDeliveryDate__lte = today, isOrderDelivered = False):
            cashback = order.cashbackRewarded
            user.walletBalance = F('walletBalance') + cashback
            user.save()
            user.refresh_from_db()
            order.isOrderDelivered = True
            order.save()
        allOrders = Orders.objects.filter(user__username = request.COOKIES['username']).order_by('-orderedOn').values()
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
            user = Users.objects.get(pk = request.COOKIES['username'])
            # If order is already delivered #
            if orderDetails.isOrderDelivered:
                messages.error(request, "Order is already delivered.")
            else:
                # Steps to cancel the order #
                Cart.objects.filter(order__orderId = orderDetails.orderId).delete() # Remove the products from the Cart Table #
                Users.objects.filter(pk = request.COOKIES['username']).update(walletBalance = F('walletBalance') + orderDetails.totalBillAmount, shopyCoins = F('shopyCoins') - orderDetails.shopyCoinsRewarded) # Refunding the order's bill amount to the user's account #

                if orderDetails.shopyCoins > 0:
                    messages.success(request, f"Order is Cancelled. Bill amount is refunded to your account. {orderDetails.shopyCoinsRewarded} Shopy Coins has been taken back.")
                else:
                    messages.success(request, f"Order is Cancelled. Bill amount is refunded to your account.")
                orderDetails.delete() # Deleting order details from the Orders Table #

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
        index, totalUnits, sumOfIndividualPrice = 1, 0, 0
        order = Orders.objects.get(pk=orderId)
        # premiumAccount = PremiumUsers.objects.filter(user = Users.objects.get(pk=request.COOKIES['username']))
        # planEnrolledIn = '' if not premiumAccount.count() else premiumAccount[0].planName.split('.')[1].lower()
        if order.crownSymbol == '♕':
            orderDiscountPercentage, deliveryDiscountPercentage, shopyCoinsPercentage = "5%", "5%", "1%"
        elif order.crownSymbol == '♚':
            orderDiscountPercentage, deliveryDiscountPercentage, shopyCoinsPercentage = "8%", "8%", "3%"
        elif order.crownSymbol == '👑':
            orderDiscountPercentage, deliveryDiscountPercentage, shopyCoinsPercentage = "10%", "100%", "5%"
        else:
            orderDiscountPercentage, deliveryDiscountPercentage, shopyCoinsPercentage = "", "", ""

        for item in cartItems:
            product = Products.objects.get(pk=item['product_id'])
            item['index'] = index
            item['total'] = (item['productQty'] * product.productPrice) 
            item['product'] = product 
            totalUnits += item['productQty']
            sumOfIndividualPrice += product.productPrice
            index += 1

        if index == 1:
            messages.error(request, "Please place an order first.")
            return HttpResponseRedirect(reverse('myshop:home'))

        return render(request, 'myshop/orderDetailsBill.html', context={
            'orderDetails' : cartItems,
            'totalUnits' : totalUnits,
            'sumOfIndividualPrice' : sumOfIndividualPrice,
            'totalBillAmount' : order.totalBillAmount,
            'deliveryCharges' : order.deliveryCharges,
            'shopyCoinsRewarded' : order.shopyCoinsRewarded,
            'cashbackRewarded' : order.cashbackRewarded,
            'orderDiscount' : order.orderDiscount,
            'deliveryDiscount' : order.deliveryDiscount,
            'crownSymbol' : order.crownSymbol,
            'orderId' : orderId,
            'userType' : Users.objects.get(pk = request.COOKIES['username']).userType,
            'isOrderDelivered' : order.isOrderDelivered,
            'orderDiscountPercentage' : orderDiscountPercentage,
            'deliveryDiscountPercentage' : deliveryDiscountPercentage,
            'shopyCoinsPercentage' : shopyCoinsPercentage
        })




class BuyNow(View):

    def get(self, request, productId):
        product = Products.objects.get(pk=productId)
        userAddresses = Address.objects.filter(person__username = request.COOKIES['username'])
        premiumAccount = PremiumUsers.objects.filter(user__username = request.COOKIES['username'])
        planEnrolledIn = premiumAccount[0].planName.split('.')[1].lower() if premiumAccount.count() else "regular"

        return render(request, 'myshop/buyNow.html', context={
            'product' : product,
            'userAddresses' : userAddresses,
            'planEnrolledIn' : planEnrolledIn
        })
    

    def post(self, request, productId):

        if 'helper' in request.session and 'helperName' in request.session:
            del request.session['helper'], request.session['helperName']

        products = Products.objects.filter(pk=request.POST['productId'])
        user = Users.objects.get(pk=request.COOKIES['username'])

        if products.count() <= 0:
            messages.error(request, "Product does not exists.")
        elif request.POST['address'].lower() == "defaulttext":
            messages.error(request, "Please select the delivery address.")
        elif int(request.POST['productQty']) <= 0:
            messages.error(request, "Product quantity should be greater than one.")
        
        productPurchased = products[0]
        totalBillAmount = (int(request.POST['productQty']) * productPurchased.productPrice) + float(request.POST['deliveryCharges']) - float(request.POST['orderDiscountInput']) - float(request.POST['deliveryDiscountInput'])
        totalBillAmount = float(format(totalBillAmount, '.2f'))
        remainigAmount = totalBillAmount - user.walletBalance

        if remainigAmount > 0:
            messages.error(request, f"Insufficient Wallet Balance. Available Wallet Balance is Rs. {format(user.walletBalance, '.2f')}")
            request.session['helper'] = reverse('userinfo:addMoney', args=[format(remainigAmount, '.2f')])
            request.session['helperName'] = f"Add Money (Rs. {format(remainigAmount, '.2f')})"
        else:
            newCart = Cart(
                person = user,
                product = productPurchased,
                productQty = int(request.POST['productQty'])
            )
            newCart.save()
            response = getCashbackAndShopyCoinsRewarded(user, totalBillAmount)
            shopyCoins = response['shopyCoins']
            cashback = response['cashback']
            newOrder = Orders(
                totalBillAmount = totalBillAmount,
                deliveryAddress = Address.objects.get(pk=request.POST['address']),
                user = user,
                deliveryCharges = float(request.POST['deliveryCharges']),
                orderDiscount = float(request.POST['orderDiscountInput']),
                deliveryDiscount = float(request.POST['deliveryDiscountInput']),
                crownSymbol = request.POST['crownSymbol'],
                cashbackRewarded = cashback,
                shopyCoinsRewarded = shopyCoins
            )
            newOrder.save()
            newCart.order = newOrder
            newCart.save()

            user.walletBalance = F('walletBalance') - totalBillAmount
            user.shopyCoins = F('shopyCoins') + shopyCoins
            user.save()
            user.refresh_from_db()
            newOrder.estimatedDeliveryDate = getEstimatedDeliveryDate(newOrder, MyShopCenters.objects.get(pk=request.POST['centerId']), user.userType.split('.')[1].lower())
            newOrder.save()

            if user.userType == 'UserType.PREMIUM':
                if cashback > 0:
                    messages.success(request, f"Order Placed Successfully. Hurrah you've recieved a cashback of Rs. {cashback} and {shopyCoins} Shopy Coins. Cashback will be credited after order delivery.")
                else:
                    messages.success(request, f"Order Placed Successfully. Hurrah you've recieved {shopyCoins} Shopy Coins.")
            else:
                messages.success(request, f"Order Placed Successfully.")

            return HttpResponseRedirect(reverse('myshop:myOrders'))
        
        return HttpResponseRedirect(reverse('myshop:buynow', kwargs={'productId':request.POST['productId']}))


class SuggestSearches(View):

    def get(self, request, searchKey):

        searchKey = searchKey.lower()

        # Initializing the viewProduct in the cache if not initialized yet. #
        initializeCacheIfNot("suggestSearches")

        if f"suggestSearches_{searchKey}" in cache.get("suggestSearches"):
            print("----- Data From Cache -----")
            response = cache.get("suggestSearches")[f"suggestSearches_{searchKey}"]
        else:
            suggestions = SearchHistory.objects.filter(searchKeyword__contains = searchKey).order_by('-frequency')
            if not suggestions.count():
                suggestions = ProductTags.objects.filter(tagName__contains = searchKey)
                suggestions = list(map(lambda tag: tag.tagName, suggestions))
            else:
                suggestions = list(map(lambda search: search.searchKeyword, suggestions))
            response = {
                'searchSuggestions' : suggestions
            }
            cache.set("suggestSearches", cache.get('suggestSearches') | {f"suggestSearches_{searchKey}":response})

        return JsonResponse(response)


class FindNearestCenter(View):

    MINIMUM_CHARGES = 30
    CHARGES_PER_KM = 0.3

    def get(self, request):

        # Initializing the viewProduct in the cache if not initialized yet. #
        initializeCacheIfNot("findNearestCenter")

        if f"findNearestCenter_{request.GET['addressId']}" in cache.get("findNearestCenter"):
            print("----- Data From Cache -----")
            response = cache.get("findNearestCenter")[f"findNearestCenter_{request.GET['addressId']}"]
        else:
            try:
                address = Address.objects.get(pk=request.GET['addressId'])
                minDistfrom_CenterToCustomer, nearestCenterId = getNearestMyShopCenter(addressPincode=address.zipCode)
                deliveryCharges = ceil(minDistfrom_CenterToCustomer * self.CHARGES_PER_KM)
                print("\nDelivery Charge : ",deliveryCharges)
                response = {
                    "deliveryCharges" : deliveryCharges if deliveryCharges >= self.MINIMUM_CHARGES else 0,
                    "centerId" : nearestCenterId
                }
            except Exception as e:
                print("\nException = ", e)
                response = {"deliveryCharges":"0", "centerId":1}

            cache.set("findNearestCenter", cache.get('findNearestCenter') | {f"findNearestCenter_{request.GET['addressId']}":response})

        return JsonResponse(response)


class Logout(View):

    def get(self, request):
        response = HttpResponseRedirect(reverse('LoginSignup:login'))
        del request.session[request.COOKIES['username']]
        response.delete_cookie(key='username')
        response.delete_cookie(key='sessionId')
        return response