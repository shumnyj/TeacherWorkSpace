import json
import datetime
import pytz
import tzlocal

from django.urls import reverse
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseForbidden, HttpResponseBadRequest
from django.contrib.auth import views as auth_views
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.shortcuts import get_object_or_404, render, redirect
from django.forms import formset_factory
from django.forms.models import model_to_dict
from rest_framework import serializers

import workspace.models as wsm
import workspace.forms as wsf

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TZ_TARGET = tzlocal.get_localzone()  # datetime.datetime.now().astimezone().tzinfo     #EEST
TIME_FORMAT = "%T %z"
DATE_FORMAT = "%d.%m.%Y"
DT_FORMAT = DATE_FORMAT + " " + TIME_FORMAT
SCHEDULE_TIME = [datetime.time(8, 30, 0, 0, tzinfo=TZ_TARGET),
                 datetime.time(10, 25, 0, 0, tzinfo=TZ_TARGET),
                 datetime.time(12, 20, 0, 0, tzinfo=TZ_TARGET),
                 datetime.time(14, 15, 0, 0, tzinfo=TZ_TARGET),
                 datetime.time(16, 10, 0, 0, tzinfo=TZ_TARGET)]
COMMIT_TAG = "[WS]"
LAT_DELTA = 0.000210
LON_DELTA = 0.000370


def index_view(request):
    """
    Index view for app with placeholder content

    **Context**

    ``notifications``
    Notifications for current :model:`auth.User`.

    **Template:**

    :template:`workspace/index.html`
    """
    context = {}
    try:
        lesson_list = wsm.Lesson.objects.order_by('-datetime')[:10]
        context['lesson_list'] = lesson_list
    except wsm.Lesson.DoesNotExist:
        print("no lessons")
    if request.user.is_authenticated:
        context["notifications"] = request.user.notification_set.all().order_by("created")[:10]
    return render(request, "workspace/index.html", context)


