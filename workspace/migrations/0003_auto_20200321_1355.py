# Generated by Django 2.2.5 on 2020-03-21 11:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('workspace', '0002_auto_20200223_2300'),
    ]

    operations = [
        migrations.CreateModel(
            name='ControlCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='ControlEntity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('date_created', models.DateField()),
                ('deadline', models.DateField()),
                ('mark_max', models.PositiveSmallIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Discipline',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('room', models.CharField(max_length=8)),
                ('building', models.CharField(max_length=50)),
                ('lon', models.FloatField()),
                ('lat', models.FloatField()),
            ],
        ),
        migrations.RemoveField(
            model_name='student',
            name='mail',
        ),
        migrations.RemoveField(
            model_name='student',
            name='name',
        ),
        migrations.AddField(
            model_name='sgroup',
            name='faculty',
            field=models.CharField(default='generic', max_length=128),
        ),
        migrations.AddField(
            model_name='student',
            name='user',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='Teacher',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('page', models.URLField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Mark',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True)),
                ('mark', models.PositiveSmallIntegerField(default=1)),
                ('reason', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workspace.ControlEntity')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workspace.Student')),
            ],
        ),
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField()),
                ('discipline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workspace.Discipline')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workspace.SGroup')),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workspace.Location')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workspace.Teacher')),
            ],
        ),
        migrations.AddField(
            model_name='controlentity',
            name='discipline',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workspace.Discipline'),
        ),
        migrations.AddField(
            model_name='controlentity',
            name='etype',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workspace.ControlCategory'),
        ),
        migrations.AddField(
            model_name='controlentity',
            name='teacher',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workspace.Teacher'),
        ),
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lon', models.FloatField()),
                ('lat', models.FloatField()),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workspace.Discipline')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workspace.Student')),
            ],
        ),
    ]
