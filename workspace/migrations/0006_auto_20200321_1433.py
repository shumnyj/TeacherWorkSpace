# Generated by Django 2.2.5 on 2020-03-21 12:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workspace', '0005_auto_20200321_1426'),
    ]

    operations = [
        migrations.AlterField(
            model_name='controlcategory',
            name='name',
            field=models.CharField(max_length=128, unique=True),
        ),
    ]