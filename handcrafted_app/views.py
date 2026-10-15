from decimal import Decimal, InvalidOperation
from functools import wraps
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .forms import RegisterForm, SellerProfileForm, ProductForm, ImageUploadForm, CheckoutForm, CustomOrderForm, CustomOrderStatusForm
from .models import User, SellerProfile, Category, Subcategory, Product, ProductImage, Cart, CartItem, Order, OrderItem, CustomOrder

def seller_only(fn):
    @wraps(fn)
    @login_required
    def wrapper(request,*args,**kwargs):
        if request.user.role != User.Role.SELLER: return HttpResponseForbidden('Seller access only')
        return fn(request,*args,**kwargs)
    return wrapper

def buyer_only(fn):
    @wraps(fn)
    @login_required
    def wrapper(request,*args,**kwargs):
        if request.user.role != User.Role.BUYER: return HttpResponseForbidden('Buyer access only')
        return fn(request,*args,**kwargs)
    return wrapper

def home(request):
    products = Product.objects.filter(is_active=True, stock__gt=0).select_related('seller','subcategory').prefetch_related('images').order_by('-created_at')
    categories = Category.objects.all()
    for category in categories:
        category.preview = ProductImage.objects.filter(product__is_active=True, product__subcategory__category=category).first()
    return render(request,'home.html', {'products':products[:8], 'hero_image':ProductImage.objects.filter(product__is_active=True).first(), 'categories':categories, 'makers':SellerProfile.objects.all()[:4]})

def catalog(request):
    products=Product.objects.filter(is_active=True).select_related('seller','subcategory__category').prefetch_related('images')
    if request.GET.get('q'): products=products.filter(Q(name__icontains=request.GET['q'])|Q(description__icontains=request.GET['q']))
    if request.GET.get('category'): products=products.filter(subcategory__category__slug=request.GET['category'])
    if request.GET.get('subcategory', '').isdigit(): products=products.filter(subcategory_id=request.GET['subcategory'])
    for key, lookup in [('min_price','price__gte'),('max_price','price__lte')]:
        try:
            value = Decimal(request.GET.get(key, ''))
            if value.is_finite() and value >= 0: products=products.filter(**{lookup:value})
        except InvalidOperation:
            pass
    if request.GET.get('availability') == 'in_stock': products=products.filter(stock__gt=0)
    sort = request.GET.get('sort', 'newest')
    products=products.order_by({'price_asc':'price','price_desc':'-price'}.get(sort,'-created_at'),'-pk')
    page=Paginator(products,12).get_page(request.GET.get('page'))
    query=request.GET.copy();query.pop('page',None)
    return render(request,'catalog.html',{'products':page,'page_obj':page,'query_string':query.urlencode(),'categories':Category.objects.prefetch_related('subcategories'),'selected':request.GET,'selected_category':Category.objects.filter(slug=request.GET.get('category')).first()})

def product_detail(request,pk):
    product=get_object_or_404(Product.objects.select_related('seller','subcategory__category').prefetch_related('images'),pk=pk,is_active=True)
    return render(request,'product_detail.html',{'product':product,'related_products':Product.objects.filter(is_active=True,subcategory=product.subcategory).exclude(pk=pk).select_related('seller','subcategory').prefetch_related('images')[:4]})

def shop(request,pk):
    seller=get_object_or_404(SellerProfile,pk=pk)
    return render(request,'shop.html',{'seller':seller,'products':seller.products.filter(is_active=True).prefetch_related('images')})

def register(request):
    form=RegisterForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            user=form.save()
            if user.role==User.Role.SELLER: SellerProfile.objects.create(user=user,shop_name=form.cleaned_data['shop_name'])
        login(request,user)
        return redirect('home')
    return render(request,'register.html',{'form':form,'heading':'Create account'})

@seller_only
def dashboard(request):
    seller=get_object_or_404(SellerProfile,user=request.user)
    order_items=OrderItem.objects.filter(seller=seller).select_related('order','product').order_by('-order__created_at')
    return render(request,'dashboard.html',{'seller':seller,'products':seller.products.prefetch_related('images').order_by('-created_at'),'order_items':order_items,'order_count':order_items.values('order_id').distinct().count(),'pending_count':order_items.filter(order__status='PENDING').values('order_id').distinct().count(),'request_count':seller.custom_requests.filter(status='PENDING').count()})

@seller_only
def edit_shop(request):
    seller=get_object_or_404(SellerProfile,user=request.user)
    form=SellerProfileForm(request.POST or None,request.FILES or None,instance=seller)
    if request.method=='POST' and form.is_valid(): form.save();messages.success(request,'Shop updated');return redirect('dashboard')
    return render(request,'form.html',{'form':form,'heading':'Edit shop'})

@seller_only
def product_edit(request,pk=None):
    seller=get_object_or_404(SellerProfile,user=request.user)
    product=get_object_or_404(Product,pk=pk,seller=seller) if pk else None
    form=ProductForm(request.POST or None,instance=product)
    upload_forms = [ImageUploadForm({'is_primary':False}, {'image':f}) for f in request.FILES.getlist('images')]
    uploads_valid = all([upload.is_valid() for upload in upload_forms])
    if not uploads_valid: form.add_error(None, 'Upload valid image files. No product changes have been saved.')
    if request.method=='POST' and form.is_valid() and uploads_valid:
        item=form.save(commit=False);item.seller=seller;item.save()
        for upload in upload_forms:
            image=upload.save(commit=False);image.product=item;image.save()
        messages.success(request,'Product saved');return redirect('dashboard')
    return render(request,'form.html',{'form':form,'heading':'Edit product' if pk else 'Add product','multi_images':True,'product':product})

