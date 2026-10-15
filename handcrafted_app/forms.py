from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, SellerProfile, Product, ProductImage, CustomOrder

class RegisterForm(UserCreationForm):
    role = forms.ChoiceField(choices=User.Role.choices)
    shop_name = forms.CharField(max_length=150, required=False)
    class Meta:
        model = User
        fields = ['username','email','first_name','last_name','role','shop_name','password1','password2']
    def clean(self):
        data = super().clean()
        if data.get('role') == User.Role.SELLER and not data.get('shop_name'):
            self.add_error('shop_name', 'Shop name is required for sellers.')
        return data

class SellerProfileForm(forms.ModelForm):
    class Meta:
        model = SellerProfile
        fields = ['shop_name','description','profile_image']

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name','description','subcategory','price','stock','is_active']
        widgets = {'description': forms.Textarea(attrs={'rows':4})}

class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image','is_primary']

class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    address = forms.CharField(max_length=250)
    city = forms.CharField(max_length=100)
    postal_code = forms.CharField(max_length=20)
    phone_number = forms.CharField(max_length=30)
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows':3}))

    def clean(self):
        data=super().clean()
        data['shipping_address']='\n'.join(str(data.get(key,'')) for key in ['full_name','address','city','postal_code','phone_number','notes'])
        return data

class CustomOrderForm(forms.ModelForm):
    class Meta:
        model = CustomOrder
        fields = ['product_type','color_preferences','specific_details','dimensions','description','reference_image']

class CustomOrderStatusForm(forms.ModelForm):
    class Meta:
        model = CustomOrder
        fields = ['status','proposed_price']
