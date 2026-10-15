from django.urls import path
from django.contrib.auth import views as auth
from . import views as v

urlpatterns = [
    path('', v.home, name='home'),
    path('catalog/', v.catalog, name='catalog'),
    path('makers/', v.makers, name='makers'),
    path('about/', v.about, name='about'),
    path('for-sellers/', v.for_sellers, name='for_sellers'),
    path('product/<int:pk>/', v.product_detail, name='product_detail'),
    path('shop/<int:pk>/', v.shop, name='shop'),
    path('register/', v.register, name='register'),
    path('login/', auth.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth.LogoutView.as_view(), name='logout'),
    path('dashboard/', v.dashboard, name='dashboard'),
    path('shop/edit/', v.edit_shop, name='edit_shop'),
    path('product/new/', v.product_edit, name='product_new'),
    path('product/<int:pk>/edit/', v.product_edit, name='product_edit'),
    path('product/<int:pk>/delete/', v.product_delete, name='product_delete'),
    path('image/<int:pk>/delete/', v.image_delete, name='image_delete'),
    path('cart/', v.cart_view, name='cart'),
    path('cart/add/<int:pk>/', v.cart_add, name='cart_add'),
    path('cart/update/<int:pk>/', v.cart_update, name='cart_update'),
    path('checkout/', v.checkout, name='checkout'),
    path('orders/', v.orders, name='orders'),
    path('custom/<int:pk>/new/', v.custom_request, name='custom_request'),
    path('custom/mine/', v.my_requests, name='my_requests'),
    path('custom/seller/', v.seller_requests, name='seller_requests'),
    path('custom/<int:pk>/manage/', v.request_manage, name='request_manage'),
]
