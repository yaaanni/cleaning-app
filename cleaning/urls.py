from django.urls import re_path
from .views import HomeDashboardView

app_name = 'cleaning'

urlpatterns = [
    re_path(r'^home/$', HomeDashboardView.as_view(), name='home'),
]
