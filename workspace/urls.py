from django.urls import path

from . import views

app_name = 'workspace'
urlpatterns = [
    path('', views.index_view, name='index'),
    path('login/', views.MyLoginView.as_view(), name='login'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/logout', views.logout_view, name='logout'),
    path('schedule/', views.schedule_view, name='schedule'),
    path('lesson/<int:l_id>/', views.lesson_view, name='l_detail'),
]