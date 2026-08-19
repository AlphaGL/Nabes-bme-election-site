from django.urls import path
from . import views
from .views import BmeLoginView, vote_position, next_position, admin_dashboard, register_student, CompletedView
from .views import reset_password

urlpatterns = [
    path('', BmeLoginView.as_view(), name='login'),
    path('register/', register_student, name='register_student'),
    path('vote/<int:position_id>/', vote_position, name='vote_position'),
    path('next_position/<int:position_id>/', next_position, name='next_position'),
    path('admin_dashboard/', admin_dashboard, name='admin_dashboard'),
    path('completed/', CompletedView.as_view(), name='completed'),
    path('reset/', views.reset_all, name='reset_all'),
    path('live_vote_count/', views.live_vote_count, name='live_vote_count'),
    path('Security-Check/', views.enter_access_code, name='enter_access_code'),
    path('students/', views.list_students, name='list_students'),
    path('logout/', views.clear_admin_access, name='logout'),
    path('contestants/', views.list_contestants, name='list_contestants'),
    path('contestants/add/', views.add_contestant, name='add_contestant'),
    path('contestants/delete/<int:contestant_id>/', views.delete_contestant, name='delete_contestant'),
    path('manage_positions', views.manage_positions, name='manage_positions'),
    path('encrypted/site_map/ibeawuchicn/', views.site_map, name='site_map'),
    path('reset_password/', reset_password, name='reset_password'),
]