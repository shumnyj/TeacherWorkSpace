from django import forms
import datetime
import workspace.models as wsm

DAY_CHOICES = [(0, "MON"), (1, "TUE"), (2, "WEN"), (3, "THU"), (4, "FRI"), (5, "SAT"), (6, "SUN")]


class TimeForm(forms.Form):
    submit_time = forms.DateTimeField(label='Submit time', initial=datetime.datetime.now())


class AttCheckForm(forms.Form):
    lon = forms.FloatField(widget=forms.HiddenInput)
    lat = forms.FloatField(widget=forms.HiddenInput)


class AttStartForm(forms.Form):
    minutes = forms.IntegerField(label='Minutes for attendance', initial=10)


class BatchLessonsForm(forms.Form):
    discipline = forms.ModelChoiceField(label='Discipline', queryset=wsm.Discipline.objects.all(), empty_label=None)
    group = forms.ModelChoiceField(label='Group', queryset=wsm.StudentGroup.objects.all(), empty_label=None)
    teacher = forms.ModelChoiceField(label='Teacher', queryset=wsm.Teacher.objects.all(), empty_label=None)
    location = forms.ModelChoiceField(label='Location', queryset=wsm.Location.objects.all(), empty_label=None)
    time = forms.TimeField(label='Lesson start time', widget=forms.TimeInput)
    day = forms.ChoiceField(label='Day of the week', choices=DAY_CHOICES)
    week = forms.BooleanField(label='Both weeks?',)
    start_date = forms.DateField(label='Start date (week)', widget=forms.SelectDateWidget())
    end_date = forms.DateField(label='Last date (week)', widget=forms.SelectDateWidget)
