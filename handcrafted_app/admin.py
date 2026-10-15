from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
class MarketplaceUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Marketplace", {"fields": ("role", "phone_number", "profile_image")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Marketplace", {"fields": ("role",)}),)
admin.site.register(User, MarketplaceUserAdmin)
@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ('shop_name','user','is_approved','accepts_custom_orders')
    list_filter = ('is_approved','accepts_custom_orders')
    search_fields = ('shop_name','user__username')
class SubcategoryInline(admin.TabularInline):
    model = Subcategory
    extra = 1
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug':('name',)}
    inlines = [SubcategoryInline]
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name','seller','price','stock','is_active')
    list_filter = ('is_active','subcategory__category')
    search_fields = ('name','seller__shop_name')
    inlines = [ProductImageInline]
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product','seller','product_name','quantity','price')
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id','buyer','status','total_price','created_at')
    list_filter = ('status',)
    inlines = [OrderItemInline]
@admin.register(CustomOrder)
class CustomOrderAdmin(admin.ModelAdmin):
    list_display = ('id','buyer','seller','status','proposed_price')
    list_filter = ('status',)
admin.site.register(Cart)
admin.site.register(CartItem)
