from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader
from django.contrib.auth import views as auth_views
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

import datetime

import workspace.models as wsm


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
        if request.user.groups.filter(name="Teachers"):
            context['auth_teacher'] = request.user
        elif request.user.groups.filter(name="Students"):
            context['auth_student'] = request.user
    #context = {'chosen_lesson': chosen_lesson, 'teacher': teacher}
    return render(request, "workspace/lesson_detail.html", context)
    #template = loader.get_template('workspace/lesson_detail.html')
    #context = {'chosen_lesson': chosen_lesson}
    #return HttpResponse(template.render(context, request))


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
def schedule_view(request):
    context = {}
    dt = datetime.date.today()
    min = dt - datetime.timedelta(days=dt.weekday())
    max = dt + datetime.timedelta(days=13-dt.weekday())
    dt = dt.weekday()
    viable = wsm.Lesson.objects.filter(datetime__gte=min).filter(datetime__lte=max)
    context["lesson"] = 1
    if request.user.groups.filter(name="Teachers"):
        vialble = viable.filter(teacher=request.user.teacher).order_by("datetime")
    elif request.user.groups.filter(name="Students"):
        vialble = viable.filter(group=request.user.student.group).order_by("datetime")
    else:
        return HttpResponseRedirect("/workspace/")
    return render(request, "workspace/schedule.html", {"personal_lessons": viable, "weekday": dt})


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
