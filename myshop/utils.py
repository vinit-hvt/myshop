from functools import reduce
from .models import Products, Users, Cart, ProductTags
from django.db.models import Q, F



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