def lesson_view(request, l_id):
    """
    View of particular lesson, also used to mark attendance by related teacher/students

    **Context**

    ``notifications``
    Notifications for current :model:`auth.User`.
    ``message``
    Notification message to render
    ``chosen_lesson``
    Current :model:`workspace.Lesson`
    ``auth_teacher``
    Current :model:`auth.User` if it is teacher
    ``auth_student``
    Current :model:`auth.User` if it is related student
    ``editable``
    Flag that shows if lesson can be modified
    ``at_form``
    Rendered form, forms.AttStartForm for viable teacher,
    forms.AttCheckForm for viable student if attendance started

    **Template:**

    :template:`workspace/lesson_detail.html`
    """
    chosen_lesson = get_object_or_404(wsm.Lesson, pk=l_id)
    context = {'chosen_lesson': chosen_lesson}
    if request.user.is_authenticated:
        if request.user.groups.filter(name="Teachers"):                                     # Teacher perspective
            if request.user == chosen_lesson.teacher.user:       # Correct teacher
                context['auth_teacher'] = request.user
                # if datetime.date.today() <= chosen_lesson.datetime.date():          # has not passed
                context['editable'] = True
                if not wsm.AttendanceToken.objects.filter(lesson=chosen_lesson):
                    # No token for this lesson (no repeat)
                    if request.method == 'POST':        # Form sent
                        at_form = wsf.AttStartForm(request.POST)
                        if at_form.is_valid():
                            at_token = wsm.AttendanceToken()
                            at_token.lesson = chosen_lesson
                            t = TZ_TARGET.localize(datetime.datetime.now())  # local current time
                            at_token.expire = t + datetime.timedelta(minutes=at_form.cleaned_data['minutes'])
                            # maybe change now() to form value or lesson start
                            at_token.save()                                       # New attendance token created
                            context['message'] = str("Timer started")
                            nn = wsm.Notification()
                            nn.note = "Lesson {} started ".format(chosen_lesson)
                            nn.link = reverse("workspace:lesson_detail", args=[chosen_lesson.id])
                            nn.expire = t + datetime.timedelta(hours=2, minutes=30)
                            # nn.created = t
                            nn.save()
                            # nn.user.set(auth.User.objects.filter(student__group = chosen_lesson.group)
                            for student in chosen_lesson.group.student_set.all():
                                nn.user.add(student.user)
                            nn.save()
                        else:
                            context['at_form'] = at_form
                            context['message'] = str("Error in form")
                    else:                   # Initial form view
                        context['at_form'] = wsf.AttStartForm()
                # else:
                    # remove atttoken
        elif request.user.groups.filter(name="Students"):                                   # Student perspective
            if request.user.student.group == chosen_lesson.group:           # Correct student
                context['auth_student'] = request.user    # maybe check for repeats
                at_tok = wsm.AttendanceToken.objects.filter(lesson=chosen_lesson)
                if at_tok.exists():                                        # If attendance available
                    at_tok = at_tok[0]
                    if TZ_TARGET.localize(datetime.datetime.now()) < at_tok.expire:  # In time
                        if request.method == 'POST':        # Form sent
                            at_form = wsf.AttCheckForm(request.POST)
                            if at_form.is_valid():          # Valid values
                                t_lat = at_form.cleaned_data['lat']
                                t_lon = at_form.cleaned_data['lon']
                                if -180 < t_lat < 180 and -90 < t_lon < 90:  # Valid values (add validator?)
                                    try:
                                        attendance, cr = wsm.Attendance.objects\
                                            .get_or_create(student=request.user.student, lesson=chosen_lesson)
                                        # defaults={'lon': t_lon, 'lat': t_lat}
                                        attendance.lat = t_lat
                                        attendance.lon = t_lon
                                        attendance.save()
                                        if chosen_lesson.location:
                                            if abs(t_lat - chosen_lesson.location.lat) < LAT_DELTA\
                                                    and abs(t_lon - chosen_lesson.location.lon) < LON_DELTA:
                                                # square accept zone
                                                # delta 0.000210 lat 0.000370 lon for ~ 50*50 m from center
                                                context['message'] = "Success"
                                            else:
                                                context['message'] = "Too far (Recorded)"
                                        else:
                                            context['message'] = "Recorded"
                                    except wsm.Attendance.MultipleObjectsReturned:         # Shouldn't show up
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
        context["notifications"] = request.user.notification_set.all().order_by("created")[:10]
    return render(request, "workspace/lesson_detail.html", context)


@login_required(login_url="workspace:login")
def lesson_edit_view(request, l_id):
    """
        View to edit particular lesson, only for respective teacher

        **Context**

        ``notifications``
        Notifications for current :model:`auth.User`.
        ``message``
        Notification message to render
        ``chosen_lesson``
        Current :model:`workspace.Lesson` to edit
        ``form``
        Rendered form, forms.LessonForm

        **Template:**

        :template:`workspace/lesson_detail.html`
        """
    chosen_lesson = get_object_or_404(wsm.Lesson, pk=l_id)
    context = {'chosen_lesson': chosen_lesson}
    if request.user.groups.filter(name="Teachers"):
        if request.user == chosen_lesson.teacher.user:          # Correct teacher
            # if datetime.date.today() <= chosen_lesson.datetime.date():    # Still editable
            if request.method == 'POST':
                form = wsf.LessonForm(request.POST)
                if form.is_valid():
                    chosen_lesson.location = form.cleaned_data['location']
                    chosen_lesson.datetime = datetime.datetime.combine(form.cleaned_data['date'],
                                                                       form.cleaned_data['time'])
                    chosen_lesson.type = form.cleaned_data['l_type']
                    chosen_lesson.modified = True
                    chosen_lesson.save()
                    return HttpResponseRedirect(reverse("workspace:lesson_detail", args=[chosen_lesson.id]))
                else:
                    context['message'] = "Invalid values, try again"
                    context['form'] = form
            else:
                form = wsf.LessonForm(initial={'location': chosen_lesson.location,'date': chosen_lesson.datetime.date(),
                                               'time': chosen_lesson.datetime.time(),'type': chosen_lesson.type})
                context['form'] = form
            context["notifications"] = request.user.notification_set.all().order_by("created")[:10]
            return render(request, "workspace/lesson_edit.html", context)
    return HttpResponseRedirect("/workspace/")  # Unrelated to course


