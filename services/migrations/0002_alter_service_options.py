# Generated by Django 5.0 on 2025-07-19 09:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="service",
            options={"verbose_name": "Услуга", "verbose_name_plural": "Услуги"},
        ),
    ]
