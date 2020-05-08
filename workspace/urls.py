from django.urls import path

from . import views

app_name = 'workspace'
urlpatterns = [
    path(r'', views.index_view, name='index'),
    path(r'login/', views.MyLoginView.as_view(), name='login'),
    path(r'logout/', views.logout_view, name='logout'),
    path(r'profile/', views.profile_view, name='profile'),
    path(r'profile/edit', views.edit_profile_view, name='profile_edit'),

    path(r'schedule/', views.schedule_view, name='schedule'),
    path(r'lesson/<int:l_id>/', views.lesson_view, name='lesson_detail'),
    path(r'lesson/<int:l_id>/edit', views.lesson_edit_view, name='lesson_edit'),
    path(r'lesson/add', views.lesson_add_view, name='lesson_add'),

    path(r'marks/', views.marks_menu_view, name="marks_menu"),
    path(r'marks/course/<int:c_id>/', views.marks_entities_view, name="marks_entities"),
    path(r'marks/course/<int:c_id>/table', views.marks_table_view, name="marks_table"),
    path(r'marks/course/<int:c_id>/add', views.marks_add_entities_view, name="marks_add_ent"),
    path(r'marks/course/<int:c_id>/ce/<int:e_id>/', views.marks_detail_view, name="marks_detail"),
    path(r'marks/course/<int:c_id>/ce/<int:e_id>/change/', views.marks_change_ent_view, name="marks_entity_change"),
    path(r'marks/course/<int:c_id>/ce/<int:e_id>/edit/', views.marks_edit_view, name="marks_edit"),
    path(r'marks/course/<int:c_id>/ce/<int:e_id>/rm/', views.marks_rm_ce_view, name="marks_entity_rm"),

    path(r'batch_add/', views.batch_add_lessons_view, name='batch_add'),
    # path(r'course/<int:c_id>/', views.course_view,  name='course_detail'),
    path(r'course/wh/github/<int:c_id>-<int:s_id>/', views.webhook_github_view, name='github_wh'),
    path(r'notification/remove/<int:n_id>', views.rm_notification, name='rm_notif'),
]