@login_required(login_url="workspace:login")
def lesson_add_view(request):
    """
        View of particular lesson, also used to mark attendance by related teacher/students

        **Context**

        ``notifications``
        Notifications for current :model:`auth.User`.
        ``message``
        Notification message to render
        ``form``
        Rendered form, forms.LessonAddForm

        **Template:**

        :template:`workspace/lesson_detail.html`
        """
    if request.user.groups.filter(name="Teachers"):
        context = {"notifications": request.user.notification_set.all().order_by("created")[:10]}
        if request.method == 'POST':
            form = wsf.LessonAddForm(request.POST)
            if form.is_valid():
                new_lesson = wsm.Lesson()
                new_lesson.discipline = form.cleaned_data['discipline']
                new_lesson.group = form.cleaned_data['group']
                new_lesson.location = form.cleaned_data['location']
                new_lesson.datetime = datetime.datetime.combine(form.cleaned_data['date'],
                                                                   form.cleaned_data['time'])
                new_lesson.type = form.cleaned_data['l_type']
                new_lesson.modified = True
                new_lesson.teacher = request.user.teacher
                new_lesson.save()
                # nn = wsm.Notification(note="New lesson created")
                return HttpResponseRedirect(reverse("workspace:lesson_detail", args=[new_lesson.id]))
            else:
                context['message'] = "Invalid values, try again"
                context['form'] = form
        else:
            form = wsf.LessonAddForm()
            context['form'] = form
        return render(request, "workspace/lesson_add.html", context)
    return HttpResponseRedirect("/workspace/")  # 403 Not teacher


class MyLoginView(auth_views.LoginView):
    """
    Login view

    **Template:**

    :template:"workspace/login.html"
    """
    template_name = "workspace/login.html"
    redirect_field_name = "/"


def logout_view(request):
    """
    Logout pseudo view
    """
    logout(request)
    return HttpResponseRedirect("/workspace/")


"""
    def course_view(request, c_id):
    a_course = get_object_or_404(wsm.AcademicCourse, id=c_id)
    return HttpResponseRedirect("/workspace/") 
"""


@csrf_exempt
def webhook_github_view(request, c_id, s_id):
    """
    Pseudo view for processing payloads from github webhooks,
    other POST requests return HttpResponseBadRequest

    **Context**

    ``message``
    Returned message
    """
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
                            n.note = "Github repo of student {} was updated:\n {}".\
                                format(a_student, commit["message"])
                            n.link = commit["url"]
                            n.expire = TZ_TARGET.localize(datetime.datetime.now()) + datetime.timedelta(days=7)
                            n.save()
                            n.user.add()
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
        return HttpResponseRedirect("/workspace/")
        # return render(request, "workspace/webhook_test.html", {"message": "Get out, this is test"})


@login_required(login_url="workspace:login")
def profile_view(request):
    """
    View of profile of current user with basic information

    **Context**

    ``notifications``
    Notifications for current :model:`auth.User`.

    **Template:**

    :template:`workspace/profile.html`
    """
    return render(request, "workspace/profile.html",
                  {"notifications": request.user.notification_set.all().order_by("created")[:10]})


