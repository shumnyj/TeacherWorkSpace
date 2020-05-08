from django import forms
from django.core.exceptions import NON_FIELD_ERRORS
from django.contrib.auth.validators import UnicodeUsernameValidator
import datetime
import workspace.models as wsm

DAY_CHOICES = [(0, "MON"), (1, "TUE"), (2, "WEN"), (3, "THU"), (4, "FRI"), (5, "SAT"), (6, "SUN")]


class AttCheckForm(forms.Form):
    """
        Form for marking attendance by student
    """
    lon = forms.FloatField(widget=forms.HiddenInput)
    lat = forms.FloatField(widget=forms.HiddenInput)


class AttStartForm(forms.Form):
    """
        Form for creating attendance token by teacher
    """
    minutes = forms.IntegerField(label='Minutes for attendance', initial=10)


class MarkForm(forms.Form):
    """
        Form for creating/changing mark for student, used to create MarkFormSet
        in views.marks_edit_view, ControlEntity defined in view
    """
    student = forms.ModelChoiceField(label='Student', queryset=wsm.Student.objects.none(),
                                     empty_label=None, widget=forms.HiddenInput)
    mark = forms.DecimalField(label='Mark', max_digits=4, decimal_places=1, required=False)

    def __init__(self, *args, **kwargs):
        """
        __init__() if 'student_group' parameter passed overrides student
         field with another queryset, presumably - set of students in course group
        """
        try:
            qs = kwargs.pop('student_group')
        except KeyError:
            qs = None
        finally:
            super().__init__(*args, **kwargs)
            if qs:
                self.fields["student"] = forms.ModelChoiceField(label='Student', queryset=qs, empty_label=None,
                                                                widget=forms.HiddenInput)


class LessonForm(forms.Form):
    l_type = forms.ModelChoiceField(label='Type', queryset=wsm.LessonType.objects.all(), required=False)
    location = forms.ModelChoiceField(label='Location', queryset=wsm.Location.objects.all(), required=False)
    date = forms.DateField(label='Date', widget=forms.SelectDateWidget)
    time = forms.TimeField(label='Lesson start time', widget=forms.TimeInput)


class LessonAddForm(LessonForm):
    discipline = forms.ModelChoiceField(label='Discipline', queryset=wsm.Discipline.objects.all(), empty_label=None)
    group = forms.ModelChoiceField(label='Student group', queryset=wsm.StudentGroup.objects.all(), empty_label=None)


class BatchLessonsForm(LessonAddForm):
    """
        Form for creating multiple identical lessons for given period with given day and time
        Used in views.batch_add_lessons_view by staff
    """
    date = None
    teacher = forms.ModelChoiceField(label='Teacher', queryset=wsm.Teacher.objects.all(), empty_label=None)

    day = forms.ChoiceField(label='Day of the week', choices=DAY_CHOICES)
    week = forms.BooleanField(label='Each of 2 weeks?',)
    start_date = forms.DateField(label='Start date (week)', widget=forms.SelectDateWidget())
    end_date = forms.DateField(label='Last date (week)', widget=forms.SelectDateWidget)

    field_order = ['discipline', 'teacher', 'group', 'l_type', 'location',
                   'time', 'day', 'week', 'start_date', 'end_date']


class ControlEntityForm(forms.ModelForm):
    """
            Form for teacher to add new control entity to his course
    """
    class Meta:
        model = wsm.ControlEntity
        fields = ['name', 'etype', 'deadline', 'mark_max', 'materials']
        error_messages = {
            NON_FIELD_ERRORS: {'unique_together': "%(model_name)s's %(field_labels)s are not unique.", }
        }
        labels = {
            'etype': "Control type"
        }
        widgets = {
            # 'course': forms.HiddenInput(),
            'deadline': forms.SelectDateWidget()
        }


class ControlEntityChangeForm(ControlEntityForm):
    class Meta(ControlEntityForm.Meta):
        exclude = ['etype', ]


class ProfileBaseForm(forms.Form):
    username = forms.CharField(label='Username/Login', max_length=30,
                               required=False, validators=[UnicodeUsernameValidator])
    email = forms.EmailField(label="E-mail", required=False)


class ProfileStudentForm(ProfileBaseForm):
    github = forms.URLField(label="Github page", required=False)


class ProfileTeacherForm(ProfileBaseForm):
    page = forms.URLField(label="Personal page", required=False)


"""class ControlEntityForm(forms.Form):

    etype = forms.ModelChoiceField(label='Category', queryset=wsm.ControlCategory.objects.all(), empty_label=None)
    name = forms.CharField(label='Title')
    deadline = forms.DateField(label='Deadline', widget=forms.SelectDateWidget)
    mark_max = forms.DecimalField(label='Maximal mark', max_digits=4, decimal_places=1)
    materials = forms.CharField(label='Study materials', required=False)"""


