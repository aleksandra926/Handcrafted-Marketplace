from django.db.models import Sum
from .models import CartItem, Category

def marketplace(request):
    count = 0
    if request.user.is_authenticated and request.user.role == 'BUYER':
        count = CartItem.objects.filter(cart__user=request.user).aggregate(total=Sum('quantity'))['total'] or 0
    return {'cart_count':count, 'nav_categories':Category.objects.all()}