@login_required(login_url="workspace:login")
def marks_menu_view(request):
    """
    Menu view with list of courses current user is related to

    **Context**

    ``notifications``
    Notifications for current :model:`auth.User`.
    ``auth_teacher``
    True if user is teacher.
    ``auth_student``
    True if user is student.
    ``user_courses``
    Contains QuerySet of :model:`workspace.AcademicCourse` for current user
    ``extra_courses``
    List of extra :model:`workspace.AcademicCourse` with access
    by current teacher user via :model:`workspace.CourseAccess`

    **Template:**

    :template:`workspace/marks_menu.html`
    """
    context = dict()
    if request.user.groups.filter(name="Teachers"):
        context["user_courses"] = request.user.teacher.academiccourse_set.all()
        # wsm.AcademicCourse.objects.filter(teacher=request.user.teacher)
        context["auth_teacher"] = True
        extra_courses = []
        for a in request.user.teacher.courseaccess_set.all():
            extra_courses.append(a.course)
        if len(extra_courses) > 0:             # use len if you need data, .count only if number
            context["extra_courses"] = extra_courses
    elif request.user.groups.filter(name="Students"):
        context["user_courses"] = request.user.student.group.academiccourse_set.all()
        # wsm.AcademicCourse.objects.filter(group=request.user.student.group)
        context["auth_student"] = True
    context["notifications"] = request.user.notification_set.all().order_by("created")[:10]
    return render(request, "workspace/marks_menu.html", context)


def get_custom_context(request, view, **kwargs):        # example of integrated function
    """
     Function for creating dictionary of custom context variables
     for passing to basic view to be rendered in template
     :param request: request from view
     :param view: actual view that needs context
     :param kwargs: additional arguments
     :return: list of tuples (:model:`workspace.Student`, [float, None])
     """
    custom_context = dict()
    if view == marks_entities_view:
        if 'course' in kwargs:
            a_course = kwargs['course']
            if a_course.discipline.name == "Math":  # check if discipline that needs github webhook
                custom_context["auth_student"] = request.user.student
        return custom_context
    # reverse("workspace:github_wh", kwargs={"c_id": a_course.id, "s_id": request.user.student.id})


@login_required(login_url="workspace:login")
def marks_entities_view(request, c_id):                             # version with menu view for student
    """
        Menu view with list of control entities in course current user is related to

        **Context**

        ``notifications``
        Notifications for current :model:`auth.User`.
        ``auth_teacher``
        True if user is teacher.
        ``auth_student``
        Student object of current user.
        ``this_course``
        :model:`workspace.AcademicCourse` of this page.
        ``entities_list``
        Contains QuerySet of :model:`workspace.ControlEntity` for this :model:`workspace.AcademicCourse`

        **Template:**

        :template:`workspace/marks_entities.html`
    """
    a_course = get_object_or_404(wsm.AcademicCourse, id=c_id)
    # a_course = get_object_or_404(request.user.student.group.academiccourse_set.all(), id=c_id)
    context = {"this_course": a_course, "entities_list": a_course.controlentity_set.all(),
               "notifications": request.user.notification_set.all().order_by("created")[:10]}
    # c_entities = wsm.ControlEntity.objects.filter(course=a_course)
    # context["notifications"] = request.user.notification_set.all().order_by("created")[:10]
    if request.user.groups.filter(name="Teachers"):
        # related users only
        if request.user.teacher == a_course.teacher \
                or a_course.courseaccess_set.filter(teacher=request.user.teacher).exists():    # Additional access
            context["auth_teacher"] = True
            return render(request, "workspace/marks_entities.html", context)
            # alternatively for teacher - table view/list of entites - links to mark input form
    elif request.user.groups.filter(name="Students"):
        if a_course.group == request.user.student.group:    # related users only
            # alternatively for student - list of all entites+marks in this course
            context.update(get_custom_context(request, marks_entities_view, course=a_course))   # modular context
            return render(request, "workspace/marks_entities.html", context)
    return HttpResponseRedirect("/workspace/")              # Unrelated to course


