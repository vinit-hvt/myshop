from .models import Products, Users, Cart


def isProductInTheCart(productId, username):
    return Cart.objects.filter(person__username = username, product__productId = productId, order__isnull = True).count() >= 1


