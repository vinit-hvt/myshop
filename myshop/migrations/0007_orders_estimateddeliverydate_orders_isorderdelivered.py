# Generated by Django 4.0.5 on 2022-07-18 11:17

from django.db import migrations, models
import myshop.models


class Migration(migrations.Migration):

    dependencies = [
        ('myshop', '0006_orders_deliveryaddress'),
    ]

    operations = [
        migrations.AddField(
            model_name='orders',
            name='estimatedDeliveryDate',
            field=models.DateTimeField(default=myshop.models.getDeliveryDate),
        ),
        migrations.AddField(
            model_name='orders',
            name='isOrderDelivered',
            field=models.BooleanField(default=False),
        ),
    ]
