from django.urls import path

from . import views

app_name = 'workspace'
urlpatterns = [
    path(r'', views.index_view, name='index'),
    path(r'login/', views.MyLoginView.as_view(), name='login'),
    path(r'logout/', views.logout_view, name='logout'),


    path(r'profile/', views.profile_view, name='profile'),
    path(r'schedule/', views.schedule_view, name='schedule'),
    path(r'lesson/<int:l_id>/', views.lesson_view, name='l_detail'),

    path(r'course/<int:c_id>/', views.course_view,  name='course_detail'),
    path(r'course/wh/github/<int:c_id>-<int:s_id>/', views.webhook_github_view, name='github_wh'),

    path(r'marks/', views.marks_menu_view, name="marks_menu"),
    path(r'marks/<int:c_id>/', views.marks_entities_view, name="marks_entities"),
    path(r'marks/<int:c_id>/add', views.marks_add_entities_view, name="marks_add_ent"),
    path(r'marks/<int:c_id>/<int:e_id>/', views.marks_detail_view, name="marks_detail"),
    path(r'marks/<int:c_id>/<int:e_id>/edit/', views.marks_edit_view, name="marks_edit"),


    path(r'batch_add/', views.batch_add_lessons_view, name='batch_add'),
]