# Generated by Django 5.0.6 on 2024-05-21 09:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("orderdata", "0005_delete_refund"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Review",
        ),
    ]