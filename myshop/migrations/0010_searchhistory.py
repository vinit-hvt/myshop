# Generated by Django 4.0.5 on 2022-07-26 06:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LoginSignup', '0006_alter_users_walletbalance'),
        ('myshop', '0009_products_isrecommended_products_recommendationamount'),
    ]

    operations = [
        migrations.CreateModel(
            name='SearchHistory',
            fields=[
                ('searchKeyword', models.CharField(max_length=200, primary_key=True, serialize=False)),
                ('frequency', models.IntegerField(default=1)),
                ('users', models.ManyToManyField(null=True, to='LoginSignup.users')),
            ],
        ),
    ]