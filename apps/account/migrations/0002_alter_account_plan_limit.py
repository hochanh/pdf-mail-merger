# Generated by Django 3.2 on 2021-05-16 05:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='plan_limit',
            field=models.PositiveIntegerField(default=50),
        ),
    ]
