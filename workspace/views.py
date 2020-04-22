from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader
from django.contrib.auth import views as auth_views
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import  MultipleObjectsReturned

import datetime


import workspace.models as wsm
import workspace.forms as wsf

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SCHEDULE_TIME = []
tz_EEST = datetime.datetime.now().astimezone().tzinfo


def index_view(request):
    try:
        lesson_list = wsm.Lesson.objects.order_by('-datetime')[:10]
    except wsm.Lesson.DoesNotExist:
        raise Http404("Lesson does not exist")
    context = {'lesson_list': lesson_list}
    return render(request, "workspace/index.html", context)


def lesson_view(request, l_id):
    try:
        chosen_lesson = wsm.Lesson.objects.get(pk=l_id)
    except wsm.Lesson.DoesNotExist:
        raise Http404("Lesson does not exist")
    context = {'chosen_lesson': chosen_lesson}
    if request.user.is_authenticated:
        if request.user.groups.filter(name="Teachers"):                                     # Teacher perspective
            context['auth_teacher'] = request.user
            if not wsm.AttendanceToken.objects.filter(lesson=chosen_lesson):    # No token for this lesson (no repeat)
                if request.method == 'POST':        # Form sent
                    at_form = wsf.AttStartForm(request.POST)
                    if at_form.is_valid():
                        at_token = wsm.AttendanceToken()
                        at_token.lesson = chosen_lesson
                        at_token.expire = datetime.datetime.now() + datetime.timedelta(minutes=at_form.cleaned_data['minutes'])
                        # maybe change now() to form value or lesson start
                        at_token.save()                         # New attendance token created
                        context['message'] = str("Timer started")
                    else:
                        context['at_form'] = at_form
                        context['message'] = str("Invalid form")
                else:                               # Initial form view
                    context['at_form'] = wsf.AttStartForm()
            # else alternative form or none
        elif request.user.groups.filter(name="Students"):                                   # Student perspective
            if request.user.student.group == chosen_lesson.group:           # Correct student
                context['auth_student'] = request.user    # maybe check for repeats
                at_tok = wsm.AttendanceToken.objects.filter(lesson=chosen_lesson)
                if at_tok is not []:                                        # If attendance available
                    at_tok = at_tok[0]
                    if datetime.datetime.now(tz=tz_EEST) < at_tok.expire:  # In time
                        if request.method == 'POST':        # Form sent
                            at_form = wsf.AttCheckForm(request.POST)
                            if at_form.is_valid():                              # Valid values
                                t_lon = at_form.cleaned_data['lon']
                                t_lat = at_form.cleaned_data['lat']
                                if -180 < t_lat < 180 and -90 < t_lon < 90:  # Valid values (maybe override is_valid()?)
                                    try:
                                        attendance, cr = wsm.Attendance.objects\
                                            .get_or_create(student=request.user.student, lesson=chosen_lesson,
                                                           defaults={'lon': t_lon, 'lat': t_lat})
                                        # attendance.save()
                                        context['message'] = "Success"
                                    except MultipleObjectsReturned:             # Shouldn't show up, but...
                                        context['message'] = "Multiple objects error, contact admin"
                                else:
                                    context['message'] = "invalid values, try again"
                                    context['at_form'] = at_form
                            else:
                                context['message'] = "invalid values here"
                                context['at_form'] = at_form
                        else:                               # Initial form view
                            context['at_form'] = wsf.AttCheckForm()
                    else:                                                   # Too late
                        at_tok.delete()
                        context['message'] = "Attendance expired, token removed"
    return render(request, "workspace/lesson_detail.html", context)


class MyLoginView(auth_views.LoginView):
    template_name = "workspace/login.html"
    redirect_field_name = "/"


def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/workspace/")


@login_required(login_url="workspace:login")
def profile_view(request):
    return render(request, "workspace/profile.html")


@login_required(login_url="workspace:login")
def marks_menu_view(request):
    context = dict()
    if request.user.groups.filter(name="Teachers"):
        user_courses = request.user.teacher.academiccourse_set.all()
        # wsm.AcademicCourse.objects.filter(teacher=request.user.teacher)
        context["auth_teacher"] = user_courses
    elif request.user.groups.filter(name="Students"):
        user_courses = request.user.student.group.academiccourse_set.all()
        # wsm.AcademicCourse.objects.filter(group=request.user.student.group)
        context["auth_student"] = user_courses
    return render(request, "workspace/marks_menu.html", context)


@login_required(login_url="workspace:login")
def marks_entities_view(request, c_id):                             # version with menu view for student
    try:
        a_course = wsm.AcademicCourse.objects.get(id=c_id)          # TODO try reverse _set here and in  marks_detail
    except wsm.AcademicCourse.DoesNotExist:
        raise Http404("Course does not exist")
    context = {"this_course": a_course, }
    c_entities = wsm.ControlEntity.objects.filter(course=a_course)
    if request.user.groups.filter(name="Teachers"):
        if a_course.teacher == request.user.teacher:        # Strict limitation to marks data (related only)
            context["entities_list"] = c_entities           # simplified
            # alternatively for teacher - table view/list of entites - links to mark input form
    elif request.user.groups.filter(name="Students"):
        if a_course.group == request.user.student.group:    # Strict limitation to marks data (related only)
            # alternatively for student - list of all entites+marks in this course
            context["entities_list"] = c_entities
    return render(request, "workspace/marks_entities.html", context)
    # else: return HttpResponseRedirect("/workspace/")