@login_required(login_url="workspace:login")
def marks_table_view(request, c_id):
    a_course = get_object_or_404(wsm.AcademicCourse, id=c_id)
    context = {'this_course': a_course}
    course_marks = wsm.Mark.objects.filter(reason__course=a_course)
    student_list = a_course.group.student_set.all().order_by('user__last_name')
    ce_list = a_course.controlentity_set.all().order_by('date_created')
    context['ce_list'] = ce_list
    res = []
    for st in student_list:
        st_marks = course_marks.filter(student=st)
        ls = []
        total = 0
        for ce in ce_list:
            try:
                x = st_marks.get(reason=ce)
                total += x.mark
            except wsm.Mark.DoesNotExist:
                x = ''
            ls.append(x)
        res.append((st, ls, total))
    if request.user.groups.filter(name="Teachers"):
        if a_course.teacher == request.user.teacher \
                or a_course.courseaccess_set.filter(teacher=request.user.teacher).exists():
            context["marks_table"] = res
    elif request.user.groups.filter(name="Students"):
        if a_course.group == request.user.student.group:
            context["marks_table"] = res
    context["notifications"] = request.user.notification_set.all().order_by("created")[:10]
    return render(request, "workspace/marks_table.html", context)


@login_required(login_url="workspace:login")
def marks_add_entities_view(request, c_id):
    """
    View with form for teacher to add another :model:`workspace.ControlEntity`

    **Context**

    ``notifications``
    Notifications for current :model:`auth.User`.
    ``message``
    Notification message to render
    ``this_course``
    :model:`workspace.AcademicCourse` of this page
    ``form``
    forms.ControlEntityForm form instance

    **Template:**

    :template:`workspace/marks_add_ent.html`
    """
    a_course = get_object_or_404(wsm.AcademicCourse, id=c_id)
    context = {"this_course": a_course}
    if request.user.groups.filter(name="Teachers"):
        if request.user.teacher == a_course.teacher:
            if request.method == 'POST':
                form = wsf.ControlEntityForm(request.POST)          # initial={'course': a_course}
                print(form.errors.values)
                if form.is_valid():                                 # and 'course' not in form.changed_data:
                    fresh_ce = form.save(commit=False)
                    fresh_ce.course = a_course
                    try:
                        fresh_ce.save()
                        return HttpResponseRedirect(reverse("workspace:marks_entities", args=[a_course.id]))
                    except IntegrityError:
                        form.add_error(NON_FIELD_ERRORS, "Course, type and name fields are not unique together")
                        # context['message'] = "Course, type and name are not unique together"
                context['message'] = "Invalid values, try again"
                context['form'] = form
            else:
                form = wsf.ControlEntityForm()
                context['form'] = form
            context["notifications"] = request.user.notification_set.all().order_by("created")[:10]
            return render(request, "workspace/marks_add_ent.html", context)
    else:
        return HttpResponseRedirect("/workspace/")  # Unrelated to course


def marks_change_ent_view(request, c_id, e_id):
    a_course = get_object_or_404(wsm.AcademicCourse, id=c_id)
    a_entity = get_object_or_404(a_course.controlentity_set, id=e_id)
    context = {"this_entity": a_entity}
    if request.user.groups.filter(name="Teachers"):
        if a_course.teacher == request.user.teacher:  # Correct teacher
            if request.method == 'POST':
                form = wsf.ControlEntityChangeForm(request.POST)
                if form.is_valid():
                    a_entity.name = form.cleaned_data['name']
                    a_entity.deadline = form.cleaned_data['deadline']
                    a_entity.mark_max = form.cleaned_data['mark_max']
                    a_entity.materials = form.cleaned_data['materials']
                    print(form.Meta.error_messages)
                    try:
                        a_entity.save()
                        return HttpResponseRedirect(reverse("workspace:marks_detail",
                                                            kwargs={'c_id': a_course.id, 'e_id': a_entity.id}))
                    except IntegrityError:
                        context['message'] = "Course, type and name are not unique together for this"
                else:
                    context['message'] = "Invalid values, try again"
                context['form'] = form
            else:
                form = wsf.ControlEntityChangeForm(instance=a_entity)
                context['form'] = form
            context["notifications"] = request.user.notification_set.all().order_by("created")[:10]
            return render(request, "workspace/marks_entity_change.html", context)
    return HttpResponseRedirect("/workspace/")  # Unrelated to course


