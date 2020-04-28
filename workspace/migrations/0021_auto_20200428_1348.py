# Generated by Django 2.2.5 on 2020-04-28 10:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workspace', '0020_auto_20200427_2053'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='link',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='student',
            name='card_id_number',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='studentgroup',
            name='specialization',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='studentgroup',
            name='curator',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='studentgroup',
            name='representative',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
    ]