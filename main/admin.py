from django.contrib import admin
from .models import User, Category, Lot, Bid, LotImage

admin.site.register(User)

admin.site.register(Category)
admin.site.register(Lot)
admin.site.register(Bid)
admin.site.register(LotImage)


# Register your models here.
