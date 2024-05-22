import requests
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
from orderdata.models import (
    WooCommerceOrder, OrderItem, Customer, Category, Product, Address, PaymentGateway, ShippingMethod, Coupon, Tax
)
from authentication.models import WooCommerceCredentials, SyncRecord
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Sync data from WooCommerce'

    def handle(self, *args, **kwargs):
        user_id = 2  # Specify the user ID for whom you want to sync data
        credentials = WooCommerceCredentials.objects.filter(user_id=user_id).first()
        if not credentials:
            self.stdout.write(self.style.ERROR('No WooCommerce credentials found for the specified user.'))
            return

        # Fetch or create a sync record for the user
        sync_record, created = SyncRecord.objects.get_or_create(
            user_id=user_id, 
            defaults={'last_sync_time': make_aware(datetime(1970, 1, 1))}
        )
        self.stdout.write(f"Last sync time: {sync_record.last_sync_time}")

        # Convert last_sync_time to ISO 8601 format
        last_sync_time = sync_record.last_sync_time.strftime('%Y-%m-%dT%H:%M:%S')

        # Step 1: Test API connection
        if not self.test_api_connection(credentials):
            return

        # Step 2: Sync orders
        new_sync_time = make_aware(datetime.utcnow())
        self.sync_orders(credentials, last_sync_time)

        # Step 3: Update sync record with the new sync time
        sync_record.last_sync_time = new_sync_time
        sync_record.save()

        self.stdout.write(self.style.SUCCESS('Sync completed successfully.'))

    def test_api_connection(self, credentials):
        self.stdout.write(self.style.NOTICE('Testing API connection...'))
        response = self.get_wc_data(credentials, 'products', {'per_page': 1})
        if response:
            self.stdout.write(self.style.SUCCESS('API connection successful.'))
            return True
        else:
            self.stdout.write(self.style.ERROR('API connection failed. Please check the WooCommerce credentials and try again.'))
            return False

    def get_wc_data(self, credentials, endpoint, params=None):
        if params is None:
            params = {}
        url = f"{credentials.store_url}/wp-json/wc/v3/{endpoint}"
        auth = (credentials.consumer_key, credentials.consumer_secret)
        self.stdout.write(self.style.NOTICE(f"Fetching {endpoint} from {url}..."))
        try:
            response = requests.get(url, auth=auth, params=params, timeout=10)
            self.stdout.write(self.style.NOTICE(f"Response status code: {response.status_code}"))
            if response.status_code == 200:
                self.stdout.write(self.style.NOTICE(f"Fetched {len(response.json())} items from {endpoint}."))
                return response.json()
            else:
                self.stdout.write(self.style.ERROR(f"Failed to fetch {endpoint}: {response.status_code}"))
                self.stdout.write(self.style.ERROR(f"Response: {response.text}"))
                return []
        except requests.exceptions.Timeout:
            self.stdout.write(self.style.ERROR(f"Request to {endpoint} timed out."))
            return []
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
            return []

    def sync_orders(self, credentials, last_sync_time):
        self.stdout.write(self.style.NOTICE('Syncing orders...'))
        all_orders = []
        for page in range(1, 11):  # Iterate over 10 pages
            params = {'per_page': 100, 'page': page, 'modified_after': last_sync_time}
            orders = self.get_wc_data(credentials, 'orders', params)
            if not orders:
                self.stdout.write(self.style.NOTICE(f'No more orders found after {len(all_orders)} orders.'))
                break
            all_orders.extend(orders)
            self.stdout.write(self.style.NOTICE(f"Fetched {len(orders)} orders from page {page}."))

        if not all_orders:
            self.stdout.write(self.style.ERROR('No orders found or failed to fetch orders.'))
            return

        self.stdout.write(self.style.NOTICE(f'Total orders fetched: {len(all_orders)}'))

        for idx, order_data in enumerate(all_orders, start=1):
            customer = self.import_customer(credentials.user, order_data['billing'], order_data['total'])
            payment_gateway = self.import_payment_gateway(credentials.user, order_data['payment_method'])
            date_created = parse_datetime(order_data['date_created'])
            date_modified = parse_datetime(order_data['date_modified'])

            if date_created and not date_created.tzinfo:
                date_created = make_aware(date_created)
            if date_modified and not date_modified.tzinfo:
                date_modified = make_aware(date_modified)

            order, created = WooCommerceOrder.objects.update_or_create(
                user=credentials.user,
                order_id=order_data['id'],
                defaults={
                    'status': order_data['status'],
                    'total': order_data['total'],
                    'date_created': date_created,
                    'date_modified': date_modified,
                    'customer': customer,
                    'refund_amount': sum(refund.get('amount', 0) for refund in order_data.get('refunds', [])),
                    'payment_gateway': payment_gateway
                }
            )
            self.stdout.write(self.style.NOTICE(f"Imported order {idx} of {len(all_orders)}: Order ID {order_data['id']}"))

            # Clear existing related objects to ensure they are overwritten
            OrderItem.objects.filter(order=order).delete()
            Address.objects.filter(order=order).delete()
            ShippingMethod.objects.filter(order=order).delete()
            Coupon.objects.filter(order=order).delete()
            Tax.objects.filter(order=order).delete()

            self.import_order_items(order, order_data['line_items'])
            self.import_addresses(order, order_data['billing'], 'billing')
            self.import_addresses(order, order_data['shipping'], 'shipping')
            self.import_shipping_methods(order, order_data['shipping_lines'])
            self.import_coupons(order, order_data['coupon_lines'])
            self.import_taxes(order, order_data['tax_lines'])

    def import_customer(self, user, billing_data, order_total):
        email = billing_data.get('email')
        if not email:
            self.stdout.write(self.style.WARNING('Missing email in billing data. Skipping customer import.'))
            return None

        customer, created = Customer.objects.get_or_create(
            user=user,
            email=email,
            defaults={
                'first_name': billing_data.get('first_name', ''),
                'last_name': billing_data.get('last_name', ''),
                'total_spent': Decimal(order_total),  # Initial order total
                'orders_count': 1  # Initial order count
            }
        )
        if not created:
            # If the customer already exists, update their information and increment their stats
            customer.first_name = billing_data.get('first_name', customer.first_name)
            customer.last_name = billing_data.get('last_name', customer.last_name)
            customer.total_spent += Decimal(order_total)  # Add the order total to total spent
            customer.orders_count += 1  # Increment the order count
            customer.save()

        return customer

    def import_payment_gateway(self, user, gateway_id):
        gateway, created = PaymentGateway.objects.update_or_create(
            user=user,
            gateway_id=gateway_id,
            defaults={
                'name': gateway_id,  # Placeholder, as name might not be available directly in order data
                'cost_percentage': 0,  # Placeholder, needs to be updated with actual data
                'cost_fixed': 0,  # Placeholder, needs to be updated with actual data
                'total_cost': 0  # Placeholder, needs to be updated with actual data
            }
        )
        # Update order count
        gateway.total_cost += 1
        gateway.save()
        return gateway

    def import_order_items(self, order, items):
        for item_data in items:
            product_id = item_data['product_id']
            self.stdout.write(self.style.NOTICE(f"Processing product ID: {product_id}"))  # Debug statement
            product = Product.objects.filter(product_id=product_id).first()  # Placeholder for now
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item_data['quantity'],
                total=item_data['total']
            )

    def import_addresses(self, order, address_data, address_type):
        customer = order.customer
        Address.objects.create(
            order=order,
            customer=customer,
            address_type=address_type,
            address=address_data
        )

    def import_shipping_methods(self, order, shipping_methods):
        for shipping_data in shipping_methods:
            ShippingMethod.objects.create(
                order=order,
                method_id=shipping_data['method_id'],
                method_title=shipping_data['method_title'],
                total=shipping_data['total']
            )

    def import_coupons(self, order, coupons):
        for coupon_data in coupons:
            Coupon.objects.create(
                order=order,
                code=coupon_data['code'],
                discount=coupon_data['discount']
            )

    def import_taxes(self, order, taxes):
        for tax_data in taxes:
            Tax.objects.create(
                order=order,
                total=tax_data.get('total', 0),  # Use .get() to handle missing 'total'
                tax_rate=tax_data.get('rate', 0),  # Use .get() to handle missing 'rate'
                tax_region=tax_data.get('label', '')  # Use .get() to handle missing 'label'
            )