@seller_only
@require_POST
def product_delete(request,pk):
    product=get_object_or_404(Product,pk=pk,seller__user=request.user)
    product.is_active=False;product.save(update_fields=['is_active'])
    messages.info(request,'Product removed from catalog');return redirect('dashboard')

@seller_only
@require_POST
def image_delete(request,pk):
    img=get_object_or_404(ProductImage,pk=pk,product__seller__user=request.user)
    product_id=img.product_id;img.delete();return redirect('product_edit',pk=product_id)

@buyer_only
@require_POST
def cart_add(request,pk):
    product=get_object_or_404(Product,pk=pk,is_active=True,stock__gt=0)
    cart,_=Cart.objects.get_or_create(user=request.user)
    item,_=CartItem.objects.get_or_create(cart=cart,product=product,defaults={'quantity':0})
    try: quantity=int(request.POST.get('quantity','1'))
    except (ValueError, TypeError): quantity=0
    if quantity < 1 or item.quantity+quantity > product.stock:
        if item.quantity == 0: item.delete()
        messages.error(request,'Requested quantity is unavailable')
    else: item.quantity+=quantity;item.save();messages.success(request,'Added to cart')
    return redirect('cart')

@buyer_only
def cart_view(request):
    cart,_=Cart.objects.get_or_create(user=request.user)
    items=list(cart.items.select_related('product__seller').prefetch_related('product__images'))
    for item in items: item.subtotal=item.product.price*item.quantity
    return render(request,'cart.html',{'items':items,'total':sum((i.subtotal for i in items),Decimal('0'))})

@buyer_only
@require_POST
def cart_update(request,pk):
    item=get_object_or_404(CartItem,pk=pk,cart__user=request.user)
    try: qty=int(request.POST.get('quantity','1'))
    except ValueError: qty=0
    if qty<=0: item.delete()
    elif qty<=item.product.stock and item.product.is_active: item.quantity=qty;item.save()
    else: messages.error(request,'Requested quantity is unavailable')
    return redirect('cart')

@buyer_only
def checkout(request):
    cart,_=Cart.objects.get_or_create(user=request.user)
    form=CheckoutForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            items=list(CartItem.objects.filter(cart=cart).select_related('product').order_by('product_id'))
            if not items: messages.error(request,'Your cart is empty');return redirect('cart')
            total=Decimal('0')
            for item in items:
                updated=Product.objects.filter(pk=item.product_id,is_active=True,stock__gte=item.quantity).update(stock=models_F('stock')-item.quantity)
                if not updated:
                    transaction.set_rollback(True);messages.error(request,f'Insufficient stock for {item.product.name}');return redirect('cart')
                total+=item.product.price*item.quantity
            order=Order.objects.create(buyer=request.user,shipping_address=form.cleaned_data['shipping_address'],total_price=total)
            OrderItem.objects.bulk_create([OrderItem(order=order,product=i.product,seller=i.product.seller,product_name=i.product.name,quantity=i.quantity,price=i.product.price) for i in items])
            cart.items.all().delete()
        messages.success(request,'Order placed successfully');return redirect('orders')
    items=list(cart.items.select_related('product__seller').prefetch_related('product__images'))
    for item in items: item.subtotal=item.product.price*item.quantity
    return render(request,'checkout.html',{'form':form,'items':items,'total':sum((i.subtotal for i in items),Decimal('0'))})
from django.db.models import F as models_F

@buyer_only
def orders(request):
    return render(request,'orders.html',{'orders':Order.objects.filter(buyer=request.user).prefetch_related('items').order_by('-created_at')})

@buyer_only
def custom_request(request,pk):
    seller=get_object_or_404(SellerProfile,pk=pk,is_approved=True,accepts_custom_orders=True)
    form=CustomOrderForm(request.POST or None,request.FILES or None)
    if request.method=='POST' and form.is_valid():
        obj=form.save(commit=False);obj.buyer=request.user;obj.seller=seller;obj.save()
        messages.success(request,'Custom request sent');return redirect('my_requests')
    return render(request,'form.html',{'form':form,'heading':f'Custom request for {seller.shop_name}'})

@buyer_only
def my_requests(request):
    return render(request,'requests.html',{'requests':CustomOrder.objects.filter(buyer=request.user).select_related('seller').order_by('-created_at'),'seller_view':False})

@seller_only
def seller_requests(request):
    return render(request,'requests.html',{'requests':CustomOrder.objects.filter(seller__user=request.user).select_related('buyer').order_by('-created_at'),'seller_view':True})

@seller_only
def request_manage(request,pk):
    obj=get_object_or_404(CustomOrder,pk=pk,seller__user=request.user)
    if not obj.seller.custom_orders_enabled: return HttpResponseForbidden('Custom orders not enabled')
    form=CustomOrderStatusForm(request.POST or None,instance=obj)
    if request.method=='POST' and form.is_valid(): form.save();messages.success(request,'Request updated');return redirect('seller_requests')
    return render(request,'form.html',{'form':form,'heading':f'Update custom request #{obj.pk}','custom_order':obj})

def makers(request):
    return render(request,'makers.html',{'makers':SellerProfile.objects.all().order_by('shop_name')})

def about(request):
    return render(request,'about.html')

def for_sellers(request):
    return render(request,'for_sellers.html')

@seller_only
@require_POST
def order_status(request,pk):
    item=get_object_or_404(OrderItem,pk=pk,seller__user=request.user)
    # One shared order can contain items from several shops. Only admin controls global status.
    messages.info(request,'Order status is managed by the administrator for multi-seller orders.')
    return redirect('dashboard')
