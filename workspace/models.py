from django.db import models
from django.conf import settings
from datetime import datetime



class StudentGroup(models.Model):
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
    group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE)
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


class AcademicCourse(models.Model):
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['discipline', 'teacher', 'group'], name='unique_courses')]

    def __str__(self):
        return str(self.discipline) + ' ' + str(self.group)


class CourseAccess(models.Model):
    course = models.ForeignKey(AcademicCourse, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.course) + ' ' + str(self.teacher)


class Location(models.Model):
    room = models.CharField(max_length=8)
    building = models.CharField(max_length=50)
    lon = models.FloatField()
    lat = models.FloatField()

    def __str__(self):
        return self.room + '/' + self.building


class Lesson(models.Model):
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)  # to_field=name ?
    group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE)           # to_field=name ?
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    datetime = models.DateTimeField()
    modified = models.BooleanField(default=False)

    def __str__(self):
        return self.discipline.name + ' ' + str(self.datetime)


class Attendance(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    lon = models.FloatField(blank=True)
    lat = models.FloatField(blank=True)

    def __str__(self):
        return self.lesson.discipline.name + ' ' + str(self.student)


class ControlCategory(models.Model):
    name = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name


class ControlEntity(models.Model):
    # discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    # teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    course = models.ForeignKey(AcademicCourse, on_delete=models.CASCADE,  default=0)
    etype = models.ForeignKey(ControlCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    date_created = models.DateField(auto_now_add=True)
    deadline = models.DateField(blank=True)
    mark_max = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    materials = models.TextField(blank=True)

    def __str__(self):
        return str(self.course.group) + ' ' + self.name + ' ' + str(self.deadline)


class Mark(models.Model):
    reason = models.ForeignKey(ControlEntity, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    mark = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    # last_change = models.DateField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['reason', 'student'], name='unique_marks')]
        # models.CheckConstraint(check=models.Q(student__group=models.F("reason__course__group")),
        #                                               name="group_student_check") ADD GROUP CONSTRAINT

    def __str__(self):
        return self.reason.name + ' ' + str(self.student)


class AttendanceToken(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    expire = models.DateTimeField()

    def __str__(self):
        return str(self.expire)


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # Not many-to-many for personal dismiss
    note = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.user) + ' ' + str(self.created)
