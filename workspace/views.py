import json
import datetime
import pytz
import tzlocal

from django.urls import path, reverse
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseForbidden, HttpResponseBadRequest
from django.contrib.auth import views as auth_views
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.forms import ModelChoiceField, formset_factory
from rest_framework import serializers

import workspace.models as wsm
import workspace.forms as wsf

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
tz_TARGET = datetime.datetime.now().astimezone().tzinfo     #EEST
TIME_FORMAT = "%T %z"
DATE_FORMAT = "%d.%m.%Y"
DT_FORMAT = DATE_FORMAT + " " + TIME_FORMAT
SCHEDULE_TIME = [datetime.time(8, 30, 0, 0, tzinfo=tz_TARGET),
                 datetime.time(10, 25, 0, 0, tzinfo=tz_TARGET),
                 datetime.time(12, 20, 0, 0, tzinfo=tz_TARGET),
                 datetime.time(14, 15, 0, 0, tzinfo=tz_TARGET),
                 datetime.time(16, 10, 0, 0, tzinfo=tz_TARGET)]
COMMIT_TAG = "[WS]"

def index_view(request):
    try:
        lesson_list = wsm.Lesson.objects.order_by('-datetime')[:10]
    except wsm.Lesson.DoesNotExist:
        raise Http404("Lesson does not exist")
    context = {'lesson_list': lesson_list}
    if request.user.is_authenticated:
        context["notifications"] = request.user.notification_set.all()
    return render(request, "workspace/index.html", context)


def lesson_view(request, l_id):
    chosen_lesson = get_object_or_404(wsm.Lesson, pk=l_id)
    context = {'chosen_lesson': chosen_lesson}
    if request.user.is_authenticated:
        if request.user.groups.filter(name="Teachers"):                                     # Teacher perspective
            context['auth_teacher'] = request.user
            if request.user == chosen_lesson.teacher.user:       # Correct teacher
                # TODO add restrictions to token start
                if not wsm.AttendanceToken.objects.filter(lesson=chosen_lesson):  # No token for this lesson (no repeat)
                    if request.method == 'POST':        # Form sent
                        at_form = wsf.AttStartForm(request.POST)
                        if at_form.is_valid():
                            at_token = wsm.AttendanceToken()
                            at_token.lesson = chosen_lesson
                            t = tzlocal.get_localzone().localize(datetime.datetime.now())  # tz_TARGET
                            print(datetime.datetime.now())
                            print(t)
                            print(t.astimezone(pytz.timezone('US/Eastern')))
                            at_token.expire = t + datetime.timedelta(minutes=at_form.cleaned_data['minutes'])
                            # maybe change now() to form value or lesson start
                            at_token.save()                                       # New attendance token created
                            context['message'] = str("Timer started")
                            for student in chosen_lesson.group.student_set.all():
                                nn = wsm.Notification()                 # ---------------------------------------
                                nn.user = student.user
                                nn.note = "<a href={}> Lesson {} started </a>"\
                                    .format(reverse("workspace:l_detail", args=[chosen_lesson.id]), chosen_lesson)
                                nn.created = t
                                nn.save()
                        else:
                            context['at_form'] = at_form
                            context['message'] = str("Error in form")
                    else:                               # Initial form view
                        context['at_form'] = wsf.AttStartForm()
                # else alternative form or none
        elif request.user.groups.filter(name="Students"):                                   # Student perspective
            if request.user.student.group == chosen_lesson.group:           # Correct student
                context['auth_student'] = request.user    # maybe check for repeats
                at_tok = wsm.AttendanceToken.objects.filter(lesson=chosen_lesson)
                if at_tok is not []:                                        # If attendance available
                    at_tok = at_tok[0]
                    if tzlocal.get_localzone().localize(datetime.datetime.now()) < at_tok.expire:  # In time
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
                                    except wsm.Attendance.MultipleObjectsReturned:             # Shouldn't show up, but...
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
        context["notifications"] = request.user.notification_set.all()
    return render(request, "workspace/lesson_detail.html", context)


class MyLoginView(auth_views.LoginView):
    template_name = "workspace/login.html"
    redirect_field_name = "/"


def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/workspace/")


def course_view(request, c_id):
    a_course = get_object_or_404(wsm.AcademicCourse, id=c_id)
    return HttpResponseRedirect("/workspace/")


