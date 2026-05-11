from django.urls import re_path
from django.contrib.auth.views import LoginView, LogoutView
from .views import ContactsListView, RegisterView, ClientProfileView, EmployeeProfileView, SuperuserDashboardView

app_name = 'users'

urlpatterns = [
    re_path(r'^contacts/$', ContactsListView.as_view(), name='contacts'),
    re_path(r'^register/$', RegisterView.as_view(), name='register'),
    re_path(r'^profile/$', ClientProfileView.as_view(), name='profile'),
    re_path(r'^login/$', LoginView.as_view(template_name='users/login.html'), name='login'),
    re_path(r'^logout/$', LogoutView.as_view(next_page='/'), name='logout'),
    re_path(r'^staff-dashboard/$', EmployeeProfileView.as_view(), name='employee_profile'),
    re_path(r'^super-dashboard/$', SuperuserDashboardView.as_view(), name='superuser_dashboard'),
]
