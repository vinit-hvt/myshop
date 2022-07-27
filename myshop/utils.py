from functools import reduce
from math import ceil
from .models import Products, Users, Cart, ProductTags, MyShopCenters
from django.db.models import Q, F
from LoginSignup.utils import isNumberValid
import requests
from datetime import timedelta

# Global Variables #
MAX_DISTANCE = None


def isProductInTheCart(productId, username):
    return Cart.objects.filter(person__username = username, product__productId = productId, order__isnull = True).count() >= 1


def deepSearch(searchKey, matchingTags):
    allTags = ProductTags.objects.all()
    for tag in allTags:
        if tag.tagName.lower() in searchKey:
            matchingTags.add(tag)
    

def searchProductWithKeyword(searchKey, username):
    searchKey = "" if searchKey.lower() == "all" else searchKey
    matchingTags = set(ProductTags.objects.filter(Q(tagName__icontains = searchKey)).order_by('-products__recommendationAmount'))

    print("Deep Search : ", searchKey)
    deepSearch(searchKey, matchingTags)
    print(matchingTags)
    allProducts = {}

    # Making the query to fetch the matching products #
    query = Q(tags__tagName = searchKey)
    for tag in matchingTags:
        query = query | Q(tags__tagName = tag.tagName)
    
    # Getting the matching products #
    for product in Products.objects.filter(query).distinct().order_by('-recommendationAmount').values():
        product['productImageUrl'] = Products.objects.get(pk=product['productId']).productImage.url
        product['isInTheCart'] = isProductInTheCart(productId=product['productId'], username=username)
        if product['productCategory'] in  allProducts:
            allProducts[product['productCategory']].append(product)
        else:
            allProducts[product['productCategory']] = [product]
    
    return allProducts



def getProductsCategoryWise(productCategory, username):
    matchingProducts = Products.objects.filter(productCategory__icontains = productCategory).order_by('-recommendationAmount')
    allProducts = {}

    for product in matchingProducts.values():
        product['productImageUrl'] = Products.objects.get(pk=product['productId']).productImage.url
        product['isInTheCart'] = isProductInTheCart(productId=product['productId'], username=username)
        if product['productCategory'] in  allProducts:
            allProducts[product['productCategory']].append(product)
        else:
            allProducts[product['productCategory']] = [product]

    return allProducts



def getDistanceBetweenPincodes(origin, destination):
    url = "https://api.distancematrix.ai/maps/api/distancematrix/json?"
    origin = str(origin)
    destination = str(destination)
    apiKey = "Ukh8rqcoSPY2mar4pKXAbzcAY5rkc"
    completeURL = f"{url}origins={origin}&destinations={destination}&key={apiKey}"

    response = requests.get(url=completeURL).json()
    distanceInKM = str(response['rows'][0]['elements'][0]['distance']['text']).split(" ")[0]
    return float(distanceInKM)



def getEstimatedDeliveryDate(order):
    '''
        Order Delivery will be done in 2 phases:
        1 phase : Manufacturer to customer's nearest MyShop's Center.
        2 phase : Customer's nearest MyShop's center to Customer's address.
    '''
    KMsPerDay = 100
    customerPincode = order.deliveryAddress.zipCode
    # Finding the nearest myshop's center to customer's address #
    minDistfrom_CenterToCustomer = None
    nearestCenter = None
    for center in MyShopCenters.objects.all():
        distance = getDistanceBetweenPincodes(center.zipCode, customerPincode)
        if minDistfrom_CenterToCustomer == None or minDistfrom_CenterToCustomer > distance:
            minDistfrom_CenterToCustomer, nearestCenter = distance, center  
        else:
            minDistfrom_CenterToCustomer, nearestCenter = minDistfrom_CenterToCustomer, nearestCenter

    print(f"Nearest MyShop's Center : {nearestCenter}")

    # Finding the max distance from a manufacturer to the nearest customer's myshop center #
    maxDistFrom_ManufacturerToCenter = None
    for cartItem in Cart.objects.filter(order=order):
        pincode = cartItem.product.manufacturerDetails.split(',')[1].split('-')[1]
        distance = getDistanceBetweenPincodes(nearestCenter.zipCode, pincode)
        maxDistFrom_ManufacturerToCenter = distance if maxDistFrom_ManufacturerToCenter == None or maxDistFrom_ManufacturerToCenter < distance else maxDistFrom_ManufacturerToCenter

    totalDeliveryDays = ceil((maxDistFrom_ManufacturerToCenter/KMsPerDay) + (minDistfrom_CenterToCustomer/KMsPerDay))
    print("\Total Delivery Days => ", totalDeliveryDays)
    return (order.orderedOn + timedelta(days=totalDeliveryDays))



def isManufacturerAddressValid(address):
    lst = address.split(',') # MyCorp, Ajmer-305001, India or MyCorp, Ajmer-305001, Rajasthan, India
    if len(lst) < 3:
        return False
    lst = lst[1].split('-') # Getting the city with pincode #
    if len(lst) != 2: # Ajmer and 305001 #
        return False
    if not isNumberValid(lst[1]): # Validating pincode #
        return False
    
    return True