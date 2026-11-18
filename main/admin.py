from django.contrib import admin
from .models import User, Category, Lot, Bid, LotImage

admin.site.register(User)
admin.site.register(Category)


class LotImageInline(admin.TabularInline):
    model = LotImage
    extra = 1


@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    list_display = ("title", "current_price", "status", "end_time")
    list_filter = ("status", "category")
    search_fields = ("title",)

    inlines = [LotImageInline]


admin.site.register(Bid)
admin.site.register(LotImage)


# Register your models here.