@csrf_exempt
def webhook_github_view(request, c_id, s_id):       # probably need rest framework  here
    a_course = get_object_or_404(wsm.AcademicCourse, id=c_id)
    a_student = get_object_or_404(a_course.group.student_set.all(), id=s_id)
    if request.method == 'POST':
        context = {}
        data_dict = {}
        try:
            if request.META["HTTP_USER_AGENT"].startswith("GitHub-Hookshot"):
                data_dict = json.loads(request.body)
                try:
                    # TODO: Need to figure out reliable check
                    """retrieved_repo = data_dict["repository"]
                    if retrieved_repo["owner"]["email"]:            # == a_student.email / nickname / whatever
                        data_str = json.dumps(retrieved_repo, indent=4, separators=(',', ':'))"""
                    retrieved_commits = data_dict["commits"]
                    for commit in retrieved_commits:
                        # print(commit)
                        if COMMIT_TAG in commit["message"]:
                            data_str = json.dumps(data_dict, indent=4, separators=(',', ':'))
                            fl = open("test_wh.txt", "a")  # debug file
                            fl.write(data_str)  # debug
                            fl.close()  # debug
                            n = wsm.Notification()
                            n.user = a_course.teacher.user
                            n.note = "Github repo of student {} was updated: {}".\
                                format(a_student, commit["message"])
                            n.created = tzlocal.get_localzone().localize(datetime.datetime.now())
                            n.save()
                            return HttpResponse("Success")
                    context["message"] = "Ignored payload"
                    print("Ignored payload")
                    return HttpResponse("Ignored")
                except KeyError:
                    context["message"] = "Invalid payload"
                    print("Invalid payload")
                    return HttpResponseBadRequest("Invalid payload")
            else:
                context["message"] = "Invalid agent"
                print("Invalid agent")  # debug
                return HttpResponseBadRequest("Invalid agent")
        except KeyError:
            context["message"] = "No agent"
            print("No agent")
            return HttpResponseBadRequest("No agent")
    else:
        return render(request, "workspace/webhook_test.html", {"message": "Get out"})     # make redirect here


@login_required(login_url="workspace:login")
def profile_view(request):
    return render(request, "workspace/profile.html", {"notifications": request.user.notification_set.all()})


@login_required(login_url="workspace:login")
def marks_menu_view(request):
    context = dict()
    if request.user.groups.filter(name="Teachers"):
        user_courses = request.user.teacher.academiccourse_set.all()
        # wsm.AcademicCourse.objects.filter(teacher=request.user.teacher)
        context["auth_teacher"] = user_courses
        additional = []
        for a in request.user.teacher.courseaccess_set.all():
            additional.append(a.course)
        if len(additional) > 0:             # use len if you need data, .count only if number
            context["extra_courses"] = additional
    elif request.user.groups.filter(name="Students"):
        user_courses = request.user.student.group.academiccourse_set.all()
        # wsm.AcademicCourse.objects.filter(group=request.user.student.group)
        context["auth_student"] = user_courses
    context["notifications"] = request.user.notification_set.all()
    return render(request, "workspace/marks_menu.html", context)


@login_required(login_url="workspace:login")
def marks_entities_view(request, c_id):                             # version with menu view for student
    a_course = get_object_or_404(wsm.AcademicCourse, id=c_id)     # TODO try reverse _set here and in  marks_detail
    context = {"this_course": a_course, }
    c_entities = wsm.ControlEntity.objects.filter(course=a_course)
    context["notifications"] = request.user.notification_set.all()
    if request.user.groups.filter(name="Teachers"):
        # Strict limitation to marks data (related only)
        if request.user.teacher == a_course.teacher \
                or a_course.courseaccess_set.filter(teacher=request.user.teacher).exists():    # Additional access
            context["entities_list"] = c_entities           # simplified
            return render(request, "workspace/marks_entities.html", context)
            # alternatively for teacher - table view/list of entites - links to mark input form
    elif request.user.groups.filter(name="Students"):
        if a_course.group == request.user.student.group:    # Strict limitation to marks data (related only)
            # alternatively for student - list of all entites+marks in this course
            context["entities_list"] = c_entities
            return render(request, "workspace/marks_entities.html", context)
    return HttpResponseRedirect("/workspace/")              # Unrelated to course


def student_list_with_marks(a_entity):                # function for creating list of student + mark with spaces
    tmp_set = a_entity.mark_set.all()
    result_list = []
    for st in a_entity.course.group.student_set.all().order_by("user__last_name"):
        mark = tmp_set.filter(student=st)
        if mark.count() == 1:
            result_list.append((st, mark[0].mark))
        else:
            result_list.append((st, ''))
    return result_list


