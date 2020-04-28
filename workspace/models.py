from django.db import models
from django.conf import settings
from datetime import datetime


class StudentGroup(models.Model):
    """
        Stores a single student group
    """
    name = models.CharField(max_length=8)
    faculty = models.CharField(max_length=128, default="generic")
    specialization = models.PositiveIntegerField(default=0)
    course = models.PositiveSmallIntegerField(default=1)
    curator = models.ForeignKey("Teacher", null=True, blank=True, on_delete=models.SET_NULL)
    # curator = models.CharField(max_length=128, blank=True, null=True)
    representative = models.ForeignKey("Student", null=True, blank=True, on_delete=models.SET_NULL)
    # representative =  models.CharField(max_length=128, blank=True, null=True)   # староста?

    def __str__(self):
        return self.name
    # representative = models.ForeignKey('Student',null=True, on_delete=models.SET_NULL)  # SET(get randos student) ?


class Student(models.Model):
    """
        Extension for student of :model:`auth.User`, user have to be added to Students group
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='student', default=0)
    card_id_number = models.PositiveIntegerField(default=00000000)
    group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE)
    github = models.URLField(blank=True)

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name


class Teacher(models.Model):
    """
        Extension for teacher of :model:`auth.User`, user have to be added to Teachers group
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='teacher', default=0)
    qualification = models.CharField(max_length=256, blank=True)        # professor, etc
    page = models.URLField(blank=True)
    # contacts etc...

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name


class Discipline(models.Model):
    """
        Stores a single studying discipline
    """
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class AcademicCourse(models.Model):
    """
        Stores objects that represent one studying course with assigned
        :model:`workspace.Teacher` and :model:`workspace.Discipline`
        for a single :model:`workspace.StudentGroup`;
        related to :model:`workspace.ControlEntity`
    """
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['discipline', 'teacher', 'group'], name='unique_courses')]

    def __str__(self):
        return str(self.discipline) + ' ' + str(self.group)


class CourseAccess(models.Model):
    """
        Represents additional access for :model:`workspace.Teacher` other then
        recorded to particular :model:`workspace.AcademicCourse`
        For current needs should be more convenient than ManyToMany field
    """
    course = models.ForeignKey(AcademicCourse, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.course) + ' ' + str(self.teacher)


class Location(models.Model):
    """
        Stores a single location (lecture hall, lab, etc) with coordinates
    """
    room = models.CharField(max_length=8)
    building = models.CharField(max_length=50)
    lon = models.FloatField()
    lat = models.FloatField()

    def __str__(self):
        return self.room + '/' + self.building


class Lesson(models.Model):
    """
        Stores a single lesson instance, related to :model:`workspace.Teacher`,
        :model:`workspace.StudentGroup` and :model:`workspace.Discipline`
        Not connected with course for flexibility
    """
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)        # to_field=name ?
    group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE)           # to_field=name ?
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    datetime = models.DateTimeField()
    # type = models.ForeignKey(LessonType, blank=True, on_delete=None)          #lect/lab
    # materials = models.TextField(blank=True)                                  #links, books, etc
    modified = models.BooleanField(default=False)       # by teacher

    def __str__(self):
        return self.discipline.name + ' ' + str(self.datetime)


class Attendance(models.Model):
    """
        Stores a mark for attendance on the lesson, related to
        :model:`workspace.Student` and :model:`workspace.Lesson`
    """
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    lon = models.FloatField(blank=True)
    lat = models.FloatField(blank=True)

    def __str__(self):
        return self.lesson.discipline.name + ' ' + str(self.student)


class ControlCategory(models.Model):
    """
        Dictionary table for types of :model:`workspace.ControlEntity`
    """
    name = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name


class ControlEntity(models.Model):
    """
        Stores instances of control measures such as lab works, exams, control works, etc;
        related to :model:`workspace.AcademicCourse` and :model:`workspace.ControlCategory`
    """
    course = models.ForeignKey(AcademicCourse, on_delete=models.CASCADE,  default=0)
    etype = models.ForeignKey(ControlCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    date_created = models.DateField(auto_now_add=True)
    deadline = models.DateField(blank=True, null=True)
    mark_max = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    materials = models.TextField(blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['course', 'etype', 'name'], name='unique_control')]

    def __str__(self):
        return str(self.course.group) + ' ' + self.name + ' ' + str(self.deadline)


class Mark(models.Model):
    """
        Stores marks for :model:`workspace.Student` for
        certain :model:`workspace.ControlCategory`;
    """
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
    """
        Stores a token that used by students to mark :model:`workspace.Attendance`
        on certain :model:`workspace.Lesson`, created by related teacher, removed
        on the first usage by student after expiration
    """
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    expire = models.DateTimeField()

    def __str__(self):
        return str(self.expire)


class Notification(models.Model):
    """
        Stores notification for :model:`auth.User`
        User field is not many-to-many for personal dismiss
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    note = models.TextField()
    link = models.URLField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.user) + ' ' + str(self.created)
