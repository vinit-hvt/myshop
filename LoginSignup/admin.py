from django.contrib import admin

from .models import PremiumUsers, Users, Address, PremiumPlans

admin.site.register(Users)
admin.site.register(Address)
admin.site.register(PremiumUsers)