@login_required(login_url="workspace:login")
def marks_detail_view(request, c_id, e_id):
    a_course = get_object_or_404(wsm.AcademicCourse, id=c_id)
    a_entity = get_object_or_404(a_course.controlentity_set, id=e_id)
    context = {"this_entity": a_entity}
    if request.user.groups.filter(name="Teachers"):
        if a_course.teacher == request.user.teacher \
                or a_course.courseaccess_set.filter(teacher=request.user.teacher).exists():
            context["auth_teacher"] = 1
            # context["marks_list"] = a_entity.mark_set.all()
            context["marks_list"] = student_list_with_marks(a_entity)
    elif request.user.groups.filter(name="Students"):
        if a_course.group == request.user.student.group:
            # context["marks_list"] = a_entity.mark_set.all()
            context["marks_list"] = student_list_with_marks(a_entity)
    context["notifications"] = request.user.notification_set.all()
    return render(request, "workspace/marks_detail.html", context)
    # else: return HttpResponseRedirect("/workspace/")


@login_required(login_url="workspace:login")
def marks_edit_view(request, c_id, e_id):
    a_course = get_object_or_404(wsm.AcademicCourse, id=c_id)
    a_entity = get_object_or_404(a_course.controlentity_set, id=e_id)
    context = {"this_entity": a_entity}
    if request.user.groups.filter(name="Teachers"):
        if a_course.teacher == request.user.teacher \
                or a_course.courseaccess_set.filter(teacher=request.user.teacher).exists():     # Valid teacher
            a_students = a_course.group.student_set.all().order_by("user__last_name")
            if len(a_students) > 0:
                if request.method == 'POST':
                    # TODO disabled students field
                    MarkFormSet = formset_factory(wsf.MarkForm, extra=len(a_students))
                    formset = MarkFormSet(request.POST, form_kwargs={"student_group": a_students})
                    print(request.POST)
                    if formset.is_valid():                  # Valid forms
                        t = datetime.date.today()
                        for form in formset:
                            # print(form.cleaned_data)
                            if form.cleaned_data["mark"]:           # if new mark is set
                                mrk, created = a_entity.mark_set.get_or_create(student=form.cleaned_data["student"],
                                                                               defaults={"reason": a_entity})
                                mrk.mark = form.cleaned_data["mark"]
                                mrk.date = t
                                mrk.save()
                        context["message"] = "Successfully saved"
                        return redirect('workspace:marks_detail', c_id=a_course.id, e_id=a_entity.id)
                else:
                    # form = wsf.MarkForm(data={"student": a_students[0]}, student_group=a_students)
                    MarkFormSet = formset_factory(wsf.MarkForm, extra=len(a_students))
                    formset = MarkFormSet(form_kwargs={"student_group": a_students})
                    i = 0
                    for form in formset:
                        form.initial = {"student": a_students[i]}
                        i += 1
                    context["student_forms"] = formset
            else:
                context["message"] = "Not teacher"          # TODO redirect here
        # context["marks_list"] = a_entity.mark_set.all()
        # context["marks_list"] = student_list_with_marks(a_entity)
        context["notifications"] = request.user.notification_set.all()
        return render(request, "workspace/marks_edit.html", context)
    return HttpResponseForbidden("403 Get out", reason="forbidden")


# @login_required(login_url="workspace:login")
# def marks_discipline_view(request):
#    render(request, "workspace/marks_discipline.html")


@login_required(login_url="workspace:login")
def schedule_view(request):    # TODO should make days tabs, rework list
    dt = datetime.date.today()
    min = dt - datetime.timedelta(days=dt.weekday())
    max = dt + datetime.timedelta(days=13 - dt.weekday())
    dt = dt.weekday()
    viable = wsm.Lesson.objects.filter(datetime__date__gte=min).filter(datetime__date__lte=max)
    if request.user.groups.filter(name="Teachers"):
        viable = viable.filter(teacher=request.user.teacher)
    elif request.user.groups.filter(name="Students"):
        viable = viable.filter(group=request.user.student.group)
    else:
        return HttpResponseRedirect("/workspace/")
    vlessons = list()
    day = min
    while day <= max:
        vlessons.append((day, viable.filter(datetime__date=day).order_by("datetime__time")))
        day += datetime.timedelta(days=1)
    context = {"personal_lessons": vlessons, "weekday": dt, "notifications": request.user.notification_set.all()}
    return render(request, "workspace/schedule.html", context)

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
        context = {"notifications": request.user.notification_set.all()}
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
                    context["message"] = "Success"
            else:
                context["message"] = "Error during processing, try again"
        else:
            context["form"] = wsf.BatchLessonsForm()
        return render(request, "workspace/batch_add.html", context)
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
