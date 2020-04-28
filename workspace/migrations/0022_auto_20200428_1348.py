# Generated by Django 2.2.5 on 2020-04-28 10:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workspace', '0021_auto_20200428_1348'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentgroup',
            name='curator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='workspace.Teacher'),
        ),
        migrations.AlterField(
            model_name='studentgroup',
            name='representative',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='workspace.Student'),
        ),
    ]