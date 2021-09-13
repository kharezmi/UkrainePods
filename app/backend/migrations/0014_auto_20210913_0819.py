# Generated by Django 3.2 on 2021-09-13 03:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0013_alter_botuser_bot_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='botuser',
            name='full_name',
            field=models.CharField(default='Nazarbek', max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='review',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='shop_review', to='backend.botuser'),
        ),
    ]
