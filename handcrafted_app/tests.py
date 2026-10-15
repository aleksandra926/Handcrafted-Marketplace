from decimal import Decimal
from io import BytesIO
from tempfile import TemporaryDirectory
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from .models import User, SellerProfile, Category, Subcategory, Product, ProductImage, Cart, CartItem, Order, CustomOrder


class MarketplaceTests(TestCase):
    def setUp(self):
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.media.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.buyer = User.objects.create_user('buyer', password='UsefulPassword42!')
        self.seller_user = User.objects.create_user('maker', password='UsefulPassword42!', role='SELLER')
        self.seller = SellerProfile.objects.create(user=self.seller_user, shop_name='Test Maker', is_approved=True, accepts_custom_orders=True)
        self.category = Category.objects.create(name='Crochets', slug='crochets')
        self.subcategory = Subcategory.objects.create(category=self.category, name='Toys', slug='toys')
        self.product = Product.objects.create(seller=self.seller, subcategory=self.subcategory, name='Test Creation', description='Made with care.', price=Decimal('500'), stock=5)

    def image(self):
        output=BytesIO()
        Image.new('RGB',(20,20),'#F4D7C9').save(output,format='PNG')
        return SimpleUploadedFile('test.png',output.getvalue(),content_type='image/png')

    def test_public_pages_and_branding(self):
        for name,args in [('home',[]),('catalog',[]),('makers',[]),('about',[]),('for_sellers',[]),('login',[]),('register',[]),('product_detail',[self.product.pk]),('shop',[self.seller.pk])]:
            with self.subTest(page=name):
                response=self.client.get(reverse(name,args=args))
                self.assertEqual(response.status_code,200)
                self.assertContains(response,'Handcrafted Marketplace')

    def test_authenticated_pages_render(self):
        self.client.force_login(self.buyer)
        for name in ['cart','checkout','orders','my_requests']:
            self.assertEqual(self.client.get(reverse(name)).status_code,200)
        self.assertEqual(self.client.get(reverse('custom_request',args=[self.seller.pk])).status_code,200)
        self.client.force_login(self.seller_user)
        for name in ['dashboard','product_new','edit_shop','seller_requests']:
            self.assertEqual(self.client.get(reverse(name)).status_code,200)
        self.assertEqual(self.client.get(reverse('product_edit',args=[self.product.pk])).status_code,200)

    def test_buyer_and_seller_access(self):
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.get(reverse('dashboard')).status_code,403)
        self.client.force_login(self.seller_user)
        self.assertEqual(self.client.get(reverse('cart')).status_code,403)
        other=User.objects.create_user('other',role='SELLER')
        SellerProfile.objects.create(user=other,shop_name='Other Shop')
        self.client.force_login(other)
        self.assertEqual(self.client.get(reverse('product_edit',args=[self.product.pk])).status_code,404)
        self.assertEqual(self.client.post(reverse('product_delete',args=[self.product.pk])).status_code,404)

    def test_login_and_registration(self):
        response=self.client.post(reverse('login'),{'username':'buyer','password':'UsefulPassword42!'})
        self.assertRedirects(response,reverse('home'))
        self.client.post(reverse('logout'))
        response=self.client.post(reverse('register'),{'username':'newmaker','email':'maker@example.com','role':'SELLER','shop_name':'New Shop','password1':'UnusualPassWord73!','password2':'UnusualPassWord73!'})
        self.assertRedirects(response,reverse('home'))
        self.assertTrue(SellerProfile.objects.filter(shop_name='New Shop').exists())

    def test_registration_requires_shop_name(self):
        response=self.client.post(reverse('register'),{'username':'incomplete','role':'SELLER','password1':'UnusualPassWord73!','password2':'UnusualPassWord73!'})
        self.assertContains(response,'Shop name is required')
        self.assertFalse(User.objects.filter(username='incomplete').exists())

    def test_catalog_filters_sort_and_invalid_values(self):
        expensive=Product.objects.create(seller=self.seller,subcategory=self.subcategory,name='Another Creation',description='Other',price=900,stock=0)
        response=self.client.get(reverse('catalog'),{'category':'crochets','subcategory':self.subcategory.pk,'min_price':'400','max_price':'600','availability':'in_stock','q':'Creation'})
        self.assertEqual(list(response.context['products']),[self.product])
        response=self.client.get(reverse('catalog'),{'sort':'price_desc'})
        self.assertEqual(list(response.context['products']),[expensive,self.product])
        response=self.client.get(reverse('catalog'),{'min_price':'invalid','max_price':'NaN','subcategory':'invalid'})
        self.assertEqual(response.status_code,200)

    def test_cart_quantity_and_checkout(self):
        self.client.force_login(self.buyer)
        self.client.post(reverse('cart_add',args=[self.product.pk]),{'quantity':'2'})
        item=CartItem.objects.get(cart__user=self.buyer)
        self.assertEqual(item.quantity,2)
        self.client.post(reverse('cart_update',args=[item.pk]),{'quantity':'3'})
        response=self.client.get(reverse('checkout'))
        self.assertEqual(response.context['total'],Decimal('1500'))
        response=self.client.post(reverse('checkout'),{'full_name':'Test Buyer','address':'Test Street 1','city':'Skopje','postal_code':'1000','phone_number':'070123456','notes':'Leave at door'})
        self.assertRedirects(response,reverse('orders'))
        order=Order.objects.get(buyer=self.buyer)
        self.assertEqual(order.total_price,Decimal('1500'))
        self.assertIn('Skopje',order.shipping_address)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock,2)
        self.assertFalse(CartItem.objects.filter(cart__user=self.buyer).exists())

    def test_stock_validation_and_removal(self):
        self.client.force_login(self.buyer)
        self.client.post(reverse('cart_add',args=[self.product.pk]),{'quantity':'999'})
        self.assertFalse(CartItem.objects.filter(cart__user=self.buyer).exists())
        self.client.post(reverse('cart_add',args=[self.product.pk]))
        item=CartItem.objects.get(cart__user=self.buyer)
        self.client.post(reverse('cart_update',args=[item.pk]),{'quantity':6})
        item.refresh_from_db();self.assertEqual(item.quantity,1)
        self.client.post(reverse('cart_update',args=[item.pk]),{'quantity':0})
        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())

    def test_checkout_rolls_back_on_insufficient_stock(self):
        self.client.force_login(self.buyer)
        cart=Cart.objects.create(user=self.buyer)
        CartItem.objects.create(cart=cart,product=self.product,quantity=6)
        response=self.client.post(reverse('checkout'),{'full_name':'Test','address':'Street','city':'Skopje','postal_code':'1000','phone_number':'123'})
        self.assertRedirects(response,reverse('cart'))
        self.assertFalse(Order.objects.exists())
        self.product.refresh_from_db();self.assertEqual(self.product.stock,5)

    def test_product_management_and_image_validation(self):
        self.client.force_login(self.seller_user)
        data={'name':'Uploaded Creation','description':'Description','subcategory':self.subcategory.pk,'price':'600','stock':'3','is_active':'on','images':[self.image(),self.image()]}
        self.assertRedirects(self.client.post(reverse('product_new'),data),reverse('dashboard'))
        product=Product.objects.get(name='Uploaded Creation')
        self.assertEqual(product.images.count(),2)
        self.assertContains(self.client.get(reverse('product_detail',args=[product.pk])),'/media/products/')
        data['name']='Invalid Upload';data['images']=[SimpleUploadedFile('fake.png',b'not an image',content_type='image/png')]
        self.assertContains(self.client.post(reverse('product_new'),data),'Upload valid image files')
        self.assertFalse(Product.objects.filter(name='Invalid Upload').exists())
        self.client.post(reverse('product_delete',args=[product.pk]))
        product.refresh_from_db();self.assertFalse(product.is_active)

    def test_custom_order_approval_and_management(self):
        self.client.force_login(self.buyer)
        response=self.client.post(reverse('custom_request',args=[self.seller.pk]),{'product_type':'Toy','description':'A personal idea','reference_image':self.image()})
        self.assertRedirects(response,reverse('my_requests'))
        custom=CustomOrder.objects.get()
        self.client.force_login(self.seller_user)
        self.assertContains(self.client.get(reverse('request_manage',args=[custom.pk])),'A personal idea')
        self.client.post(reverse('request_manage',args=[custom.pk]),{'status':'ACCEPTED','proposed_price':'750'})
        custom.refresh_from_db();self.assertEqual(custom.status,'ACCEPTED')
        self.assertFalse(Order.objects.exists())
        self.seller.accepts_custom_orders=False;self.seller.save()
        self.assertEqual(self.client.get(reverse('request_manage',args=[custom.pk])).status_code,403)
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.get(reverse('custom_request',args=[self.seller.pk])).status_code,404)

    def test_pagination_preserves_filters(self):
        Product.objects.bulk_create([Product(seller=self.seller,subcategory=self.subcategory,name=f'Creation {i}',description='Test',price=100,stock=1) for i in range(13)])
        response=self.client.get(reverse('catalog'),{'category':'crochets','page':'2'})
        self.assertEqual(response.context['page_obj'].number,2)
        self.assertEqual(len(response.context['products']),2)
        self.assertContains(response,'category=crochets&amp;page=1')

    def test_cross_shop_image_and_request_access(self):
        other = User.objects.create_user('unrelated',role='SELLER')
        SellerProfile.objects.create(user=other,shop_name='Unrelated Shop')
        image=ProductImage.objects.create(product=self.product,image=self.image())
        custom=CustomOrder.objects.create(buyer=self.buyer,seller=self.seller,product_type='Toy',description='Idea')
        self.client.force_login(other)
        self.assertEqual(self.client.post(reverse('image_delete',args=[image.pk])).status_code,404)
        self.assertEqual(self.client.get(reverse('request_manage',args=[custom.pk])).status_code,404)

    def test_checkout_rolls_back_preceding_item(self):
        unavailable=Product.objects.create(seller=self.seller,subcategory=self.subcategory,name='Unavailable',description='Test',price=100,stock=0)
        cart=Cart.objects.create(user=self.buyer)
        CartItem.objects.create(cart=cart,product=self.product,quantity=2)
        CartItem.objects.create(cart=cart,product=unavailable,quantity=1)
        self.client.force_login(self.buyer)
        self.client.post(reverse('checkout'),{'full_name':'Test','address':'Street','city':'Skopje','postal_code':'1000','phone_number':'123'})
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock,5)
        self.assertFalse(Order.objects.exists())
        self.assertEqual(cart.items.count(),2)
