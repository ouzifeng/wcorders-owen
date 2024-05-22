from django.db import models
from django.contrib.auth.models import User

class WooCommerceCredentials(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='woocommerce_credentials')
    store_url = models.URLField()
    consumer_key = models.CharField(max_length=255)
    consumer_secret = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user.username}'s WooCommerce Credentials"


class SyncRecord(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_sync_time = models.DateTimeField()

    def __str__(self):
        return f"{self.user.username} - Last Sync: {self.last_sync_time}"