from rest_framework import viewsets, filters
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

from .models import (
    Customer, Category, Product, WooCommerceOrder, OrderItem, 
    Address, PaymentGateway, ShippingMethod, Coupon, Tax
)
from .serializers import (
    CustomerSerializer, CategorySerializer, ProductSerializer, WooCommerceOrderSerializer, OrderItemSerializer, 
    AddressSerializer, PaymentGatewaySerializer, ShippingMethodSerializer, CouponSerializer, TaxSerializer
)

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class WooCommerceOrderViewSet(viewsets.ModelViewSet):
    queryset = WooCommerceOrder.objects.all()
    serializer_class = WooCommerceOrderSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        date_range = self.request.query_params.get('date_range')

        if date_range == '1d':
            filter_date = timezone.now() - timedelta(days=1)
        elif date_range == '1w':
            filter_date = timezone.now() - timedelta(weeks=1)
        elif date_range == '1m':
            filter_date = timezone.now() - timedelta(days=30)
        elif date_range == '1y':
            filter_date = timezone.now() - timedelta(days=360)            
        else:
            return queryset

        return queryset.filter(date_created__gte=filter_date)

class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer

class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

class PaymentGatewayViewSet(viewsets.ModelViewSet):
    queryset = PaymentGateway.objects.all()
    serializer_class = PaymentGatewaySerializer

class ShippingMethodViewSet(viewsets.ModelViewSet):
    queryset = ShippingMethod.objects.all()
    serializer_class = ShippingMethodSerializer

class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer

class TaxViewSet(viewsets.ModelViewSet):
    queryset = Tax.objects.all()
    serializer_class = TaxSerializer
