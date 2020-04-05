from django.db import models
from django.conf import settings


class SGroup(models.Model):
    name = models.CharField(max_length=8)
    faculty = models.CharField(max_length=128, default="generic")
    course = models.PositiveSmallIntegerField(default=1)
    curator = models.CharField(max_length=128, blank=True)
    representative = models.CharField(max_length=128, blank=True)   # староста?

    def __str__(self):
        return self.name
    # representative = models.ForeignKey('Student',null=True, on_delete=models.SET_NULL)  # SET(get randos student) ?


class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='student', default=0)
    group = models.ForeignKey(SGroup, on_delete=models.CASCADE)
    # name = models.CharField(max_length=128)  # first/last name already kept from user
    # mail = models.EmailField()
    github = models.URLField(blank=True)

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name


class Teacher(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='teacher', default=0)
    # name = models.CharField(max_length=128)
    # mail = models.EmailField()
    page = models.URLField(blank=True)
    # contacts etc...

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name


class Discipline(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class Location(models.Model):
    room = models.CharField(max_length=8)
    building = models.CharField(max_length=50)
    lon = models.FloatField()
    lat = models.FloatField()

    def __str__(self):
        return self.room + '/' + self.building


class Lesson(models.Model):
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)  # to_field=name ?
    group = models.ForeignKey(SGroup, on_delete=models.CASCADE)           # to_field=name ?
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    datetime = models.DateTimeField()

    def __str__(self):
        return self.discipline.name + ' ' + str(self.datetime)


class Attendance(models.Model):
    lesson = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    lon = models.FloatField()
    lat = models.FloatField()

    def __str__(self):
        return self.lesson.discipline.name + ' ' + self.student.__str__()


class ControlCategory(models.Model):
    name = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name


class ControlEntity(models.Model):
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    etype = models.ForeignKey(ControlCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    date_created = models.DateField()
    deadline = models.DateField(blank=True)
    mark_max = models.PositiveSmallIntegerField(blank=True)

    def __str__(self):
        return self.name + ' ' + str(self.deadline)


class Mark(models.Model):
    reason = models.ForeignKey(ControlEntity, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    mark = models.PositiveSmallIntegerField(default=1)

    def __str__(self):
        return self.reason.name + ' ' + self.student.__str__()
