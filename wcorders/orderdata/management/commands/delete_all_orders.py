from django.core.management.base import BaseCommand
from orderdata.models import (
    WooCommerceOrder, OrderItem, Address, ShippingMethod, Coupon, Tax, Customer, PaymentGateway, Product, Category
)
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Delete all existing orders and their respective order data for a specific user'

    def handle(self, *args, **kwargs):
        user_id = 2  # Specify the user ID for whom you want to delete data
        user = User.objects.filter(id=user_id).first()
        
        if not user:
            self.stdout.write(self.style.ERROR(f'No user found with ID {user_id}.'))
            return
        
        self.stdout.write(self.style.NOTICE(f'Deleting all orders and related data for user ID {user_id}...'))

        # Find all orders for the specific user
        orders = WooCommerceOrder.objects.filter(user=user)

        # Retrieve product IDs associated with the user's orders
        product_ids = OrderItem.objects.filter(order__in=orders).values_list('product_id', flat=True)

        # Delete related order data for the specific user's orders
        OrderItem.objects.filter(order__in=orders).delete()
        Address.objects.filter(order__in=orders).delete()
        ShippingMethod.objects.filter(order__in=orders).delete()
        Coupon.objects.filter(order__in=orders).delete()
        Tax.objects.filter(order__in=orders).delete()

        # Delete orders for the specific user
        orders.delete()

        # Delete related data directly associated with the user
        Customer.objects.filter(user=user).delete()
        PaymentGateway.objects.filter(user=user).delete()

        # Delete products and related data directly associated with the user
        Product.objects.filter(id__in=product_ids).delete()

        # Delete categories and reviews associated with the user's products
        if product_ids:
            Category.objects.filter(product__id__in=product_ids).delete()
            Review.objects.filter(product__id__in=product_ids).delete()

        self.stdout.write(self.style.SUCCESS(f'Successfully deleted all orders and related data for user ID {user_id}.'))