def marks_rm_ce_view(request, c_id, e_id):
    a_course = get_object_or_404(wsm.AcademicCourse, id=c_id)
    if request.user.groups.filter(name="Teachers"):
        if request.user.teacher == a_course.teacher:        # only main one can delete
            a_entity = get_object_or_404(a_course.controlentity_set, id=e_id)
            a_entity.delete()
            return HttpResponseRedirect(reverse("workspace:marks_entities", args=[a_course.id]))
    return HttpResponseForbidden("403 Get out", reason="forbidden")


def student_list_with_marks(a_entity):
    """
    Function for creating list (alphabetic ordering) of tuples
    (student, mark) with spaces if no mark available
    :param a_entity: required control entity :model:`workspace.ControlEntity`
    :return: list of tuples (:model:`workspace.Student`, [float, None])
    """
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
    """
    View with table of marks for current :model:`workspace.ControlEntity`
    in :model:`workspace.AcademicCourse`

    **Context**

    ``notifications``
    Notifications for current :model:`auth.User`.
    ``auth_teacher``
    True if user is teacher.
    ``this_entity``
    :model:`workspace.ControlEntity` of this page
    ``marks_list``
    List created by views.student_list_with_marks()

    **Template:**

    :template:`workspace/marks_entities.html`
    """
    a_course = get_object_or_404(wsm.AcademicCourse, id=c_id)
    a_entity = get_object_or_404(a_course.controlentity_set, id=e_id)
    context = {"this_entity": a_entity}
    if request.user.groups.filter(name="Teachers"):
        if a_course.teacher == request.user.teacher \
                or a_course.courseaccess_set.filter(teacher=request.user.teacher).exists():
            context["auth_teacher"] = True
            # context["marks_list"] = a_entity.mark_set.all()
            context["marks_list"] = student_list_with_marks(a_entity)
    elif request.user.groups.filter(name="Students"):
        if a_course.group == request.user.student.group:
            # context["marks_list"] = a_entity.mark_set.all()
            context["marks_list"] = student_list_with_marks(a_entity)
    context["notifications"] = request.user.notification_set.all().order_by("created")[:10]
    return render(request, "workspace/marks_detail.html", context)
    # else: return HttpResponseRedirect("/workspace/")


@login_required(login_url="workspace:login")
def marks_edit_view(request, c_id, e_id):
    """
    View with formset with every :model:`workspace.Student`
    of :model:`workspace.AcademicCourse` that contains current
    :model:`workspace.ControlEntity`, updates existing marks,
    adds new if mark don't exist for student

    **Context**

    ``notifications``
    Notifications for current :model:`auth.User`.
    ``message``
    Notification message to render
    ``this_entity``
    :model:`workspace.ControlEntity` of this page
    ``student_forms``
    Formset with forms.MarkForm instances for each student,
    unfilled forms are ignored

    **Template:**

    :template:`workspace/marks_edit.html`
    """
    a_course = get_object_or_404(wsm.AcademicCourse, id=c_id)
    a_entity = get_object_or_404(a_course.controlentity_set, id=e_id)
    context = {"this_entity": a_entity}
    if request.user.groups.filter(name="Teachers"):
        if a_course.teacher == request.user.teacher \
                or a_course.courseaccess_set.filter(teacher=request.user.teacher).exists():     # Valid teacher
            a_students = a_course.group.student_set.all().order_by("user__last_name")
            if len(a_students) > 0:
                if request.method == 'POST':
                    MarkFormSet = formset_factory(wsf.MarkForm, extra=len(a_students))
                    formset = MarkFormSet(request.POST, form_kwargs={"student_group": a_students})
                    # print(request.POST)             # debug
                    if formset.is_valid():                  # Valid forms
                        t = datetime.date.today()
                        for form in formset:
                            # print(form.cleaned_data)
                            if form.cleaned_data["mark"] is not None:           # if new mark is set
                                mrk, created = a_entity.mark_set.get_or_create(student=form.cleaned_data["student"],
                                                                               defaults={"reason": a_entity})
                                mrk.mark = form.cleaned_data["mark"]
                                mrk.date = t
                                mrk.save()
                        context["message"] = "Successfully saved"
                        return redirect('workspace:marks_detail', c_id=a_course.id, e_id=a_entity.id)
                    else:
                        context["message"] = "Error in form"
                        context["student_forms"] = formset
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
                context["message"] = "No students"          # TODO redirect here
            context["notifications"] = request.user.notification_set.all().order_by("created")[:10]
            return render(request, "workspace/marks_edit.html", context)
    return HttpResponseForbidden("403 Get out", reason="forbidden")


