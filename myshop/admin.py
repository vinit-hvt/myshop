from operator import imod
from django.contrib import admin
from .models import Products, Cart, Orders, ProductTags, SearchHistory

# Register your models here.

admin.site.register(Products)
admin.site.register(Cart)
admin.site.register(Orders)
admin.site.register(ProductTags)
admin.site.register(SearchHistory)
