from django.core.management.base import BaseCommand
from django.utils.text import slugify
from handcrafted_app.models import Category,Subcategory
DATA={'Crochets':['Toys','Keychains','Purses','Clothing','Decorations'],'Candles':['Pillar Candles','Container Candles','Taper Candles','Decorative Candles'],'Jewelry & Accessories':['Earrings','Rings','Necklaces','Bracelets'],'Home Decor':['Wall Decorations','Handmade Ornaments','Decorative Items'],'Personalized Gifts':['Gift Boxes','Customized Accessories','Other Gifts']}
class Command(BaseCommand):
    help='Create initial marketplace categories'
    def handle(self,*args,**options):
        for name,subs in DATA.items():
            category,_=Category.objects.get_or_create(slug=slugify(name),defaults={'name':name})
            for sub in subs: Subcategory.objects.get_or_create(category=category,slug=slugify(sub),defaults={'name':sub})
        self.stdout.write(self.style.SUCCESS('Categories ready'))