# @login_required(login_url="workspace:login")
# def marks_discipline_view(request):
#    render(request, "workspace/marks_discipline.html")


@login_required(login_url="workspace:login")
def schedule_view(request):
    """
    View with schedule with :model:`workspace.Lesson` for 2 weeks
     from this week's Monday, no whitespaces for "windows"

    **Context**

    ``notifications``
    Notifications for current :model:`auth.User`.
    ``weekday``
    Day of the week, int (0-6 : Mon-Sun)
    ``personal_lessons``
    Constructed list of QuerySets of :model:`workspace.Lesson` for each day of the interval

    **Template:**

    :template:`workspace/schedule.html`
    """
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
    context = {"personal_lessons": vlessons, "weekday": dt,
               "notifications": request.user.notification_set.all().order_by("created")[:10]}
    return render(request, "workspace/schedule.html", context)


def rm_notifcation(request, n_id):
    try:
        nn = wsm.Notification.objects.get(id=n_id)
        nn.user.remove(request.user)
        if nn.user.all().count() == 0:
            nn.delete()
        return HttpResponse('', status=204)
    except wsm.Notification.DoesNotExist:
        return HttpResponse('', status=404)



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
    """
    View for staff with form to add identical lessons in batch with forms.BatchLessonsForm

    **Context**

    ``notifications``
    Notifications for current :model:`auth.User`.
    ``message``
    Notification message to render
    ``form``
    Instance of forms.BatchLessonsForm

    **Template:**

    :template:`workspace/batch_add.html`
    """
    if request.user.is_staff:
        context = {"notifications": request.user.notification_set.all().order_by("created")[:10]}
        if request.method == 'POST':
            form = wsf.BatchLessonsForm(request.POST)
            if form.is_valid():
                if form.cleaned_data["week"]:
                    delta = datetime.timedelta(days=7)
                else:
                    delta = datetime.timedelta(days=14)
                les = wsm.Lesson()
                les.teacher = form.cleaned_data["teacher"]
                les.location = form.cleaned_data["location"]
                les.group = form.cleaned_data["group"]
                les.discipline = form.cleaned_data["discipline"]
                les.type = form.cleaned_data["l_type"]
                t = form.cleaned_data["start_date"]
                while t.weekday() != int(form.cleaned_data["day"]):     # "getting" from the start_date to set weekday
                    t += datetime.timedelta(days=1)
                while t < form.cleaned_data["end_date"]:
                    les.datetime = datetime.datetime.combine(t, form.cleaned_data["time"])
                    les.save()
                    les.pk = None
                    t += delta
                    context["message"] = "Success"
            else:
                context["form"] = form
                context["message"] = "Error during processing, try again"
        else:
            context["form"] = wsf.BatchLessonsForm()
        return render(request, "workspace/batch_add.html", context)
    else:
        return HttpResponseForbidden("403 Get out", reason="forbidden")


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
