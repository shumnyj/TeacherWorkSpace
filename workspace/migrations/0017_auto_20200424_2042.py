# Generated by Django 2.2.5 on 2020-04-24 17:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workspace', '0016_auto_20200424_1557'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='modified',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='attendance',
            name='lat',
            field=models.FloatField(blank=True),
        ),
        migrations.AlterField(
            model_name='attendance',
            name='lon',
            field=models.FloatField(blank=True),
        ),
    ]
