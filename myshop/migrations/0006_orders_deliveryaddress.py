# Generated by Django 4.0.5 on 2022-07-18 07:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('LoginSignup', '0006_alter_users_walletbalance'),
        ('myshop', '0005_alter_orders_totalbillamount'),
    ]

    operations = [
        migrations.AddField(
            model_name='orders',
            name='deliveryAddress',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='LoginSignup.address'),
        ),
    ]
