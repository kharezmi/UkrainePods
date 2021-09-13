# Generated by Django 3.2 on 2021-09-13 02:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0010_auto_20210913_0714'),
    ]

    operations = [
        migrations.RenameField(
            model_name='category',
            old_name='name_ru',
            new_name='name',
        ),
        migrations.RemoveField(
            model_name='category',
            name='name_ua',
        ),
        migrations.AlterField(
            model_name='category',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='backend.category'),
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='backend.category'),
        ),
    ]