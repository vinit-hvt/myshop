from django.db.models.signals import post_save, post_delete
# from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Products
from django.core.cache import cache 



CACHE_TO_BE_DELETED = {
    'homePage' : False,
    'viewProducts' : False,
    'searchProducts' : False,
    'viewProduct' : True
}



@receiver(post_save, sender=Products)
def product_save(sender, instance, created, **kwargs):
    print("\nProduct Saved :: ", instance, "\n")
    for cacheKey in CACHE_TO_BE_DELETED:
        try:
            if CACHE_TO_BE_DELETED[cacheKey]:
                result = cache.get(cacheKey)
                del result[f"{cacheKey}_{instance.productId}"]
                cache.set(cacheKey, cache.get(cacheKey) | result)
            else:
                cache.delete(cacheKey)
        except:
            pass




@receiver(post_delete, sender=Products)
def product_delete(sender, instance, created, **kwargs):
    print("\nProduct Deleted :: ", instance, "\n")
    for cacheKey in CACHE_TO_BE_DELETED:
        try:
            if CACHE_TO_BE_DELETED[cacheKey]:
                result = cache.get(cacheKey)
                del result[f"{cacheKey}_{instance.productId}"]
                cache.set(cacheKey, cache.get(cacheKey) | result)
            else:
                cache.delete(cacheKey)
        except:
            pass

