from .models import Products, Users, Cart, ProductTags
from django.db.models import Q, F



def isProductInTheCart(productId, username):
    return Cart.objects.filter(person__username = username, product__productId = productId, order__isnull = True).count() >= 1


def deepSearch(searchKey):
    allTags = ProductTags.objects.all()
    matchingTags = []
    for tag in allTags:
        if tag.tagName in searchKey:
            matchingTags.append(tag)
    
    return matchingTags


def searchProductWithKeyword(searchKey, username):
    searchKey = "" if searchKey.lower() == "all" else searchKey
    matchingTags = ProductTags.objects.filter(Q(tagName__icontains = searchKey)).order_by('-products__recommendationAmount')
    isDeepSearchActivated = False

    if not matchingTags.count():
        matchingTags = deepSearch(searchKey)
        isDeepSearchActivated = True

    allProducts = {}
    productsEncountered = {}

    for tag in matchingTags:
        for product in tag.products_set.all().order_by('-recommendationAmount').values():
            if product['productId'] not in productsEncountered and (isDeepSearchActivated == False or ( isDeepSearchActivated and product['isRecommended'] )):
                productsEncountered[product['productId']] = True
                product['productImageUrl'] = Products.objects.get(pk=product['productId']).productImage.url
                product['isInTheCart'] = isProductInTheCart(productId=product['productId'], username=username)
                if product['productCategory'] in  allProducts:
                    allProducts[product['productCategory']].append(product)
                else:
                    allProducts[product['productCategory']] = [product]
    
    print("YEs searched with tag : ", searchKey)
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
