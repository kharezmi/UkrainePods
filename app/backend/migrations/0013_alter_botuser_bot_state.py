# Generated by Django 3.2 on 2021-09-13 03:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0012_remove_purchase_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='botuser',
            name='bot_state',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
