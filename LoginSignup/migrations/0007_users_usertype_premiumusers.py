# Generated by Django 4.0.5 on 2022-08-09 09:41

import LoginSignup.models
import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('LoginSignup', '0006_alter_users_walletbalance'),
    ]

    operations = [
        migrations.AddField(
            model_name='users',
            name='userType',
            field=models.CharField(choices=[(LoginSignup.models.UserType['REGULAR'], 'regular'), (LoginSignup.models.UserType['PREMIUM'], 'premium')], default=LoginSignup.models.UserType['REGULAR'], max_length=20),
        ),
        migrations.CreateModel(
            name='PremiumUsers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('planName', models.CharField(choices=[(LoginSignup.models.PremiumPlans['ONE_MONTH_PLAN'], 'One Month Plan'), (LoginSignup.models.PremiumPlans['THREE_MONTH_PLAN'], 'Three Month Plan'), (LoginSignup.models.PremiumPlans['ONE_YEAR_PLAN'], 'One Year Plan')], max_length=20)),
                ('startDate', models.DateTimeField(default=datetime.datetime.now)),
                ('endDate', models.DateTimeField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='LoginSignup.users')),
            ],
        ),
    ]
