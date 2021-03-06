# Generated by Django 2.2.5 on 2020-04-22 14:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workspace', '0010_auto_20200421_0158'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='controlentity',
            name='discipline',
        ),
        migrations.RemoveField(
            model_name='controlentity',
            name='teacher',
        ),
        migrations.RenameModel(
            old_name='SGroup',
            new_name='StudentGroup',
        ),
        migrations.CreateModel(
            name='AcademicCourse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('discipline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workspace.Discipline')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workspace.StudentGroup')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workspace.Teacher')),
            ],
        ),
        migrations.AddField(
            model_name='controlentity',
            name='course',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='workspace.AcademicCourse'),
            preserve_default=False,
        ),
    ]
