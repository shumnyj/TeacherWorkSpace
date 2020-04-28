from django import forms
from django.core.exceptions import NON_FIELD_ERRORS

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


class BatchLessonsForm(forms.Form):
    """
        Form for creating multiple identical lessons for given period with given day and time
        Used in views.batch_add_lessons_view by staff
    """
    discipline = forms.ModelChoiceField(label='Discipline', queryset=wsm.Discipline.objects.all(), empty_label=None)
    group = forms.ModelChoiceField(label='Group', queryset=wsm.StudentGroup.objects.all(), empty_label=None)
    teacher = forms.ModelChoiceField(label='Teacher', queryset=wsm.Teacher.objects.all(), empty_label=None)
    location = forms.ModelChoiceField(label='Location', queryset=wsm.Location.objects.all(), empty_label=None)
    time = forms.TimeField(label='Lesson start time', widget=forms.TimeInput)
    day = forms.ChoiceField(label='Day of the week', choices=DAY_CHOICES)
    week = forms.BooleanField(label='Both weeks?',)
    start_date = forms.DateField(label='Start date (week)', widget=forms.SelectDateWidget())
    end_date = forms.DateField(label='Last date (week)', widget=forms.SelectDateWidget)


class MarkForm(forms.Form):
    """
        Form for creating/changing mark for student, used to create MarkFormSet
        in views.marks_edit_view, ControlEntity defined in view
    """
    student = forms.ModelChoiceField(label='Student', queryset=wsm.Student.objects.none(),
                                     empty_label=None,  disabled=True)
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
                self.fields["student"] = forms.ModelChoiceField(label='Student', queryset=qs, empty_label=None)


class ControlEntityForm(forms.ModelForm):
    """
        Form for teacher to add new control entity to his course
    """
    #course = forms.ModelChoiceField(queryset=wsm.AcademicCourse.objects, )
    # disabled=True don't really work for this widget=forms.Select(attrs={'disabled': True}) tpp

    class Meta:
        model = wsm.ControlEntity
        fields = ['course', 'etype', 'name', 'deadline', 'mark_max', 'materials']
        localized_fields = ('deadline',)
        error_messages = {
            NON_FIELD_ERRORS: {'unique_together': "%(model_name)s's %(field_labels)s are not unique.", }
        }
        widgets = {
            'deadline': forms.SelectDateWidget()
        }

# MarkFormSet = forms.formset_factory(MarkForm, extra=3)
