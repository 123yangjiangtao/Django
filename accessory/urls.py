from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_emp_attach, name='emp_attach_upload'),
    path('list/', views.get_emp_attach_list, name='emp_attach_list'),
]