def student_list_with_marks(a_entity):                # function for creating list of student + mark with spaces
    tmp_set = a_entity.mark_set.all()
    result_list = []
    for st in a_entity.course.group.student_set.all().order_by("user__last_name"):
        mark = tmp_set.filter(student=st)
        if len(mark) == 1:
            result_list.append((st, mark[0].mark))
        else:
            result_list.append((st, ''))
    return result_list


@login_required(login_url="workspace:login")
def marks_detail_view(request, c_id, e_id):
    try:
        a_course = wsm.AcademicCourse.objects.get(id=c_id)
    except wsm.AcademicCourse.DoesNotExist:
        raise Http404("Course does not exist")
    try:
        a_entity = a_course.controlentity_set.get(id=e_id)
    except wsm.ControlEntity.DoesNotExist:
        raise Http404("No such control event in this course")
    context = {"this_entity": a_entity}
    if request.user.groups.filter(name="Teachers"):
        if a_course.teacher == request.user.teacher:
            context["auth_teacher"] = 1
            # context["marks_list"] = a_entity.mark_set.all()
            context["marks_list"] = student_list_with_marks(a_entity)
    elif request.user.groups.filter(name="Students"):
        if a_course.group == request.user.student.group:
            # context["marks_list"] = a_entity.mark_set.all()
            context["marks_list"] = student_list_with_marks(a_entity)
    return render(request, "workspace/marks_detail.html", context)
    # else: return HttpResponseRedirect("/workspace/")


@login_required(login_url="workspace:login")
def marks_discipline_view(request):
    render(request, "workspace/marks_discipline.html")


@login_required(login_url="workspace:login")
def schedule_view(request):                             # TODO should make days tabs
    if request.user.groups.filter(name="Teachers"):
        viable = wsm.Lesson.objects.filter(teacher=request.user.teacher)
    elif request.user.groups.filter(name="Students"):
        viable = wsm.Lesson.objects.filter(group=request.user.student.group)
    else:
        return HttpResponseRedirect("/workspace/")
    dt = datetime.date.today()
    min = dt - datetime.timedelta(days=dt.weekday())
    max = dt + datetime.timedelta(days=13 - dt.weekday())
    dt = dt.weekday()
    vlessons = list()
    day = min
    while day <= max:
        vlessons.append((day, viable.filter(datetime__date=day).order_by("datetime__time")))
        day += datetime.timedelta(days=1)
    return render(request, "workspace/schedule.html", {"personal_lessons": vlessons, "weekday": dt})
"""
dt = datetime.date.today()
min = dt - datetime.timedelta(days=dt.weekday())
max = dt + datetime.timedelta(days=13-dt.weekday())
dt = dt.weekday()
viable = wsm.Lesson.objects.filter(datetime__gte=min).filter(datetime__lte=max)
if request.user.groups.filter(name="Teachers"):
    vialble = viable.filter(teacher=request.user.teacher).order_by("datetime")
elif request.user.groups.filter(name="Students"):
    vialble = viable.filter(group=request.user.student.group).order_by("datetime")
else:
    return HttpResponseRedirect("/workspace/")
return render(request, "workspace/schedule.html", {"personal_lessons": viable, "weekday": dt})"""


@login_required(login_url="workspace:login")
def batch_add_lessons_view(request):        # maybe split weeks
    if request.user.is_staff:
        if request.method == 'POST':
            form = wsf.BatchLessonsForm(request.POST)
            if form.is_valid():
                if form.cleaned_data["week"]:
                    delta = datetime.timedelta(days=7)
                else:
                    delta = datetime.timedelta(days=14)
                l = wsm.Lesson()
                l.teacher = form.cleaned_data["teacher"]
                l.location = form.cleaned_data["location"]
                l.group = form.cleaned_data["group"]
                l.discipline = form.cleaned_data["discipline"]
                t = form.cleaned_data["start_date"]
                while t.weekday() != int(form.cleaned_data["day"]):
                    t += datetime.timedelta(days=1)
                while t < form.cleaned_data["end_date"]:
                    l.datetime = datetime.datetime.combine(t, form.cleaned_data["time"])
                    l.save()
                    l.pk = None
                    t += delta
                return render(request, "workspace/batch_add.html", {"message": "Success"})
            else:
                return render(request, "workspace/batch_add.html", {"message": "Err"})
        else:
            form = wsf.BatchLessonsForm()
            return render(request, "workspace/batch_add.html", {"form": form})
    else:
        return HttpResponseRedirect("workspace:index")  # TODO forbidden



"""
def login_view(request):
    username = ""
    password = ""
    pnext = ""

    if request.GET:
        pnext = request.GET['next']
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']

    user = authenticate(request, username=username, password=password)
    if user is not None:
        if user.is_active:
            login(request, user)
            if pnext == "":
                return HttpResponseRedirect('/workspace/')
            else:
                return HttpResponseRedirect(next)
    return render(request, "workspace/login.html")
"""
