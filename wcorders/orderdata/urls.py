from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomerViewSet, CategoryViewSet, ProductViewSet, WooCommerceOrderViewSet, OrderItemViewSet, 
    AddressViewSet, PaymentGatewayViewSet, ShippingMethodViewSet, CouponViewSet, TaxViewSet
)

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'orders', WooCommerceOrderViewSet)
router.register(r'order-items', OrderItemViewSet)
router.register(r'addresses', AddressViewSet)
router.register(r'payment-gateways', PaymentGatewayViewSet)
router.register(r'shipping-methods', ShippingMethodViewSet)
router.register(r'coupons', CouponViewSet)
router.register(r'taxes', TaxViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
