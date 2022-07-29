from math import ceil
import time
from turtle import distance
from numpy import NAN, NaN
from LoginSignup.models import Address
from .models import Products, Users, Cart, ProductTags, MyShopCenters
from django.db.models import Q, F
from LoginSignup.utils import isNumberValid
import requests
from datetime import timedelta
import aiohttp
import asyncio
from asgiref.sync import sync_to_async
from pgeocode import GeoDistance




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
    try:
        dist = GeoDistance('in')
        distanceInKM = dist.query_postal_code(origin, destination)
        return float(distanceInKM)
    except Exception as e:
        print("\nException in getDiatnce : ", e)
        return NaN


def getEstimatedDeliveryDate(order, nearestCenter):

    KMsPerDay = 100
    customerPincode = order.deliveryAddress.zipCode
    manufacturerAddresses = Cart.objects.filter(order=order).values('product__manufacturerDetails')
    minDistfrom_CenterToCustomer = getDistanceBetweenPincodes(nearestCenter.zipCode, customerPincode)
    maxDistFrom_ManufacturerToCenter = None

    # Finding the max distance from a manufacturer to the nearest customer's myshop center #
    for address in manufacturerAddresses:
        pincode = address['product__manufacturerDetails'].split(',')[1].split('-')[1]
        distance = getDistanceBetweenPincodes(pincode, nearestCenter.zipCode)
        maxDistFrom_ManufacturerToCenter = distance if maxDistFrom_ManufacturerToCenter == None or maxDistFrom_ManufacturerToCenter < distance else maxDistFrom_ManufacturerToCenter

    totalDeliveryDays = ceil((maxDistFrom_ManufacturerToCenter/KMsPerDay) + (minDistfrom_CenterToCustomer/KMsPerDay))
    return (order.orderedOn + timedelta(days=totalDeliveryDays))
    


def getNearestMyShopCenter(addressPincode):
    minDistfrom_CenterToGivenAddress = None
    nearestCenter = None
    start = time.time()
    centers = MyShopCenters.objects.all().values('centerId', 'zipCode')

    for center in centers:
        distance = getDistanceBetweenPincodes(addressPincode, center['zipCode'])
        if minDistfrom_CenterToGivenAddress == None or minDistfrom_CenterToGivenAddress > distance:
            minDistfrom_CenterToGivenAddress, nearestCenter = distance, center['centerId']
        print(f"\nCenterId : {center['centerId']}, Distance => {distance}")

    print("\nEnded in ", (time.time()-start), "\n")
    return minDistfrom_CenterToGivenAddress, nearestCenter



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