# Generated by Django 2.2.5 on 2020-04-22 15:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workspace', '0011_auto_20200422_1747'),
    ]

    operations = [
        migrations.AlterField(
            model_name='controlentity',
            name='course',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='workspace.AcademicCourse'),
        ),
    ]
