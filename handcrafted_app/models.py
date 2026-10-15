from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

class User(AbstractUser):
    class Role(models.TextChoices):
        BUYER = 'BUYER', 'Buyer'
        SELLER = 'SELLER', 'Seller'
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.BUYER)
    phone_number = models.CharField(max_length=30, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True)

class SellerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='seller_profile')
    shop_name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to='shops/', blank=True)
    is_approved = models.BooleanField(default=False)
    accepts_custom_orders = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.shop_name
    @property
    def custom_orders_enabled(self): return self.is_approved and self.accepts_custom_orders

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    def __str__(self): return self.name

class Subcategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='subcategories')
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    class Meta:
        constraints = [models.UniqueConstraint(fields=['category','slug'], name='unique_subcategory_slug')]
    def __str__(self): return f'{self.category} / {self.name}'

class Product(models.Model):
    seller = models.ForeignKey(SellerProfile, on_delete=models.PROTECT, related_name='products')
    subcategory = models.ForeignKey(Subcategory, on_delete=models.PROTECT, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    is_primary = models.BooleanField(default=False)

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    class Meta:
        constraints = [models.UniqueConstraint(fields=['cart','product'], name='unique_cart_product')]

class Order(models.Model):
    class Status(models.TextChoices):
        PENDING='PENDING','Pending'
        CONFIRMED='CONFIRMED','Confirmed'
        SHIPPED='SHIPPED','Shipped'
        COMPLETED='COMPLETED','Completed'
        CANCELLED='CANCELLED','Cancelled'
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='orders')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    seller = models.ForeignKey(SellerProfile, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

class CustomOrder(models.Model):
    class Status(models.TextChoices):
        PENDING='PENDING','Pending'
        ACCEPTED='ACCEPTED','Accepted'
        REJECTED='REJECTED','Rejected'
        IN_PROGRESS='IN_PROGRESS','In progress'
        COMPLETED='COMPLETED','Completed'
        CANCELLED='CANCELLED','Cancelled'
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='custom_requests')
    seller = models.ForeignKey(SellerProfile, on_delete=models.PROTECT, related_name='custom_requests')
    product_type = models.CharField(max_length=150)
    color_preferences = models.CharField(max_length=200, blank=True)
    specific_details = models.TextField(blank=True)
    dimensions = models.CharField(max_length=120, blank=True)
    description = models.TextField()
    reference_image = models.ImageField(upload_to='custom_orders/', blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    proposed_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0.01)])
    created_at = models.DateTimeField(auto_now_add=True)
