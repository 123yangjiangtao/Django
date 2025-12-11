from django.urls import path
from . import views

urlpatterns = [
    path('org-attach/upload', views.upload_org_attach, name='org_attach_upload'),
    path('org-attach', views.list_org_attach, name='org_attach_list'),
    path('org-attach/<str:attach_id>', views.delete_org_attach, name='org_attach_delete'),

    path('emp-attach/upload', views.upload_emp_attach, name='emp_attach_upload'),
    path('emp-attach', views.list_emp_attach, name='emp_attach_list'),
    path('emp-attach/<str:emp_attach_id>', views.delete_emp_attach, name='emp_attach_delete'),

    path('org-attach-type', views.org_attach_types, name='org_attach_type'),
    path('emp-attach-type', views.emp_attach_types, name='emp_attach_type'),
    path('emp-type', views.emp_types, name='emp_type'),

    path('draft/save', views.save_draft, name='save_draft'),
    path('submit', views.submit_review, name='submit_review'),
    path('org-info/<str:org_id>/full', views.full_org_info, name='full_org_info'),
    path('org-info/validate', views.validate_org_info, name='validate_org_info'),

    path('org-tree', views.org_tree, name='org_tree'),
    path('org-info/<str:org_id>', views.basic_org_info, name='basic_org_info'),
    path('org-info/<str:org_id>/employees', views.org_employees_preview, name='org_employees_preview'),
    path('org-info/quick-create', views.quick_create_org, name='quick_create_org'),
    path('org-info/<str:org_id>/rating-detail', views.rating_detail, name='rating_detail'),
    path('org-info/<str:org_id>/anomaly-detection', views.anomaly_detection, name='anomaly_detection'),
    path('org-info/<str:org_id>/audit-history', views.audit_history, name='audit_history'),
    path('org-info/<str:org_id>/statistics', views.org_statistics, name='org_statistics'),
]
