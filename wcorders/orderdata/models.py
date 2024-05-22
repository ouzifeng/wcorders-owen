from django.db import models
from django.contrib.auth.models import User

class Customer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customers')
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    orders_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.email} - {self.first_name} {self.last_name}"

class Category(models.Model):
    category_id = models.BigIntegerField(unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Product(models.Model):
    product_id = models.BigIntegerField(unique=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class WooCommerceOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_id = models.BigIntegerField(unique=True)
    status = models.CharField(max_length=50)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    date_created = models.DateTimeField()
    date_modified = models.DateTimeField()
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_gateway = models.ForeignKey('PaymentGateway', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Order {self.order_id}"

class OrderItem(models.Model):
    order = models.ForeignKey(WooCommerceOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField()
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Item {self.product.name} in Order {self.order.order_id}"

class Address(models.Model):
    order = models.ForeignKey(WooCommerceOrder, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    address_type = models.CharField(max_length=10)  # 'billing' or 'shipping'
    address = models.JSONField()

    def __str__(self):
        return f"{self.address_type.capitalize()} Address for Order {self.order.order_id}"


class PaymentGateway(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    gateway_id = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    cost_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    cost_fixed = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class ShippingMethod(models.Model):
    order = models.ForeignKey(WooCommerceOrder, on_delete=models.CASCADE)
    method_id = models.CharField(max_length=50)
    method_title = models.CharField(max_length=255)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.method_title

class Coupon(models.Model):
    order = models.ForeignKey(WooCommerceOrder, on_delete=models.CASCADE)
    code = models.CharField(max_length=50)
    discount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.code

class Tax(models.Model):
    order = models.ForeignKey(WooCommerceOrder, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    tax_region = models.CharField(max_length=255)

    def __str__(self):
        return f"Tax {self.total} for Order {self.order.order_id}"
